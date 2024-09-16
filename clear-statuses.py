import os
import json
import argparse

def recursively_status(obj):
    remove_keys = ['status']
    for key in obj.keys():
        value = obj[key]
        if isinstance(value, dict):
            if value.get('status', None) == 'removed':
                remove_keys.append(key)
            else:
                recursively_status(value)
    for key in remove_keys:
        obj.pop(key, None)

def clear_statuses(data_path):
    for f in os.listdir(data_path):
        if (f.endswith('.json')):
            filename = os.path.join(data_path, f)
            with open(filename, 'r') as file:
                j = file.read()
                try:
                    file_json = json.loads(j)
                except:
                    print(f'error loading')
                    continue

            if isinstance(file_json, list):
                file_json = [v for v in file_json if v.get('status') != 'removed']
                for v in file_json:
                    recursively_status(v)
            else:
                recursively_status(file_json)
            with open(filename, 'w') as file:
                file.write(json.dumps(file_json, indent = 4))

def main():
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'wikidata-site/public/data')
    parser = argparse.ArgumentParser(description='Clear status information from data')
    parser.add_argument('--path', required=False, help='Path to json files')
    args = parser.parse_args()
    if args.path:
        data_path = args.path
    clear_statuses(data_path)

if __name__ == '__main__':
    main()