import logging
import argparse
from wikidata.client import Client
from wikidata.cache import MemoryCachePolicy
from termcolor import colored
import json
import requests
import os
import re
from PIL import Image
import shutil

_logger = logging.getLogger(__name__)

sparql_endpoint = 'https://query.wikidata.org/sparql'

data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'wikidata-site/public/data')

client = Client(cache_policy=MemoryCachePolicy(max_size=100000))

wiki_bot_headers = {'User-Agent': 'YaleLibraryBot/0.0 (https://library.yale.edu; library@yale.edu)'}

label_map = {}

value_properties = ['P625']

allowed_properties = None
allowed_images = None

def configure_logging(name):
    root_logger = logging.getLogger()
    log_level = os.getenv("LOG_LEVEL", "INFO")
    root_logger.setLevel(log_level)
    console_handler = logging.StreamHandler()
    root_logger.addHandler(console_handler)
    fh_info = logging.FileHandler(name)
    fh_info.setLevel(log_level)
    root_logger.addHandler(fh_info)

def lookup_entity_data(entity_id):
    entity = client.get(entity_id, load=True)
    data = {'label': label(entity)}
    if entity.data:
        claims = entity.data.get('claims', {})
        filtered_claims = {}
        for key in [claim_key for claim_key in claims.keys() if claim_key in value_properties]:
            filtered_claims[key] = claims[key]
        if filtered_claims:
            additional_data = load_properties(filtered_claims, False)
            data['properties'] = additional_data
    else:
        _logger.error(f'No data for {entity_id} {entity.__dict__}')
    return data


class properties_dict(dict):
    def __missing__(self, key):
        if 'http://www.wikidata.org/entity/' in key:
            _logger.error(colored(f'Key with wikidata URI: {key}', 'red'))
            key = key.replace('http://www.wikidata.org/entity/', '')
            return self[key]
        self[key] = lookup_entity_data(key)
        return self[key]

entity_data = properties_dict({})


def snack_data(snack):
    value_data = None
    if snack:
        datatype = snack['datatype']
        value_data = {'value-type': datatype}
        match datatype:
            case 'wikibase-form':
                id = find(snack, 'datavalue.value.id')
                value_data['id'] = id
                value_data['data'] = entity_data[id]
                value_data['text'] = value_data['data'].get('label', None)
            case 'monolingualtext':
                value_data['text'] = find(snack, 'datavalue.value.text')
            case 'string':
                value_data['text'] = find(snack, 'datavalue.value')
            case 'url':
                value_data['text'] = find(snack, 'datavalue.value')
            case 'time':
                value_data['text'] = find(snack, 'datavalue.value.time')
                if not value_data['text']:
                    _logger.error(f'No time info {snack}')
                calendar_model = find(snack, 'datavalue.value.calendarmodel')
                if calendar_model:
                    calendar_model = calendar_model.replace('http://www.wikidata.org/entity/', '')
                    value_data['calendar-model'] = entity_data[calendar_model]
                timezone = find(snack, 'datavalue.value.timezone')
                if timezone:
                    value_data['timezone'] = timezone
            case 'wikibase-item' | 'wikibase-property':
                id = find(snack, 'datavalue.value.id')
                if not id:
                    _logger.error(f'Id not found {snack}')
                    return None
                value_data['id'] = id
                value_data['data'] = entity_data[id]
                value_data['text'] = value_data['data'].get('label', None)
            case 'external-id':
                value_data['text'] = find(snack, 'datavalue.value')
            case 'globe-coordinate':
                value_data['latitude'] = find(snack, 'datavalue.value.latitude')
                value_data['longitude'] = find(snack, 'datavalue.value.longitude')
            case 'geo-shape':
                #https://commons.wikimedia.org/w/api.php\?action\=query\&prop\=revisions\&rvslots\=\*\&rvprop\=content\&format\=json\&titles\=Data:South%20Korea/Seoul.map\&origin\=\*
                data_value = find(snack, 'datavalue.value')
                value_data['name'] = data_value
                url = f'https://commons.wikimedia.org/w/api.php?action=query&prop=revisions&rvslots=*&rvprop=content&format=json&titles={data_value}'
                resp = requests.get(url=url, headers=wiki_bot_headers)
                value_data['geo-shape'] = resp.json()
            case 'quantity':
                unit = None
                unit_ref = find(snack, 'datavalue.value.unit')
                if unit_ref:
                    unit = entity_data[unit_ref.replace('http://www.wikidata.org/entity/', '')]
                value_data['amount'] = find(snack, 'datavalue.value.amount')
                if not value_data['amount']:
                    _logger.error(f'amount not found {snack}')
                    return None
                if unit:
                    value_data['unit'] = unit
            case 'commonsMedia':
                data_value = find(snack, 'datavalue.value')
                if not data_value:
                    return None
                if allowed_images and not data_value in allowed_images:
                    return None
                value_data['name'] = data_value
                info_url = f'https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo|info&inprop=url&iiprop=url|size|mime&format=json&titles=File:{requests.utils.quote(data_value)}'
                resp = requests.get(url=info_url, headers=wiki_bot_headers)
                info = resp.json()
                image_info = find(info, 'query.pages.*.imageinfo')
                if image_info:
                    if image_info[0]['mime'] == 'image/tiff':
                        image_info[0]['name'] = data_value
                        url = image_info[0]['url']
                        try:
                            img = Image.open(requests.get(url, stream=True, headers=wiki_bot_headers).raw)
                            rgb_im = img.convert("RGB")
                            if rgb_im.size[0] > 500:
                                rgb_im.thumbnail((500,500), Image.LANCZOS)
                            rgb_im.save(f'{os.path.join(data_path, data_value)}.jpg')
                            _logger.info(f'Converted image: {image_info[0]['url']} to /data/{data_value}.jpg')
                            image_info[0]['url'] = f'/data/{data_value}.jpg'
                            image_info[0]['mime'] = 'image/jpeg'
                        except Exception as e:
                            _logger.error(f'Unable to convert image {image_info[0]['url']}', e)
                            pass

                value_data['image-info'] = image_info
    return value_data


def _load_props(props):
    if not props:
        return []
    props_data = []
    for key in props.keys():
        prop_data = {'key': key, 'property': entity_data[key], 'values': []}
        for prop in props[key]:
            data = snack_data(prop)
            if data:
                prop_data['values'].append(data)
        if prop_data['values']:
            props_data.append(prop_data)
    return props_data


def load_properties(entity, include_refs_and_quals = True):
    all_props = {}
    property_keys = entity.keys()
    if allowed_properties:
        property_keys = [p for p in property_keys if p in allowed_properties]
    for key in property_keys:
        property_data = {'key': key, 'property': entity_data[key], 'values': []}
        for value in entity[key]:
            mainsnack = value.get('mainsnak', None)
            value_data = snack_data(mainsnack)
            if not value_data:
                _logger.error(colored(f'No data for {key}', 'red'))
                print(mainsnack)
                continue
            if value_data and value_data != 'skip':
                if include_refs_and_quals:
                    qualifiers = value.get('qualifiers', None)
                    qs = _load_props(qualifiers)
                    if qs:
                        value_data['qualifiers'] = qs
                    references_list = value.get('references', None)
                    if references_list:
                        rlist = []
                        for references in references_list:
                            references = references['snaks']
                            rs = _load_props(references)
                            if rs:
                                rlist.append(rs)
                        if rlist:
                            value_data['references'] = rlist
            elif value_data != 'skip':
                if not find(mainsnack, 'snaktype') == 'novalue':
                    _logger.error(f'Error with {entity_data[key]} ({key})')
            property_data['values'].append(value_data)
        _logger.debug(property_data)
        if property_data.get('values'):
            all_props[key] = property_data
    return all_props


def load_claims(entity):
    entity_claims = find(entity.data, 'claims')
    property_data = load_properties(entity_claims)
    return property_data


def find(data, path):
    keys = path.split('.')
    empty = {}
    rv = data
    for key in keys:
        if key == '*':
            key = list(rv.keys())[0]
        rv = rv.get(key, empty)
        if rv == empty:
            break
    return None if rv == empty else rv

def label(entity):
    if entity.id in label_map:
        return label_map[entity.id]
    if not entity.data:
        return None
    return find(entity.data, 'labels.en.value') or find(entity.data, 'representations.en.value')

def add_to_entity_file(entity):
    entity_ref = create_entity_ref(entity)
    entity_list_file = os.path.join(data_path, f'entity_list.json')
    entity_list = []
    if os.path.exists(entity_list_file):
        with open(entity_list_file, 'r') as file:
            entity_list = json.load(file)
    entity_list = [entity for entity in entity_list if entity['id'] != entity_ref['id']]
    entity_list.append(entity_ref)
    with open(entity_list_file, 'w') as file:
        file.write(json.dumps(entity_list, indent=4))

def create_entity_ref(entity):
    entity_ref = {
        'id': entity['id'],
        'description': entity['description'],
        'label': entity['label']
    }
    ref_properties = ['P569', 'P19', 'P570', 'P20', 'P18', 'P69']
    entity_ref['properties'] = {}
    for ref_property in ref_properties:
        prop = entity['properties'].get(ref_property)
        if prop:
            prop = prop.copy()
            for value in prop['values']:
                value.pop('references', None)
                value.pop('qualifiers', None)
            entity_ref['properties'][ref_property] = prop
    return entity_ref

def load_file_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    return None

def extract_columns(column_names, line):
    if not line:
        return None
    cols = line.split('\t')
    ix = 0
    row = {}
    for column_name in column_names:
        if len(cols) <= ix:
            break
        row[column_name] = cols[ix].strip()
        ix += 1
    return row



def load(id, bio_url_prefix = None, property_override_url_prefix = None, publications_url_prefix = None):
    entity = {}
    wiki_entity = client.get(id, load=True)
    entity['id'] = id
    entity['description'] = f'{wiki_entity.description}'
    entity['label'] = label(wiki_entity)
    if bio_url_prefix:
        text = load_file_from_url(f'{bio_url_prefix}{id}.md')
        if text:
            entity['biographyMarkdown'] = text
            lines = entity['biographyMarkdown'].split('\n')
            entity['label'] = lines[0].strip().replace('# ', '')
            if lines[1].startswith('## '):
                entity['description'] = lines[1].strip().replace('## ', '')


    if publications_url_prefix:
        text = load_file_from_url(f'{publications_url_prefix}{id}.tsv')
        if text:
            publications = [extract_columns(['title', 'date', 'link', 'journal', 'role', 'authors'], line) for line in text.split('\n')]
            if publications:
                entity['publications'] = [p for p in publications if p]

    entity['properties'] = load_claims(wiki_entity)
    if property_override_url_prefix:
        response = requests.get(f'{property_override_url_prefix}{id}.json')
        if response.status_code == 200:
            try:
                props = response.json()
                entity['properties'].update(props)
                rm_props = []
                for k in entity['properties']:
                    if not entity['properties'][k]:
                        rm_props.append(k)
                for k in rm_props:
                    entity['properties'].pop(k, None)
            except Exception as e:
                _logger.error(f'Error loading property overrides for {id} {e}')
                print(response.text)
                print(e)

    with open(os.path.join(data_path, f'{id}.json'), 'w') as file:
        file.write(json.dumps(entity, indent=4))
    add_to_entity_file(entity)

def load_ids(ids, bio_url_prefix = None, property_override_url_prefix= None, publications_url_prefix = None):
    for wikidata_id in ids:
        _logger.info(colored(f'Loading {wikidata_id}', 'blue'))
        load(wikidata_id, bio_url_prefix, property_override_url_prefix, publications_url_prefix)

def load_sparql_results(sparql, bio_url_prefix = None, property_override_url_prefix= None, publications_url_prefix = None):
    params = {'query': sparql}
    headers = wiki_bot_headers.copy()
    headers['Accept'] = 'application/json'
    response = requests.get(sparql_endpoint, params=params, headers=headers)
    results = find(response.json(), 'results.bindings')
    for result in results:
        wikidata_uri = find(result, 'item.value')
        if wikidata_uri:
            label = find(result, 'itemLabel.value')
            wikidata_id = wikidata_uri.split('/')[-1:][0]
            _logger.info(colored(f'Loading {wikidata_id}: {label}', 'blue'))
            load(wikidata_id, bio_url_prefix, property_override_url_prefix, publications_url_prefix)

def load_id_list(id_list_url):
    id_list = []
    response = requests.get(id_list_url, headers=wiki_bot_headers)
    if response.status_code == 200:
        data = response.text
        for line in data.split('\n'):
            row = line.split('\t')
            if row[0].startswith('Q'):
                id_list.append(row[0])
                if row[1]:
                    label_map[row[0]] = row[1]
    return id_list


def compare_with_site(site):
    changed_ids = []
    for f in os.listdir(data_path):
        if (f.startswith('Q') and f.endswith('.json')):
            with open(os.path.join(data_path, f)) as local_file:
                local_json = json.load(local_file)
            remote_json = None
            item_changed = False
            response = requests.get(f'{site}/data/{f}')
            if response.status_code == 200:
                remote_json = response.json()
                for item in local_json['properties'].values():
                    remote_item = remote_json['properties'].get(item['key'])
                    if remote_item and remote_item.get('status') == 'removed':
                        remote_item = None
                    if remote_item:
                        remote_item.pop('status', None)
                    if not remote_item:
                        item['status'] = 'new'
                        item_changed = True
                    elif remote_item != item:
                        print(remote_item)
                        print(item)
                        item['status'] = 'updated'
                        item_changed = True

                for item in remote_json['properties'].values():
                    if item.get('status') == 'removed':
                        continue
                    local_item = local_json['properties'].get(item['key'])
                    if not local_item:
                        item['status'] = 'removed'
                        local_json['properties'][item['key']] = item
                        item_changed = True
                if remote_json.get('label') != local_json.get('label'):
                    local_json['labelStatus'] = 'updated'
                    item_changed = True
                if remote_json.get('biographyMarkdown') != local_json.get('biographyMarkdown'):
                    local_json['biographyMarkdownStatus'] = 'updated'
                    item_changed = True
                if remote_json.get('description') != local_json.get('description'):
                    local_json['descriptionStatus'] = 'updated'
                    item_changed = True
                if remote_json.get('publications') != local_json.get('publications'):
                    if not remote_json.get('publications'):
                        local_json['publicationsStatus'] = 'new'
                    elif not local_json.get('publications'):
                        local_json['publicationsStatus'] = 'removed'
                        local_json['publications'] = remote_json.get('publications')
                    else:
                        local_json['publicationsStatus'] = 'updated'
                    item_changed = True
            else:
                local_json['status'] = 'new'
                item_changed = True

            if item_changed:
                _logger.info(f'Updating {f}')
                changed_ids.append(local_json['id'])
                with open(os.path.join(data_path, f), 'w') as local_file:
                    local_file.write(json.dumps(local_json, indent=4))
            else:
                _logger.info(f'No update for {f}')


    # special treatment for entity json
    f = 'entity_list.json'
    with open(os.path.join(data_path, f)) as local_file:
        local_json = json.load(local_file)
    remote_json = None
    item_changed = False
    response = requests.get(f'{site}/data/{f}')
    if response.status_code == 200:
        remote_json = response.json()
    remote_item_map = {x['id']: x for x in remote_json}
    local_item_map = {x['id']: x for x in local_json}
    for item in local_json:
        remote_item = remote_item_map.get(item['id'])
        if not remote_item:
            item['status'] = 'new'
        elif item['id'] in changed_ids:
            item['status'] = 'updated'
    for item in remote_json:
        if not local_item_map[item['id']]:
            item['status'] = 'removed'
            local_json.append(item)


    with open(os.path.join(data_path, f), 'w') as local_file:
        local_file.write(json.dumps(local_json, indent=4))





def main():
    global allowed_properties, allowed_images
    configure_logging('wikiloader.log')
    parser = argparse.ArgumentParser(description='Load wikidata')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--entity-id', required=False, help='Entity id to load (eg Q20145)')
    group.add_argument('--sparql-file', required=False, help='SPARQL query file to get list of ids')
    group.add_argument('--site-file', required=False, help='JSON file containing query and or SPARQL with site information')
    group.add_argument('--id-file', required=False, help='File with a list of entity ids')
    parser.add_argument('--append', action='store_true', help='Append to existing entities')
    parser.add_argument('--compare-site', required=False, help='Site for comparing values')
    args = parser.parse_args()

    if not args.append:
        for f in os.listdir(data_path):
            if f.startswith('Q') or f.endswith('.jpg') or f == f'entity_list.json':
                os.remove(os.path.join(data_path, f))

    if args.site_file:
        with open(args.site_file) as f:
            site_json = json.load(f)
        _logger.info(f'Processing {site_json['title']} from {args.site_file}.')
        bio_url_prefix = site_json.get('bioUrlPrefix')
        property_override_url_prefix = site_json.get('propertyOverrideUrlPrefix')
        publications_url_prefix = site_json.get('publicationsUrlPrefix')

        if site_json.get('properties'):
            response = requests.get(site_json.get('properties'))
            if response.status_code == 200:
                data = response.text
                allowed_properties = []
                for line in data.split('\n'):
                    row = line.split('\t')
                    if row[0].startswith('P'):
                        entity_data[row[0]] = {'label': row[1]}
                        allowed_properties.append(row[0])
                _logger.info(f'allowed properties update with {allowed_properties}')

        if site_json.get('images'):
            response = requests.get(site_json.get('images'))
            if response.status_code == 200:
                data = response.text
                allowed_images = []
                for line in data.split('\n'):
                    row = line.split('\t')
                    if row[0].startswith('Q'):
                        allowed_images.append(row[2])
                _logger.info(f'allowed images update with {allowed_images}')
        if site_json.get('idList'):
            id_list = site_json['idList']

            if isinstance(id_list, str):
                id_list = load_id_list(id_list)
            load_ids(id_list, bio_url_prefix, property_override_url_prefix, publications_url_prefix)
        if site_json.get('sparql'):
            load_sparql_results(site_json['sparql'], bio_url_prefix, property_override_url_prefix, publications_url_prefix)

        shutil.copyfile(args.site_file, os.path.join(data_path, 'site.json'))
    elif args.entity_id:
        load(args.entity_id)
    elif args.id_file:
        pattern = re.compile("^Q([0-9]+)$")
        with open(args.id_file, 'r') as file:
            ids = [line.strip() for line in file.readlines() if pattern.match(line.strip())]
        load_ids(ids)
    else:
        with open(args.sparql_file, 'r') as file:
            sparql = file.read()
        load_sparql_results(sparql)

    if args.compare_site:
        compare_with_site(args.compare_site)

if __name__ == '__main__':
    main()