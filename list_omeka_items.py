import json

with open('all_omeka_items.json') as f:
    all_data = json.load(f)

for item in all_data:
    print(f'{item['@type'][1]}\t{item['o:title']}\t{item['schema:sameAs'][0]['@id']}')