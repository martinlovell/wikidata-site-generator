import json
import os
import re

def main():
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'wikidata-site/public/data')
    entity_list_file = os.path.join(data_path, f'entity_list.json')
    with open(entity_list_file, 'r') as f:
        entity_list_json = json.load(f)
    with open('entity_list.csv', 'w') as entity_list_file:
        entity_list_file.write('entity id\tlabel\n')
        for entity in entity_list_json:
            entity_list_file.write(f'{entity['id']}\t{entity['label']}\n')

    pattern = r'Q\d+?\.json'
    properties = {}
    with open('all_images_list.csv', 'w') as image_list_file:
        image_list_file.write('entity id\tlabel\timage name\n')
        for f in os.listdir(data_path):
            if re.match(pattern,f):
                entity_file_name = os.path.join(data_path, f)
                with open(entity_file_name, 'r') as entity_file:
                    entity_json = json.load(entity_file)
                    with open(f'../constellations-data/biographies/{entity_json['id']}.md', 'w') as biofile:
                        biofile.write(f'# {entity_json['label']}\n')
                        if entity_json['description']:
                            biofile.write(f'## {entity_json['description']}\n')
                    for property in entity_json.get('properties', {}).values():
                        properties[property['key']] = property.get('property', {}).get('label')
                        if 'values' in property:
                            for property_value in property['values']:
                                for value_property in property_value.get('data',{}).get('properties', {}).values():
                                    properties[value_property['key']] = value_property.get('property', {}).get('label')

                                if property_value.get('value-type') == 'commonsMedia':
                                    name = property_value.get('name')
                                    if name:
                                        image_list_file.write(f'{entity_json['id']}\t{entity_json['label']}\t{name}\n')

    with open('all_properties_list.csv', 'w') as properties_list_file:
        properties_list_file.write('property id\tlabel\n')
        for key in properties.keys():
            properties_list_file.write(f'{key}\t{properties[key]}\n')

if __name__ == '__main__':
    main()