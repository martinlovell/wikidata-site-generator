import logging
import argparse
from termcolor import colored
import json
import requests
import os
import re
from PIL import Image
import shutil
import dateparser
import gzip
import string
from bs4 import BeautifulSoup
import markdown

_logger = logging.getLogger(__name__)

sparql_endpoint = 'https://query.wikidata.org/sparql'

data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'wikidata-site/public/data')

wiki_cache_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'wiki-cache')

disable_cache_check = False
use_image_cache = True

search_index = []

site_json = {}

if not os.path.exists(data_path):
    os.makedirs(data_path)
if not os.path.exists(wiki_cache_path):
    os.makedirs(wiki_cache_path)


wiki_bot_headers = {'User-Agent': 'YaleLibraryDownloader/0.0 (https://library.yale.edu; library@yale.edu)'}
requests_session = requests.Session()
requests_session.headers.update(wiki_bot_headers)

label_map = {}

value_properties = ['P625']

allowed_properties = None

def configure_logging(name):
    root_logger = logging.getLogger()
    log_level = os.getenv("LOG_LEVEL", "INFO")
    root_logger.setLevel(log_level)
    console_handler = logging.StreamHandler()
    root_logger.addHandler(console_handler)
    fh_info = logging.FileHandler(name)
    fh_info.setLevel(log_level)
    root_logger.addHandler(fh_info)

def load_wikidata_entity(id):
    cache_file = os.path.join(wiki_cache_path, f'{id}.json.gz')
    existing_data = None
    if os.path.exists(cache_file):
        with gzip.open(cache_file, 'rt') as cf:
            try:
                existing_data = json.loads(cf.read())
            except:
                _logger.error(f'Unable to read cache for {id}')
    if existing_data and disable_cache_check:
        return existing_data
    url = f'https://www.wikidata.org/wiki/Special:EntityData/{id}.json'
    headers = {}
    if existing_data:
        modifications = existing_data.get('modified')
        dt = dateparser.parse(modifications)
        headers['If-Modified-Since'] = dt.strftime('%a, %d %b %Y %H:%M:%S GMT')
    response = requests_session.get(url, headers=headers)
    if response.status_code == 200:
        response_json = response.json()
        downloaded_data = response_json.get('entities', {}).get(id, None)
        if not downloaded_data:
            v = list(response_json.get('entities', {}).values())
            if len(v) > 0:
                downloaded_data = v[0]
        _logger.debug(f'adding to cache {id}')
        if downloaded_data:
            with gzip.open(cache_file, 'wt') as cf:
                cf.write(json.dumps(downloaded_data))
        return downloaded_data
    elif response.status_code == 304:
        _logger.debug(f'using cache {id}')
        return existing_data
    return None


def lookup_entity_data(entity_id):
    entity = load_wikidata_entity(entity_id)
    data = {'label': label(entity)}
    if entity:
        claims = entity.get('claims', {})
        instance_of_labels = []
        for instance_of in claims.get('P31', []):
            if find(instance_of, 'mainsnak.datatype') == 'wikibase-item':
                inst = find(instance_of, 'mainsnak.datavalue.value.id')
                if inst:
                    inst = load_wikidata_entity(inst)
                    instance_of_labels.append(label(inst))
        data['instance_of'] = instance_of_labels
        s = ' '.join(instance_of_labels)
        if 'city' in s or 'town' in s or 'borough' in s or 'island' in s or 'county' in s or 'neighborhood' in s or 'state' in s or 'place' in s:
            data['label'] = ', '.join(list(dict.fromkeys([data['label']] + enhanced_label_suffix(entity))))
        filtered_claims = {}
        for key in [claim_key for claim_key in claims.keys() if claim_key in value_properties]:
            filtered_claims[key] = claims[key]
        if filtered_claims:
            additional_data = load_properties(None, filtered_claims, False)
            data['properties'] = additional_data

    else:
        _logger.error(f'No data for {entity_id}')
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
                else:
                    value_data['text'] = value_data['text'][1:5]
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
                resp = requests_session.get(url)
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
    return value_data


def _load_props(props):
    if not props:
        return []
    props_data = []
    for key in props.keys():
        property_label = entity_data[key]['label']
        prop_data = {'label': property_label, 'values': []}
        for prop in props[key]:
            data = snack_data(prop)
            if data:
                prop_data['values'].append(data)
        if prop_data['values']:
            props_data.append(prop_data)
    return props_data


def load_properties(entity_id, entity, include_refs_and_quals = True):
    all_props = {}
    property_keys = entity.keys()
    if allowed_properties:
        property_keys = [p for p in property_keys if p in allowed_properties]

    for key in property_keys:
        property_data = entity_data[key]
        property_label = property_data['label']
        property_data = {'label': property_label, 'values': []}
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
            elif value_data != 'skip':
                if not find(mainsnack, 'snaktype') == 'novalue':
                    _logger.error(f'Error with {entity_data[key]} ({key})')
            property_data['values'].append(value_data)
        _logger.debug(property_data)
        if property_data.get('values'):
            all_props[property_label] = property_data
    consolidate_relatives(all_props)
    return all_props

def consolidate_relatives(properties):
    relatives = None
    for relative in ['sibling', 'mother', 'father', 'spouse', 'parent']:
        if relative in properties:
            if not relatives:
                relatives = properties.get('relative')
                if not relatives:
                    properties['relative'] = relatives = {
                        "label": "relative",
                        "values": []
                    }
            print("Replacing " + relative)
            r = properties.pop(relative)
            values = r['values']
            qualifier = [{
                            "label": "kinship to subject",
                            "values": [
                                {
                                    "text": relative
                                }
                            ]
                        }]
            for v in values:
                v['qualifiers'] = qualifier
                relatives['values'].append(v)


def load_claims(entity):
    entity_claims = find(entity, 'claims')
    property_data = load_properties(entity['id'], entity_claims)
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
    if not entity:
        return None
    if entity['id'] in label_map:
        return label_map[entity['id']]

    lbl = find(entity, 'labels.en.value') or find(entity, 'representations.en.value')
    return lbl

def load_state(entity):
    state = entity['claims'].get('P131')
    if state:
        state_id = find(state[0], 'mainsnak.datavalue.value.id')
        state_entity = load_wikidata_entity(state_id)
        state_label = label(state_entity)
        if 'County' in state_label or 'Region' in state_label or 'Parish' in state_label or 'District' in state_label:
            return load_state(state_entity)
        else:
            if state_label == 'United States of America':
                state_label = 'US'
            return state_label


def enhanced_label_suffix(entity):
    suffixes = []
    state_label = load_state(entity)
    if state_label:
        suffixes.append(state_label)
    country = entity['claims'].get('P17')
    if country:
        country_id = find(country[0], 'mainsnak.datavalue.value.id')
        country_entity = load_wikidata_entity(country_id)
        country_label = label(country_entity)
        if country_label == 'United States of America':
            country_label = 'US'
        suffixes.append(country_label)
    return list(dict.fromkeys(suffixes))

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
        'label': entity['label']
    }
    if 'description' in entity:
        entity_ref['description'] = entity['description']
    ref_properties = ['date of birth', 'place of birth', 'date of death', 'place of death', 'image', 'educated at']
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
    response = requests_session.get(url)
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

def load_image(id):
    url = f'{site_json["images"]}{id}.jpg'
    image = f'{data_path}/{id}.jpg'
    r = requests_session.get(url, stream=True)
    if r.status_code == 200:
        with open(image, 'wb') as f:
            for chunk in r:
                f.write(chunk)
        return True
    else:
        _logger.error(f'Unable to load remote image {r.status_code} {url} {id}')


def load(id, bio_url_prefix = None, property_override_url_prefix = None, publications_url_prefix = None):
    entity = {}
    wiki_entity = load_wikidata_entity(id)
    _logger.info(colored(f'{id} - {wiki_entity["modified"]}', 'green'))
    entity['id'] = id
    entity['label'] = label(wiki_entity)
    if bio_url_prefix:
        text = load_file_from_url(f'{bio_url_prefix}{id}.md')
        if text:
            entity['biographyMarkdown'] = text
            lines = entity['biographyMarkdown'].split('\n')
            entity['label'] = lines[0].strip().replace('# ', '')
            if lines[1].startswith('## '):
                entity['description'] = lines[1].strip().replace('## ', '')
            else:
                _logger.info(f'Description not found: {id}')
    if publications_url_prefix:
        text = load_file_from_url(f'{publications_url_prefix}{id}.md')
        if text:
            entity['publicationsMarkdown'] = text

    entity['properties'] = load_claims(wiki_entity)
    if property_override_url_prefix:
        response = requests_session.get(f'{property_override_url_prefix}{id}.json')
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
    if load_image(id):
        entity['properties']['image'] = {
            "label": "image",
            "values": [
                {
                    "value-type": "commonsMedia",
                    "name": entity['label'],
                    "image-info": [
                        {
                            "url": f"/data/{id}.jpg",
                            "mime": "image/jpeg"
                        }
                    ]
                }
            ]
        }
    with open(os.path.join(data_path, f'{id}.json'), 'w') as file:
        file.write(json.dumps(entity, indent=4))
        search_index.append(entity_index_entry(id, entity))
    add_to_entity_file(entity)


def name_to_slug(name):
    return name.translate(str.maketrans('', '', string.punctuation)).title().replace(' ', '')

def markdown_to_text(md):
    if not md:
        return ''
    html = markdown.markdown(md, extensions=['extra'])
    soup = BeautifulSoup(html, features='html.parser')
    return f'{soup.get_text()}'.replace(u"\u2018", "'").replace(u"\u2019", "'")

def index_text(s, type):
    return s

def entity_index_entry(id, entity):
    entry = {'id': id, 'Label': entity['label'], 'Biography': markdown_to_text(entity.get('biographyMarkdown')), 'Description': entity.get('description'), 'Publications': markdown_to_text(entity.get('publicationsMarkdown'))}
    all_text = []
    for prop in entity['properties'].values():
        label = prop['label']
        values = [index_text(v['text'], v.get('value-type')) for v in prop['values'] if 'text' in v]
        if not values:
            continue
        all_text.extend(values)
        entry[label] = values
    entry['AllText'] = ' '.join(all_text)
    return entry

def load_ids(ids, bio_url_prefix = None, property_override_url_prefix= None, publications_url_prefix = None):
    for wikidata_id in ids:
        _logger.info(colored(f'Loading {wikidata_id}', 'blue'))
        load(wikidata_id, bio_url_prefix, property_override_url_prefix, publications_url_prefix)

def load_sparql_results(sparql, bio_url_prefix = None, property_override_url_prefix= None, publications_url_prefix = None):
    params = {'query': sparql.replace('[AUTO_LANGUAGE]', 'en')}
    response = requests_session.get(sparql_endpoint, params=params, headers={'Accept':'application/json'})
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
    response = requests_session.get(id_list_url)
    if response.status_code == 200:
        data = response.text
        for line in data.split('\n'):
            row = line.split(None, 1)
            if len(row) < 2:
                _logger.info(f'skipping row in ID list [{line}]')
                continue
            if row[0].startswith('Q'):
                id_list.append(row[0])
                if len(row) < 2:
                    print(line)
                if row[1]:
                    label_map[row[0]] = row[1]
    return id_list

def get_response_json(response):
    if response.status_code == 200:
        try:
            return response.json()
        except:
            pass
    return None

def extract_location_information():
    location_information = {}
    for f in os.listdir(data_path):
        if (f.startswith('Q') and f.endswith('.json')):
            with open(os.path.join(data_path, f)) as local_file:
                local_json = json.load(local_file)
            entity_id = local_json['id']
            entity_name = local_json['label']
            for item in local_json['properties'].values():
                property_id = item['label']
                property_name = find(item, 'label')
                for value in [i for i in item['values'] if i.get('value-type') == 'wikibase-item']:
                    value_id = value['id']
                    value_name = value['text']
                    for value_coordinate_property in value.get('data', {}).get('properties', {}).get('coordinate location', {}).get('values', []):
                        latitude = value_coordinate_property.get('latitude')
                        longitude = value_coordinate_property.get('longitude')
                        if latitude and longitude:
                            location = location_information.get(value_id, {'label': value_name, 'entity_properties': [], 'lat': latitude, 'long': longitude})
                            location_information[value_id] = location
                            entity_properties = location['entity_properties']
                            info = {
                                'property_id': property_id,
                                'property_name': property_name.title(),
                                'entity_id': entity_id,
                                'entity_name': entity_name
                            }
                            entity_properties.append(info)
                            break
    with open(os.path.join(data_path, 'location_information.json'), 'w') as location_file:
        location_file.write(json.dumps(location_information, indent=4))

def compare_with_site(site):
    changed_ids = []
    for f in os.listdir(data_path):
        if (f.startswith('Q') and f.endswith('.json')):
            with open(os.path.join(data_path, f)) as local_file:
                local_json = json.load(local_file)
            remote_json = None
            item_changed = False
            response = requests_session.get(f'{site}/data/{f}')
            remote_json = get_response_json(response)
            if remote_json:
                for item in local_json['properties'].values():
                    remote_item = remote_json['properties'].get(item['label'])
                    if remote_item and remote_item.get('status') == 'removed':
                        remote_item = None
                    if remote_item:
                        remote_item.pop('status', None)
                    if not remote_item:
                        item['status'] = 'new'
                        item_changed = True
                    elif remote_item != item:
                        item['status'] = 'updated'
                        item_changed = True

                for item in remote_json['properties'].values():
                    if item.get('status') == 'removed':
                        continue
                    local_item = local_json['properties'].get(item.get('label'))
                    if not local_item:
                        item['status'] = 'removed'
                        local_json['properties'][item.get('label')] = item
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
    response = requests_session.get(f'{site}/data/{f}')
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
        if not item['id'] in local_item_map:
            item['status'] = 'removed'
            local_json.append(item)


    with open(os.path.join(data_path, f), 'w') as local_file:
        local_file.write(json.dumps(local_json, indent=4))

def load_properties_list(file):
    global allowed_properties
    response = requests_session.get(file)
    if response.status_code == 200:
        data = response.text
        allowed_properties = []
        for line in data.split('\n'):
            row = line.split(None, 1)
            if len(row) < 2:
                _logger.info(f'skipping row [{line}]')
                continue
            if row[0].startswith('P'):
                entity_data[row[0]] = {'label': row[1]}
                allowed_properties.append(row[0])
        entity_data['P625'] = {'label': 'coordinate location'}
        allowed_properties.append('P625')


def main():
    global allowed_properties, disable_cache_check, use_image_cache, data_path, wiki_cache_path, site_json
    configure_logging('wikiloader.log')
    parser = argparse.ArgumentParser(description='Load wikidata')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--entity-id', required=False, help='Entity id to load (eg Q20145)')
    group.add_argument('--sparql-file', required=False, help='SPARQL query file to get list of ids')
    group.add_argument('--site-file', required=False, help='JSON file containing query and or SPARQL with site information')
    group.add_argument('--id-file', required=False, help='File with a list of entity ids')
    parser.add_argument('--append', action='store_true', help='Append to existing entities')
    parser.add_argument('--no-cache-check', action='store_true', help='Disable cache check (always use the cached data)')
    parser.add_argument('--disable-image-cache', action='store_true', help='Disable image cache')
    parser.add_argument('--compare-site', required=False, help='Site for comparing values')
    parser.add_argument('--data-path', required=False, help=f'Path to react site data (default {data_path})')
    parser.add_argument('--cache-path', required=False, help=f'Path to wikidata cache (default {wiki_cache_path})')
    args = parser.parse_args()

    if args.data_path:
        data_path = args.data_path
    if args.cache_path:
        wiki_cache_path = args.cache_path

    disable_cache_check = args.no_cache_check

    if not args.append:
        for f in os.listdir(data_path):
            if f.startswith('Q') or f.endswith('.jpg') or f == f'entity_list.json':
                os.remove(os.path.join(data_path, f))

    if args.disable_image_cache:
        use_image_cache = False

    if args.site_file:
        with open(args.site_file) as f:
            site_json = json.load(f)
        _logger.info(f'Processing {site_json["title"]} from {args.site_file}.')
        bio_url_prefix = site_json.get('bioUrlPrefix')
        property_override_url_prefix = site_json.get('propertyOverrideUrlPrefix')
        publications_url_prefix = site_json.get('publicationsUrlPrefix')

        if site_json.get('properties'):
            load_properties_list(site_json.get('properties'))
            _logger.info(f'allowed properties update with {allowed_properties}')

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

    extract_location_information()
    with open(os.path.join(data_path, 'search_index.json'), 'w') as f:
        json.dump(search_index, f)

    if args.compare_site:
        compare_with_site(args.compare_site)

if __name__ == '__main__':
    main()