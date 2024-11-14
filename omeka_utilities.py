import os
import re
import json
import markdown
import requests
import math
import string
import logging
from PIL import Image
from io import StringIO

OMEKA_KEY=os.environ.get('OMEKA_KEY')
OMEKA_CRED=os.environ.get('OMEKA_CRED')
OMEKA_API=os.environ.get('OMEKA_API')
OMEKA_SITE=os.environ.get('OMEKA_SITE')
OMEKA_ITEM_SET=os.environ.get('OMEKA_ITEM_SET')
OMEKA_SITE_SLUG=os.environ.get('OMEKA_SITE_SLUG')
OMEKA_ITEMSET_TITLE=os.environ.get('OMEKA_ITEMSET_TITLE')

important_places_title = 'Important Places'


_logger = logging.getLogger(__name__)



ua_headers = {'User-Agent': 'YaleLibraryDownloader/0.0 (https://library.yale.edu; library@yale.edu)'}
requests_session = requests.Session()
requests_session.headers.update(ua_headers)

def omeka_api_get(uri, params = {}):
    params['key_identity'] = OMEKA_KEY
    params['key_credential'] = OMEKA_CRED
    response = requests_session.get(f'{OMEKA_API}{uri}', params = params, headers = {'Accept':'application/json', 'Content-Type': 'application/json'})
    if response.status_code == 200:
        return response.json()
    else:
        _logger.error(response.text)



def omeka_api_delete(uri, params):
    print(f'{OMEKA_API}{uri}',)
    params['key_identity'] = OMEKA_KEY
    params['key_credential'] = OMEKA_CRED
    response = requests_session.delete(f'{OMEKA_API}{uri}', params = params)
    if response.status_code == 200:
        return response.json()
    else:
        _logger.error(response.text)

def omeka_api_post(uri, params, object):
    params['key_identity'] = OMEKA_KEY
    params['key_credential'] = OMEKA_CRED
    response = requests_session.post(f'{OMEKA_API}{uri}', params = params, headers = {'Accept':'application/json', 'Content-Type': 'application/json'}, data = json.dumps(object))
    if response.status_code == 200:
        try:
            return response.json()
        except:
            return {'message': response.text}
    else:
        _logger.error(response.text)

def omeka_api_put(uri, params, object):
    params['key_identity'] = OMEKA_KEY
    params['key_credential'] = OMEKA_CRED
    response = requests_session.put(f'{OMEKA_API}{uri}', params = params, headers = {'Accept':'application/json', 'Content-Type': 'application/json'}, data = json.dumps(object))
    if response.status_code == 200:
        try:
            return response.json()
        except:
            print(response.text)
            exit(9)
    else:
        _logger.error(response.text)


def configure_logging(name):
    root_logger = logging.getLogger()
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    root_logger.setLevel(log_level)
    console_handler = logging.StreamHandler()
    root_logger.addHandler(console_handler)
    fh_info = logging.FileHandler(name)
    fh_info.setLevel(log_level)
    root_logger.addHandler(fh_info)



def load_config_file(file_name):
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), file_name)) as f:
        return json.load(f)

class property_ids_dict(dict):
    def __missing__(self, key):
        result = omeka_api_get('/properties', {'term': key})
        if result and len(result) == 1:
            self[key] = result[0]['o:id']
            return self[key]
        else:
            _logger.error(f'unable to find property [{key}]')

property_ids = property_ids_dict({})


def update_property_labels():
    property_labels = load_config_file('property_labels.json')
    for prop in property_labels.keys():
        id = property_ids[prop]
        if id:
            label = property_labels[prop]
            existing_property = omeka_api_get(f'/properties/{id}')
            if existing_property['o:label'] != label:
                _logger.info(f'Updating {prop} ({id}) from {existing_property['o:label']} to {label}')
                existing_property['o:label'] = label
                omeka_api_put(f'/properties/{id}', {}, existing_property)
            else:
                _logger.info(f'{label} is already set for /properties/{id}')
        else:
            _logger.info(f'Unable to find property {prop}')


def main():
    configure_logging('omeka_upload.log')
    global data_path, OMEKA_ITEM_SET, OMEKA_SITE
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'wikidata-site/public/data')
    update_property_labels()






def remove_pages():

    site = omeka_api_get(f'/sites?slug={OMEKA_SITE_SLUG}', {})
    site = site[0]
    OMEKA_SITE = site['o:id']
    item_set = omeka_api_get(f'/item_sets?property[0][property]=dcterms:title&property[0][text]={OMEKA_ITEMSET_TITLE}&property[0][type]=eq',{})
    item_set = item_set[0]
    OMEKA_ITEM_SET = item_set['o:id']
    print(f"Using Site ID: {OMEKA_SITE}, and Item Set ID: {OMEKA_ITEM_SET}")
    site = omeka_api_get(f'/sites/{OMEKA_SITE}')
    pages_to_keep = []
    for n in site['o:navigation']:
        if n['type'] == 'page':
            pages_to_keep.append(n['data']['id'])
    site['o:page'] = [p for p in site['o:page'] if p['o:id'] in pages_to_keep]

    omeka_api_put(f'/sites/{OMEKA_SITE}', {}, site)

    print(site['o:page'])





if __name__ == '__main__':
    main()