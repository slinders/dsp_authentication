import json

class dspUtilities:

    # function to pretty print json
    def print_json(json_object, indent=2, sort_keys=False, encoding='utf-8' ):
        try:
            # Convert the JSON object to a string with specified indentation and sorting
            json_string = json.dumps(json_object, indent=indent, sort_keys=sort_keys, ensure_ascii=False).encode(encoding).decode(encoding)
            print(json_string)

        except (TypeError, ValueError) as e:
            # Error handling if the input is not a valid JSON object
            print(f"Error: Unable to print the JSON object. {str(e)}")