#-----------------------------------------------------------    
# Package import
#-----------------------------------------------------------
from dsp_authentication import dspClient
from dsp_utilities import dspUtilities as dspu
import json

#-----------------------------------------------------------
# dsp functions
#-----------------------------------------------------------
# function to get assets, with spaceName as parameter which is used as odata v4 filter
def get_assets(dsp_cli, space_name, top=10):
    # Datasphere asset metadata url
    dsp_assets = '/api/v1/dwc/catalog/assets'
    # get assets
    response = dsp_cli.request('GET', f'{dsp_assets}?$filter=spaceName eq \'{space_name}\'&$top={top}')
    return response

def start_task_chain(dsp_cli, space_id, task_chain_id):
    # API according to browser network trace
    # response = dsp_cli.request('POST', f'/dwaas-core/tf/{space_id}/taskchains/{task_chain_id}/start')
    # API according to CLI discovery document
    response = dsp_cli.request('POST', f'/dwaas-core/api/v1/tasks/chains/{space_id}/run/{task_chain_id}')
    return response

#-----------------------------------------------------------
# Read connection information from file and create dsp client
#-----------------------------------------------------------
connection_dir = 'connections/'

# Read connection information from file
dsp1_connection_file = connection_dir + 'conn_global-coe-dwchc.eu10_I077531_blank.json'
with open(dsp1_connection_file, 'r') as f:
    connection_info = json.load(f)

# create dsp client
dsp1_cli = dspClient(connection_info["dsp_url"], connection_info["authorization_url"], connection_info["token_url"], connection_info["redirect_url"], connection_info["client_id"], connection_info["client_secret"], connection_info["refresh_token_file_name"])

# Read connection information from file
# dsp2_connection_file = connection_dir + 'conn_dwc-gcoe.eu10_I077531.json'
# with open(dsp2_connection_file, 'r') as f:
#     connection_info = json.load(f)

# create dsp client
dsp2_cli = dspClient(connection_info["dsp_url"], connection_info["authorization_url"], connection_info["token_url"], connection_info["redirect_url"], connection_info["client_id"], connection_info["client_secret"], connection_info["refresh_token_file_name"])


#-----------------------------------------------------------
# call dsp functions
#-----------------------------------------------------------
# Pull DSP assets for space
response = get_assets(dsp1_cli, 'GCOE_INFRA_COSTS', 2)
print(f'Response status code: {response.status_code}')
dspu.print_json(response.json())

# Pull DSP assets for space
# response = get_assets(dsp2_cli, 'GCOE_INFRA_COSTS', 2)
# print(f'Response status code: {response.status_code}')
# dspu.print_json(response.json())

# Start task chain
response = start_task_chain(dsp1_cli, 'SEFANGENERATESTUFF','T1_V_persist_view')
print(f'Start task chain response status code: {response.status_code}')
dspu.print_json(response.json())

# Get discovery document
# Datasphere asset metadata url
# dsp_discovery = '/dwaas-core/api/v1/discovery'
# # get discovery document
# response = dsp1_cli.request('GET', f'{dsp_discovery}')
# # store response json in file
# with open('dsp_discovery.json', 'w') as f:
#     json.dump(response.json(), f)

# response = dsp1_cli.request('GET', '/dwaas-core/api/v1/users')
# # strcuture response json with indentation
# print (json.dumps(response.json(), indent=2))

#response = dsp1_cli.request('GET', '/dwaas-core/api/v1/content?space=GCOE_INFRA_COSTS&definitions=true')
# structure response json with indentation
#print (json.dumps(response.json(), indent=2))
