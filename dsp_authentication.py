#-----------------------------------------------------------
# oAuth authentication to SAP Datasphere using three-legged oAuth
#-----------------------------------------------------------

#-----------------------------------------------------------    
# Package import
#-----------------------------------------------------------

from requests_oauthlib import OAuth2Session # to handle oauth
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import urllib.parse
import webbrowser
from urllib.parse import urlparse

#-----------------------------------------------------------
# Authorization variables
#-----------------------------------------------------------


#-----------------------------------------------------------
# Class dspClient
#-----------------------------------------------------------
class dspClient:
    
    def __init__(self, dsp_url, authorization_url, token_url, redirect_url, client_id, client_secret, refresh_token_file):
        self.client_id = client_id
        self.client_secret = client_secret
        self.dsp_url = dsp_url
        self.authorization_code = None
        self.authorization_url = authorization_url
        self.token_url = token_url
        self.refresh_token_file = refresh_token_file
        
        # parse redirect url to get port and path
        parsed_redirect_url = urlparse(redirect_url)
        self.redirect_port = parsed_redirect_url.port
        self.redirect_path = parsed_redirect_url.path

        # create oauth session
        self.oauth = self.setup_oauth_session()

    # Get authorization code by starting a local server and 
    # opening the authorization url in a browser window and then
    # catch the authorization code in the local server
    def get_authorization_code(self):
        # Redirect user to the authorization url
        code_url = f'{self.authorization_url}?response_type=code&client_id={self.client_id}'.replace("|","%7C")
        print('Opening browser to fetch auth code on URL: ' + code_url)

        def open_auth_url():
            webbrowser.open_new(code_url)

        # Start a local server to listen for the authorization code
        threading.Thread(target=open_auth_url).start()
        server_address = ('', self.redirect_port)
        httpd = CustomHTTPServer(server_address, RequestHandler, dsp_client=self)
        print(f"Starting HTTP Server on {server_address[1]}...")
        httpd.serve_forever()
            
        return self.authorization_code
    
    # function to store refresh token in file in current directory
    def store_refresh_token(self, refresh_token):
        # store refresh token in file
        print('Storing refresh token in file ' + self.refresh_token_file)
        with open(self.refresh_token_file, 'w') as f:
            f.write(refresh_token)
        print('Refresh token stored in file ' + self.refresh_token_file)

    # function to read refresh token from file in current directory and return it if it exists
    def read_refresh_token(self):
        # read refresh token from file
        print('Reading refresh token from file ' + self.refresh_token_file)
        try:
            with open(self.refresh_token_file, 'r') as f:
                refresh_token = f.read()
            print('Refresh token read from file ' + self.refresh_token_file)
            return refresh_token
        except:
            print('No refresh token found in file ' + self.refresh_token_file)
            return None
        
    def setup_oauth_session(self):
        # create oauth client
        oauth = OAuth2Session(client_id=self.client_id)
        
        # check if there is a refresh token
        refresh_token = self.read_refresh_token()

        if refresh_token:
            print('Refresh token found, trying to fetch new access token')
            try:
                oauth.refresh_token(token_url=self.token_url, refresh_token=refresh_token, client_id=self.client_id, client_secret=self.client_secret)
                print('New access token fetched with refresh token')
                return oauth
            except:
                print('Error while fetching new access token with refresh token, please log in manually')
                refresh_token_invalid = True

        # if there is no refresh token, get authorization code and exchange it for access token
        print('No valid refresh token found, authorization code needed')
        self.authorization_code = self.get_authorization_code()

        # exchange authorization code for access token
        oauth.fetch_token(token_url=self.token_url, code=self.authorization_code, client_secret=self.client_secret, include_client_id=True)
        print('Authorization code exchanged for access token')

        # store refresh token
        refresh_token = oauth.token['refresh_token']
        self.store_refresh_token(refresh_token)

        return oauth

    # function to make a request. Oauth handling is done within the function, only method and url are input parameters
    # requests are made with oauthlib
    # output is the json response
    # a try except block is used to catch oauth errors, e.g., when the refresh token needs to be refreshed or the user needs to log in again, 
    # then the function is called again
    def request(self, method, url, data=None, is_retry=False):

        # replace spaces and | in url
        url = self.dsp_url + url
        url = url.replace(" ","%20").replace("|","%7C")
        print(f'Making request with method {method} to url {url}')
        
        try:
            # make request, with data if provided
            if data is None:
                response = self.oauth.request(method, url)
            else:
                response = self.oauth.request(method, url, data=data)
            
            # check for 401 status code
            if response.status_code == 401:
                raise Exception("Unauthorized (401)")
        
        except:
            # if there is an oauth error or 401 status code and this is the first time,
            # try to get a new access token and call the function again
            if not is_retry:
                print('Oauth error or 401 status code during request call, trying to get new access token')
                self.oauth = self.setup_oauth_session()
                print('Re-executing request')
                response = self.request(method, url, data, is_retry=True)
            else:
                print('Failed to execute request even after retrying')
                response = None  # or you can raise an error here

        # return response
        return response

#-----------------------------------------------------------
# The CustomHTTPServer class is a subclass of the HTTPServer class from http.server
# We're extending HTTPServer to allow additional arguments (in this case, dsp_client) to be passed to
# the request handler class.
#-----------------------------------------------------------

class CustomHTTPServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, dsp_client):
        self.dsp_client = dsp_client
        super().__init__(server_address, RequestHandlerClass)

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self, dsp_client=self.dsp_client)

#-----------------------------------------------------------
# this class handles the request to the local server when
# the authorization server redirects to the local server
# to pass the authorization code, then shuts down the server
#-----------------------------------------------------------

class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, dsp_client, **kwargs):
        self.dsp_client = dsp_client
        super().__init__(*args, **kwargs)
        
    def do_GET(self):
        # remove slash from redirect path if it exists
        redirect_path = self.dsp_client.redirect_path
        if redirect_path.startswith('/'):
            redirect_path = redirect_path[1:]

        print ('Path = ' + self.path)
        print ('RedirectPath = ' + redirect_path)

        # Parse request parameters
        params = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)

        # Check if the authorization code is in the request parameters 
        # and if so, assign authorization code to global variable and shut down server
        if self.path.startswith('/' + redirect_path + '?code'):
            self.auth_code = params['code'][0]
            print(f"Authorization code received: {self.auth_code}")
            
            self.dsp_client.authorization_code = self.auth_code

            # Send response to browser
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            # Send response body with HTML content including a title
            html_content = b"""
                <!DOCTYPE html>
                <html>
                    <head>
                        <title>Got it!</title>
                    </head>
                    <body>
                        SAP Datasphere authorization code received, you can leave this window open if you're into collecting tabs.
                    </body>
                </html>
            """
            self.wfile.write(html_content)

            def stop_server():
                self.server.shutdown()
            threading.Thread(target=stop_server).start()