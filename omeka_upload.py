import os
import re
import json
import markdown
import requests
import math
import string
import logging
from PIL import Image

OMEKA_KEY=os.environ.get('OMEKA_KEY')
OMEKA_CRED=os.environ.get('OMEKA_CRED')
OMEKA_API=os.environ.get('OMEKA_API')
OMEKA_SITE=os.environ.get('OMEKA_SITE')
OMEKA_ITEM_SET=os.environ.get('OMEKA_ITEM_SET')


_logger = logging.getLogger(__name__)

data_path = None
resources = {}
resources_by_itemid = {}


def load_config_file(file_name):
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), file_name)) as f:
        return json.load(f)

property_map = load_config_file('property_map.json')
resource_class_map = load_config_file('resource_class_map.json')
resource_class_precedence = ['schema:EducationalOrganization', 'schema:Organization', 'schema:Place']



ua_headers = {'User-Agent': 'YaleLibraryDownloader/0.0 (https://library.yale.edu; library@yale.edu)'}
requests_session = requests.Session()
requests_session.headers.update(ua_headers)

def omeka_api_get(uri, params):
    params['key_identity'] = OMEKA_KEY
    params['key_credential'] = OMEKA_CRED
    response = requests_session.get(f'{OMEKA_API}{uri}', params = params, headers = {'Accept':'application/json', 'Content-Type': 'application/json'})
    if response.status_code == 200:
        return response.json()
    else:
        _logger.error(response.text)

def omeka_api_post(uri, params, object):
    params['key_identity'] = OMEKA_KEY
    params['key_credential'] = OMEKA_CRED
    response = requests_session.post(f'{OMEKA_API}{uri}', params = params, headers = {'Accept':'application/json', 'Content-Type': 'application/json'}, data = json.dumps(object))
    if response.status_code == 200:
        return response.json()
    else:
        _logger.error(response.text)

def omeka_api_put(uri, params, object):
    params['key_identity'] = OMEKA_KEY
    params['key_credential'] = OMEKA_CRED
    response = requests_session.put(f'{OMEKA_API}{uri}', params = params, headers = {'Accept':'application/json', 'Content-Type': 'application/json'}, data = json.dumps(object))
    if response.status_code == 200:
        return response.json()
    else:
        _logger.error(response.text)

class property_ids_dict(dict):
    def __missing__(self, key):
        result = omeka_api_get('/properties', {'term': key})
        if result:
            self[key] = result[0]['o:id']
            return self[key]
property_ids = property_ids_dict({})

class resource_class_ids_dict(dict):
    def __missing__(self, key):
        result = omeka_api_get('/resource_classes', {'term': key})
        if result:
            self[key] = result[0]['o:id']
            return self[key]
resource_class_ids = resource_class_ids_dict({})

class page_ids_dict(dict):
    def __missing__(self, key):
        result = omeka_api_get('/site_pages', {'slug': key})
        if result:
            self[key] = result[0]['o:id']
            return self[key]
page_ids = page_ids_dict({})

def name_to_slug(name):
    return name.translate(str.maketrans('', '', string.punctuation)).lower().replace(' ', '_')

def upload_media_for_item(item_id, image_path):
    object = { 'o:ingester': 'upload', 'file_index': 0, 'o:item': {'o:id': item_id}}
    multipart_form_data = {'file[0]': (os.path.basename(image_path), open(image_path, 'rb'))}
    uri = f'/media?key_identity={OMEKA_KEY}&key_credential={OMEKA_CRED}'
    params = {'data': json.dumps(object)}
    response = requests_session.post(f'{OMEKA_API}{uri}', files = multipart_form_data, headers = {'Accept':'application/json'}, data = params)
    if not response.status_code == 200:
        _logger.error(f'Error uploading {image_path}: {response.text}')
        exit(1)
    return response.json()

def load_item_by_wikidata_id(wikidata_id):
    params = {
        'property[0][property]': 'schema:sameAs',
        'property[0][text]': f'https://www.wikidata.org/wiki/{wikidata_id}',
        'property[0][type]': 'eq'    }
    results = omeka_api_get('/items', params)
    if results:
        return results[0]

def value_to_omeka_property(label, property_value):
    value =  property_value['text']
    if value.startswith('http'):
            return {'type': 'uri', '@id': value, 'property_label': label.title(), 'property_id': property_ids[property_map[label]]
            }
    if property_value['value-type'] == 'time':
        value =  value[1:5]
    resource_class = resource_class_map.get(label)
    if resource_class and property_value['value-type'] == 'wikibase-item':
        if not resource_class == 'schema:EducationalOrganization':
            # heristics to find universities by instance names
            school_instance = [t for t in property_value['data']['instance_of'] if ('universit' in t or 'school' in t or 'college' in t) and not 'town' in t]
            if school_instance:
                resource_class = 'schema:EducationalOrganization'
                _logger.info(f'Overriding resource type because of instanceof {school_instance} for {property_value["id"]}')
        existing_resource = resources.get(property_value['id'])
        if existing_resource:
            type = existing_resource['@type']
            if resource_class_precedence.index(resource_class) < resource_class_precedence.index(type):
                existing_resource['o:resource_class'] = {'oid': resource_class_ids[resource_class]}
                _logger.info(f'updating resource {property_value['id']} to {resource_class} from {type} as id {resource_class_ids[resource_class]}')
            oid = save_resource(property_value['id'], existing_resource)['o:id']
        else: # new resource
            resource = {
                    'o:title': property_value['text'],
                    '@type': resource_class,
                    'o:resource_class': {'o:id':resource_class_ids[resource_class]},
                    'o:item_set': [{'o:id': OMEKA_ITEM_SET}],
                    'dcterms:title': [{'@value': property_value['text'], 'type': 'literal', 'property_label': 'Title', 'property_id': property_ids['dcterms:title']}],
                    'schema:sameAs': [{'type': 'uri', '@id': f'https://www.wikidata.org/wiki/{property_value['id']}', 'o:label': 'Wikidata', 'property_id': property_ids['schema:sameAs']}],
                    'dbo:name': [{'type': 'literal', '@value': property_value['text'], 'property_id': property_ids['dbo:name']}]
            }
            resources[property_value['id']] = resource
            coordinates = property_value.get('data', {}).get('properties', {}).get('P625')
            if coordinates:
                resource['o-module-mapping:mapping'] = {'@type': 'o-module-mapping:Map', 'o-module-mapping:bounds': get_bounding_box(coordinates['values'][0]['latitude'], coordinates['values'][0]['longitude'], 100)}
                resource['o-module-mapping:feature'] = [{
                    '@type': 'o-module-mapping:Feature', 'o-module-mapping:geography-type': 'Point',
                    'o-module-mapping:geography-coordinates': [coordinates['values'][0]['longitude'], coordinates['values'][0]['latitude']]
                }]
            oid = save_resource(property_value['id'], resource)['o:id']
        prop =  {'type': 'resource', 'property_label': label.title(), 'value_resource_id': oid, 'value_resource_name': 'items', 'display_title': property_value['text'], 'property_id': property_ids[property_map[label]]}
        return prop
    else:
        prop =  {'type': 'literal', 'property_label': label.title(), '@value': value, 'property_id': property_ids[property_map[label]]}
        return prop

def save_resource(resource_id, resource):
    existing_item = load_item_by_wikidata_id(resource_id)
    if not existing_item:
        response = omeka_api_post('/items', {}, resource)
        if not response:
            _logger.error('Unable to update resource')
            exit(1)
    else:
        resource['o:id'] = existing_item['o:id']
        if 'o-module-mapping:mapping' in resource:
            resource['o-module-mapping:mapping']['o:id'] = existing_item['o:id']
        response = omeka_api_put(f'/items/{existing_item['o:id']}', {}, resource)
        if not response:
            _logger.error('Unable to save resource')
            exit(2)
    resources_by_itemid[f'{response['o:id']}'] = response
    return response


def load_data():
    pnames = set()
    pattern = r'Q\d+?\.json'
    for f in os.listdir(data_path):
        if re.match(pattern,f):
            entity_file_name = os.path.join(data_path, f)
            with open(entity_file_name, 'r') as entity_file:
                entity_json = json.load(entity_file)
                dt = {}
                if 'biographyMarkdown' in entity_json:
                    dt['biography_html'] = markdown.markdown(entity_json['biographyMarkdown'])
                if 'publications' in entity_json:
                    dt['publications'] = markdown.markdown(entity_json['publications'])

                dt['item'] = {
                    'o:item_set': [{'o:id': OMEKA_ITEM_SET}],
                    'o:site': [{'o:id': OMEKA_SITE}],
                    'o:resource_class': {'o:id':resource_class_ids['schema:Person']},
                    'o:title': [{'@value': entity_json['label'], 'type': 'literal', 'property_id': property_ids['dcterms:title']}],
                    'schema:sameAs': [{ 'type': 'uri',
                        '@id': f'https://www.wikidata.org/wiki/{entity_json['id']}',
                        'o:label': 'Wikidata',
                        'property_id': property_ids['schema:sameAs']
                        }],
                    'dbo:name': [{'type': 'literal', '@value': entity_json['label'], 'property_id': property_ids['dbo:name']}],
                    'dcterms:description': [{'type': 'literal', '@value': entity_json['description'], 'property_id': property_ids['dcterms:description']}]
                }
                for property in entity_json.get('properties', {}).values():
                    if property['key'] == 'P18':
                        if 'values' in property:
                            for property_value in property['values']:
                                if property_value.get('value-type') == 'commonsMedia':
                                    for image_info in property_value.get('image-info', []):
                                        if 'url' in image_info:
                                            if not 'images' in dt:
                                                dt['images'] = []
                                            dt['images'].append({'url': image_info['url'], 'name': property_value['name']})
                    else:
                        label = property['property']['label']
                        pnames.add(label)
                        dt['item'][property_map[label]] = []
                        if 'values' in property:
                            for property_value in property['values']:
                                if 'text' in property_value:
                                    dt['item'][property_map[label]].append(value_to_omeka_property(label, property_value))
                                else:
                                    _logger.error(f'Unable to find text in property {label}')
                                    exit(5)

                add_properties_with_location_to_map(dt['item'])
                omeka_item = save_resource(entity_json['id'], dt['item'])
                item_id = omeka_item['o:id']
                images = upload_images(item_id, dt)
                create_or_update_page(item_id, dt, images)
                _logger.info(f'Uploaded {entity_json["label"]}')

def add_properties_with_location_to_map(item):
    features = []
    p_keys = list(property_map.values())
    p_vals = list(property_map.keys())
    for prop_key in [i for i in item.keys() if i in p_keys]:
        values = [x for x in item[prop_key] if x['type'] == 'resource']
        values = [resources_by_itemid[f'{x['value_resource_id']}'] for x in values]
        for value in [v for v in values if 'o-module-mapping:feature' in v]:
            feature = value['o-module-mapping:feature'][0].copy()

            feature['o:id'] = value.get('o:id')
            prop_name = p_vals[p_keys.index(prop_key)]

            feature = {
                '@type': feature['@type'],
                'o-module-mapping:geography-type': feature['o-module-mapping:geography-type'],
                'o-module-mapping:geography-coordinates': feature['o-module-mapping:geography-coordinates'],
                'o:label': f'{prop_name.title()}:<br /> {value['o:title']}',
                # 'o:id': value.get('o:id')
                # 'o:item': {
                #     "o:id": value.get('o:id')
                # }
            }


            features.append(feature)

    if features:
        if len(features) > 1:
            item['o-module-mapping:mapping'] = {'@type': 'o-module-mapping:Map'}
        else:
            item['o-module-mapping:mapping'] = {'@type': 'o-module-mapping:Map', 'o-module-mapping:bounds': get_bounding_box(features[0]['o-module-mapping:geography-coordinates'][0], features[0]['o-module-mapping:geography-coordinates'][1], 100)}
        item['o-module-mapping:feature'] = features

def resize_image(img):
    _logger.info(f'Resizing image {img}')
    with Image.open(img) as image:
        rgb_im = image.convert("RGB")
        if rgb_im.size[0] > 800:
            rgb_im.thumbnail((800,800), Image.LANCZOS)
        rgb_im.save(img, format='JPEG')


def upload_images(item_id, dt):
    images = []
    for image in dt.get('images', []):
        temp_image = None
        img = None
        if image['url'].startswith('http'):
            temp_image = image['name']
            img = image['name']
            r = requests_session.get(image['url'], stream=True)
            if r.status_code == 200:
                with open(img, 'wb') as f:
                    for chunk in r:
                        f.write(chunk)
            else:
                _logger.error(f'Unable to load remote image {r.status_code} {image['url']} {r.text}')
        else:
            img = os.path.join(data_path, os.path.basename(image['url']))
        if os.path.getsize(img) > 1.5 * 1024 * 1024:
            resize_image(img)
        images.append(upload_media_for_item(item_id, img)['o:id'])
        if temp_image:
            os.remove(temp_image)
    return images

def create_or_update_page(item_id, dt, images):
    title = dt['item']['o:title'][0]['@value']
    page_data = {
        '@type': 'o:SitePage',
        'o:title': title,
        'o:slug': name_to_slug(title),
        'o:site': {'o:id': OMEKA_SITE},
        'o:block': [
            {'o:layout': 'html', 'o:data': {'html': dt['biography_html']}, 'o:attachment': []},
            {
                'o:layout': 'itemWithMetadata',
                'o:attachment': [{'o:item': {'@id': f'http://localhost/api/items/{item_id}', 'o:id': item_id}}]
            },
            {
                "o:layout": "mappingMap",
                "o:data": {
                    "scroll_wheel_zoom": False,
                },
                "o:layout_data": {
                    "grid_column_position": "auto",
                    "grid_column_span": "12"
                },
                "o:attachment": [
                    {
                        "o:item": {
                            "o:id": item_id
                        }
                    }]
            }
        ]
    }

    if images:
        for image in images:
            page_data['o:block'].insert(0,
                {
                    'o:layout': 'media',
                    'o:data': { 'thumbnail_type': 'medium', 'show_title_option': 'item_title' },
                    'o:layout_data': {'alignment_block': 'right'},
                    'o:attachment': [
                        {
                            'o:item': {'o:id': item_id},
                            'o:media': {'o:id': image}
                        }
                    ]
                }
            )
    existing_page_id = page_ids[name_to_slug(title)]
    if existing_page_id:
        omeka_api_put(f'/site_pages/{existing_page_id}', {}, page_data)
    else:
        omeka_api_post('/site_pages', {}, page_data)

def get_bounding_box(latitude_in_degrees, longitude_in_degrees, half_side_in_miles):
    half_side_in_km = half_side_in_miles * 1.609344
    lat = math.radians(latitude_in_degrees)
    lon = math.radians(longitude_in_degrees)
    radius  = 6371
    parallel_radius = radius*math.cos(lat)
    lat_min = lat - half_side_in_km/radius
    lat_max = lat + half_side_in_km/radius
    lon_min = lon - half_side_in_km/parallel_radius
    lon_max = lon + half_side_in_km/parallel_radius
    rad2deg = math.degrees
    return f'{rad2deg(lon_min)},{rad2deg(lat_min)},{rad2deg(lon_max)},{rad2deg(lat_max)}'

def configure_logging(name):
    root_logger = logging.getLogger()
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    root_logger.setLevel(log_level)
    console_handler = logging.StreamHandler()
    root_logger.addHandler(console_handler)
    fh_info = logging.FileHandler(name)
    fh_info.setLevel(log_level)
    root_logger.addHandler(fh_info)

def main():
    configure_logging('omeka_upload.log')
    global data_path
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'wikidata-site/public/data')
    load_data()

if __name__ == '__main__':
    main()