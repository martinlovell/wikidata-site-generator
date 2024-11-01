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
OMEKA_MAPPING_FEATURE='marker'

important_places_title = 'Important Places'


_logger = logging.getLogger(__name__)

data_path = None
resources = {}
resources_by_itemid = {}
property_values_with_mapping = set()
description_by_label = {}


def load_config_file(file_name):
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), file_name)) as f:
        return json.load(f)

property_map = load_config_file('property_map.json')
property_annotation_map = load_config_file('property_annotation_map.json')
resource_class_map = load_config_file('resource_class_map.json')
resource_class_precedence = ['schema:EducationalOrganization', 'schema:Organization', 'schema:Place']



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

class property_ids_dict(dict):
    def __missing__(self, key):
        result = omeka_api_get('/properties', {'term': key})
        if result and len(result) == 1:
            self[key] = result[0]['o:id']
            return self[key]
        else:
            _logger.error(f'unable to find property [{key}]')

property_ids = property_ids_dict({})

class resource_class_ids_dict(dict):
    def __missing__(self, key):
        result = omeka_api_get('/resource_classes', {'term': key})
        if result:
            self[key] = result[0]['o:id']
            return self[key]
        else:
            print(f"****************{key}")
            exit(5)
resource_class_ids = resource_class_ids_dict({})

class page_ids_dict(dict):
    def __missing__(self, key):
        result = omeka_api_get('/site_pages', {'slug': key})
        if result:
            self[key] = result[0]['o:id']
            return self[key]
page_ids = page_ids_dict({})

item_ids_by_slug = {}

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


def upload_html_for_item(item_id, title, html):
    object = { 'o:ingester': 'html', 'o:renderer': 'html', 'file_index': 0, 'o:item': {'o:id': item_id},
    "dcterms:title": [
        {
        "type": "literal",
        "property_id": 1,
        "property_label": "Title",
        "is_public": True,
        "@value": title
        }
    ],
    'html': html}
    multipart_form_data = {'file[0]': (f'html', StringIO(html))}
    uri = f'/media?key_identity={OMEKA_KEY}&key_credential={OMEKA_CRED}'
    params = {'data': json.dumps(object)}
    response = requests_session.post(f'{OMEKA_API}{uri}', files = multipart_form_data, headers = {'Accept':'application/json'}, data = params)
    if not response.status_code == 200:
        _logger.error(f'Error uploading {title}: {response.text}')
        exit(1)
    print(f'update html response {title}')
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
    relationship = property_map[label]
    if relationship == 'schema:relatedTo':
        if property_value['value-type'] == 'wikibase-item':
            # this relies on the related item to have been previously loaded
            relative =  load_item_by_wikidata_id(property_value['id'])
            if relative:
                prop =  {'type': 'resource', 'property_label': label.title(), 'value_resource_id': relative['o:id'], 'value_resource_name': 'items', 'display_title': property_value['text'], 'property_id': property_ids[property_map[label]]}
                add_annotations(prop, label, property_value)
                _logger.info('Adding relative')
                return prop
            else:
                _logger.info('Skipping unknown relative')
                return None



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
                    # 'o:site': [{'o:id': OMEKA_SITE}],
                    'dcterms:title': [{'@value': property_value['text'], 'type': 'literal', 'property_label': 'Title', 'property_id': property_ids['dcterms:title']}],
                    'schema:sameAs': [{'type': 'uri', '@id': f'https://www.wikidata.org/wiki/{property_value['id']}', 'o:label': 'Wikidata', 'property_id': property_ids['schema:sameAs']}]
            }
            resources[property_value['id']] = resource
            coordinates = property_value.get('data', {}).get('properties', {}).get('P625')
            if coordinates:
                resource['o-module-mapping:mapping'] = {'@type': 'o-module-mapping:Map', 'o-module-mapping:bounds': get_bounding_box(coordinates['values'][0]['latitude'], coordinates['values'][0]['longitude'], 100)}
                resource[f'o-module-mapping:{OMEKA_MAPPING_FEATURE}'] = [{
                    '@type': f'o-module-mapping:{OMEKA_MAPPING_FEATURE}', 'o-module-mapping:geography-type': 'Point'
                }]
                feature = resource[f'o-module-mapping:{OMEKA_MAPPING_FEATURE}'][0]
                if OMEKA_MAPPING_FEATURE == 'marker':
                    feature['o-module-mapping:lng'] = coordinates['values'][0]['longitude']
                    feature['o-module-mapping:lat'] = coordinates['values'][0]['latitude']
                    feature['o-module-mapping:label'] = property_value['text']
                else:
                    feature['o-module-mapping:geography-coordinates'] = [coordinates['values'][0]['longitude'], coordinates['values'][0]['latitude']]

            oid = save_resource(property_value['id'], resource)['o:id']
            if coordinates:
                property_values_with_mapping.add(oid)
        prop =  {'type': 'resource', 'property_label': label.title(), 'value_resource_id': oid, 'value_resource_name': 'items', 'display_title': property_value['text'], 'property_id': property_ids[property_map[label]]}
        add_annotations(prop, label, property_value)
        return prop
    else:
        prop =  {'type': 'literal', 'property_label': label.title(), '@value': value, 'property_id': property_ids[property_map[label]]}
        add_annotations(prop, label, property_value)
        return prop

def add_annotations(prop, label, property_value):
    title_annotation = property_annotation_map.get(label)
    if label == 'relative' and 'qualifiers' in property_value:
        for qualifier in property_value['qualifiers']:
            if qualifier['key'] == 'P1039' and qualifier.get('values'): #kinship to subject
                title_annotation = qualifier['values'][0].get('text')
    if title_annotation:
        title_annotation = title_annotation.title()
        print(f'Adding annotation: {title_annotation}')
        prop['@annotation'] = {
            'dcterms:type': [
                {
                    "type": "literal",
                    "property_id": property_ids['dcterms:type'],
                    "property_label": "Type",
                    "is_public": True,
                    "@value": title_annotation
                }
            ]
        }
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
        if 'o-module-mapping:mapping' in resource and 'o-module-mapping:mapping' in existing_item:
            resource['o-module-mapping:mapping']['o:id'] = existing_item['o-module-mapping:mapping']['o:id']
        if f'o-module-mapping:{OMEKA_MAPPING_FEATURE}' in resource and f'o-module-mapping:{OMEKA_MAPPING_FEATURE}' in existing_item:
            ix = 0
            for mf in existing_item[f'o-module-mapping:{OMEKA_MAPPING_FEATURE}']:
                if len(resource[f'o-module-mapping:{OMEKA_MAPPING_FEATURE}']) > ix:
                    resource[f'o-module-mapping:{OMEKA_MAPPING_FEATURE}'][ix]['o:id'] = mf['o:id']
                    ix += 1

        response = omeka_api_put(f'/items/{existing_item['o:id']}', {}, resource)
        if not response:
            _logger.error('Unable to save resource')
            exit(2)
    resources_by_itemid[f'{response['o:id']}'] = response
    return response


def load_data():
    global description_by_label
    pnames = set()
    pattern = r'Q\d+?\.json'
    #pattern = r'Q7108504.json'
    for f in os.listdir(data_path):
        if re.match(pattern,f):
            entity_file_name = os.path.join(data_path, f)
            with open(entity_file_name, 'r') as entity_file:
                entity_json = json.load(entity_file)
                dt = {}
                if 'biographyMarkdown' in entity_json:
                    md = entity_json['biographyMarkdown']
                    md = md.split('\n', 1)[1] if '\n' in md else md
                    dt['biography_html'] = markdown.markdown(md).replace('h2>', 'h3>')
                if 'publicationsMarkdown' in entity_json:
                    dt['publications_html'] = f'<h3>Publications</h3>{markdown.markdown(entity_json['publicationsMarkdown'])}'

                dt['item'] = {
                    'o:item_set': [{'o:id': OMEKA_ITEM_SET}],
                    'o:site': [{'o:id': OMEKA_SITE}],
                    'o:resource_class': {'o:id':resource_class_ids['schema:Person']},
                    'o:title': [{'@value': entity_json['label'], 'type': 'literal', 'property_id': property_ids['dcterms:title']}],
                    'foaf:name': [{'type': 'literal', '@value': entity_json['label'], 'property_id': property_ids['foaf:name']}],
                    'dcterms:description': [{'type': 'literal', '@value': entity_json['description'], 'property_id': property_ids['dcterms:description']}]
                }

                description_by_label[entity_json['label']] = entity_json['description']
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
                                    val = value_to_omeka_property(label, property_value)
                                    if val:
                                        dt['item'][property_map[label]].append(val)
                                else:
                                    _logger.error(f'Unable to find text in property {label}')
                                    exit(5)
                dt['item']['schema:sameAs'] = [{ 'type': 'uri',
                        '@id': f'https://www.wikidata.org/wiki/{entity_json['id']}',
                        'o:label': 'Wikidata',
                        'property_id': property_ids['schema:sameAs']
                        }]
                add_properties_with_location_to_map(dt['item'])
                omeka_item = save_resource(entity_json['id'], dt['item'])
                item_id = omeka_item['o:id']
                if 'biography_html' in dt:
                    upload_html_for_item(item_id, 'Biography', dt['biography_html'])
                if 'publications_html' in dt:
                    upload_html_for_item(item_id, 'Publications', dt['publications_html'])
                    _logger.info(f'Added publication to {entity_json['label']}')
                upload_images(item_id, dt)
                title = dt['item']['o:title'][0]['@value']
                item_ids_by_slug[name_to_slug(title)] = item_id
                _logger.info(f'Uploaded {entity_json["label"]}  {item_id}')
    create_full_map_page()

def add_properties_with_location_to_map(item):
    features = []
    p_keys = list(property_map.values())
    p_vals = list(property_map.keys())
    for prop_key in [i for i in item.keys() if i in p_keys]:
        values = [x for x in item[prop_key] if x['type'] == 'resource']
        values = [resources_by_itemid[f'{x['value_resource_id']}'] for x in values if f'{x['value_resource_id']}' in resources_by_itemid]
        for value in [v for v in values if f'o-module-mapping:{OMEKA_MAPPING_FEATURE}' in v]:
            original_feature = value[f'o-module-mapping:{OMEKA_MAPPING_FEATURE}'][0].copy()
            original_feature = omeka_api_get(f'/mapping_{OMEKA_MAPPING_FEATURE}s/{original_feature['o:id']}', {})
            prop_name = p_vals[p_keys.index(prop_key)]
            feature = {
                'o:label': f'{prop_name.title()}: {value['o:title']}',
                'o-module-mapping:label': f'{prop_name.title()}: {value['o:title']}'
            }
            if '@type' in original_feature:
                feature['@type'] = original_feature['@type']

            if OMEKA_MAPPING_FEATURE == 'marker':
                feature['o-module-mapping:lng'] = original_feature['o-module-mapping:lng']
                feature['o-module-mapping:lat'] = original_feature['o-module-mapping:lat']
            else:
                feature['o-module-mapping:geography-coordinates'] = original_feature['o-module-mapping:geography-coordinates']
                feature['o-module-mapping:geography-type'] = original_feature['o-module-mapping:geography-type']
            features.append(feature)

    if features:
        if len(features) > 1:
            item['o-module-mapping:mapping'] = {'@type': 'o-module-mapping:Map'}
        else:
            feature = features[0]
            if OMEKA_MAPPING_FEATURE == 'marker':
                feature_lat = feature['o-module-mapping:lat']
                feature_lng = feature['o-module-mapping:lng']
            else:
                feature_lat = feature['o-module-mapping:geography-coordinates'][1]
                feature_lng = feature['o-module-mapping:geography-coordinates'][0]
            item['o-module-mapping:mapping'] = {'@type': 'o-module-mapping:Map', 'o-module-mapping:bounds': get_bounding_box(feature_lng, feature_lat, 100)}
        item[f'o-module-mapping:{OMEKA_MAPPING_FEATURE}'] = features

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

def create_full_map_page():
    title = important_places_title
    page_data = {
        '@type': 'o:SitePage',
        'o:title': title,
        'o:slug': name_to_slug(title),
        'o:site': {'o:id': OMEKA_SITE},
        'o:block':
            [{
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
                    } for item_id in property_values_with_mapping]
            }]
    }



    existing_page_id = page_ids[name_to_slug(title)]
    if existing_page_id:
        omeka_api_put(f'/site_pages/{existing_page_id}', {}, page_data)
    else:
        print("new map page")
        omeka_api_post('/site_pages', {}, page_data)

    pass

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

def load_descriptions():
    pattern = r'Q\d+?\.json'
    for f in os.listdir(data_path):
        if re.match(pattern,f):
            with open(os.path.join(data_path, f)) as file:
                student_json = json.load(file)
            description_by_label[student_json['label']] = student_json['description']

def create_all_people():
    pattern = r'Q\d+?\.json'
    for f in os.listdir(data_path):
        if re.match(pattern,f):
            id = f.replace('.json', '')
            if not load_item_by_wikidata_id(id):
                item = {
                    'schema:sameAs': [{ 'type': 'uri',
                            '@id': f'https://www.wikidata.org/wiki/{id}',
                            'o:label': 'Wikidata',
                            'property_id': property_ids['schema:sameAs']
                            }],
                    'o:title': "Loading...",
                    '@type': 'schema:Person',
                    'o:resource_class': {'o:id':resource_class_ids['schema:Person']},
                    'o:item_set': [{'o:id': OMEKA_ITEM_SET}],
                }
                omeka_item = omeka_api_post('/items', {}, item)
                _logger.info(f'Created item {id} with o:id {omeka_item['o:id']}')

remove_punctuation = str.maketrans('', '', string.punctuation)
def sort_name(person):
    title = person['o:title']
    parts = title.split(' ')
    while (parts[-1].endswith('.')):
        parts.pop()
    return f'{parts[-1].translate(remove_punctuation)} {title}'

def browse_page_html(site_data, omeka_site):
    html = '''<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.min.js" integrity="sha384-0pUGZvbkm6XF6gxjEnlmuGrJXVbNuzT9qBBavbLwCsOGabYfZo0T0to5eqruptLy" crossorigin="anonymous"></script>
    <style>
        .link-card {
            width: 250px;
            // height: 40rem;
            margin-bottom: 10px;
            margin-top: 10px;
            border-radius: 0;
        }
        .link-card .card-body {
            height: 470px;
            padding: 0;
            text-align: center;
        }
        .carousel-images {
            width: 250px;
            height: 337px;
        }
        .card-image {
            border: 0;
            width: 100%;
            height: 337px;
            object-fit: cover;
            margin-bottom: 10px;
            border-radius: 0;
        }
        .card-person-icon {
            background-color: #555588;
            margin-bottom: 10px;
            border-radius: 0;
        }
        .card-text {
            font-size: 10pt;
            line-height: normal;
            padding: 0 5px;
        }
        body {
            font-family: "Open Sans",sans-serif;
            font-size: 20px;
            line-height: 30px;
            word-wrap: break-word;
        }
    </style>
    '''

    html += f'''
    <h1>{site_data['title']}</h1><h2>{site_data['about']}</h2>
    <div class='container-fluid'>
         <div class="row justify-content-center">
    '''

    items = omeka_api_get(f'/items?item_set_id={OMEKA_ITEM_SET}&per_page=10000')
    people = [p for p in items if 'schema:Person' in p['@type']]

    people = sorted(people, key=sort_name)

    for person in people:
        student = person['o:title']
        image_urls = []
        for media in person['o:media']:
            media_data = omeka_api_get(f'/media/{media["o:id"]}')
            if media_data['@type'] == 'o:Media':
                try:
                    image_url = media_data['thumbnail_display_urls']['large']
                    image_urls.append(f'<img src="{image_url}" class="card-img-top card-image" alt="{student}">')
                except:
                    _logger.error(f"Unable to handle media: {media}")

        if len(image_urls) > 1:
            img_html = f'<div class="carousel-images"><div class="carousel" data-bs-ride="carousel">'
            for img in image_urls:
                img_html += f'<div class="carousel-item active">{img}</div>'
            img_html += '</div></div>'
        elif image_urls:
            img_html = image_urls[0]
        else:
            img_html = f'<div class="card-person-icon card-image"><svg xmlns="http://www.w3.org/2000/svg" width="250" height="330" fill="#ffffff" class="bi bi-person-fill" viewBox="1 1 14 14"><path d="M3 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6"/></svg></div>'


        description = '';
        if 'dcterms:description' in person:
            description = person['dcterms:description'][0]['@value']
        html += f'''
        <div class="col-auto">
            <div class="card link-card" >
            <div class="card-body">
                <a href="../item/{person['o:id']}" class="stretched-link" title="{student}"></a>
                {img_html}
                <h5 class="card-title">{student}</h5>
                <p class="card-text">{description}</p>
            </div>
            </div>
        </div>
        '''

    html += f'''
            </div>
        </div>
            '''
    return html


def map_props_to_html(property_groups):
    html = ''
    for rel in property_groups.keys():
        html += f"<h5 class='map-h5'>{rel}:</h5>"
        for person in property_groups[rel]:
            html += f'<a href=\'../item/{item_ids_by_slug[name_to_slug(person)]}\'>{person}</a><br />'
    return html


def maps_page_html():

    with open(os.path.join(data_path, 'location_information.json')) as f:
        location_info = json.load(f)


    html = '''
        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet-src.min.js" integrity="sha512-3/WyQrhTdqSVmSifQS62akgtNBhZha2lS44TnoN9Jk3J01FvsKK4suVmz6t5FtccGb5iJw58GoFhBjPE5EPc8Q==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" integrity="sha512-h9FcoyWjHcOcmEVkxOfTLnmZFWIH0iZhZT1H2TbOq55xssQGEJHEaIm+PgoUaZbRvQTNTluNOEfb1ZRy6D3BOw==" crossorigin="anonymous" referrerpolicy="no-referrer" />
        <style>
            #map {
                width: 100%;
                height: 600px;
            }
            .map-h5 {
                font-size: 10pt;
                font-weight: bold;
                margin: 0;
            }
            .map-h4 {
                font-size: 14pt;
                font-weight: bold;
                margin: 0;
            }
            .leaflet-marker-icon {
                width: 15px;
                height: 25px;
            }
        </style>
        <div id="map"></div>
        <script>
            var icon = new L.Icon.Default();
            icon.options.iconSize = [0.5 * icon.options.iconSize[0], 0.5 * icon.options.iconSize[1]];
            icon.options.iconAnchor = [0.5 * icon.options.iconAnchor[0], 0.5 * icon.options.iconAnchor[1]];
            icon.options.shadowSize = [0.5 * icon.options.shadowSize[0], 0.5 * icon.options.shadowSize[1]];
            icon.options.popupAnchor = [-3, -16];
            var map = L.map('map', {
                    fullscreenControl: true,
                    minZoom: 2,
                    fullscreenControlOptions: {
                        position: 'topleft'
                    } }).setView([41.311, -72.92], 6);
            var points = [];
            L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 18,
                minZoom: 2,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);

        '''
    points = []
    for key in location_info.keys():
        location = location_info[key]
        label = location['label']
        property_groups = {}
        for prop in location['entity_properties']:
            people = property_groups.get(prop['property_name'], [])
            property_groups[prop['property_name']] = people
            people.append(prop['entity_name'])



        points.append([location['lat'],location['long']]);

        html += f'''
            L.marker([{location['lat']},{location['long']}],{{icon:icon}}).addTo(map)
                .bindPopup("<h4 class='map-h4'>{label}</h4>{map_props_to_html(property_groups).replace('"', '&quot;')}")
            points.push([{location['lat']},{location['long']}])
        '''

    html += '''
            map.fitBounds(points);
        </script>
        '''
    return html



def home_page_html(site_data):
    html = f'''<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.min.js" integrity="sha384-0pUGZvbkm6XF6gxjEnlmuGrJXVbNuzT9qBBavbLwCsOGabYfZo0T0to5eqruptLy" crossorigin="anonymous"></script>
    <style>
        body {{
            font-family: "Open Sans",sans-serif;
            font-size: 20px;
            line-height: 30px;
            word-wrap: break-word;
        }}
        .blk {{
            background: #555555;
            height: 200px;
            width: 80%;
        }}
    </style>
    <h1>{site_data['title']}</h1><h2>{site_data['about']}</h2>
    <p>This is the home page.</p>
    <p>This page can contain whatever HTML you want.</p>
    <p>The HTML could be edited through Omeka admin, or it could be added to the GitHub repo and inserted when the site is updated.</p>
    <div class="container mb-10">
    <div class="row">
        <div class="col-sm">
        Who
        <div class="blk"></div>
        </div>
        <div class="col-sm">
        What
        <div class="blk"></div>
        </div>
        <div class="col-sm">
        Why
        <div class="blk"></div>
        </div>
    </div>
    </div>

    <small>
        The data has been generated from <a href="https://w.wiki/BXic">wikidata.org</a>.
    </small>


    '''

    return html


def update_site():
    if not description_by_label.keys():
        load_descriptions()
    omeka_site = omeka_api_get(f'/sites/{OMEKA_SITE}', {})
    with open(os.path.join(data_path, 'site.json')) as f:
        site_data = json.load(f)

    existing_browse_page = omeka_api_get('/site_pages', {'slug': 'constellations-browse-page'})
    page_data = {
        '@type': 'o:SitePage',
        'o:title': f'{site_data['title']} Browse',
        'o:slug': 'constellations-browse-page',
        'o:site': {'o:id': OMEKA_SITE},
        'o:block': [
            {'o:layout': 'html', 'o:data': {'html': browse_page_html(site_data, omeka_site)}, 'o:attachment': []},
        ]
    }
    if existing_browse_page:
        page_data['o:id'] = existing_browse_page[0]['o:id']
        response = omeka_api_put(f'/site_pages/{existing_browse_page[0]['o:id']}', {}, page_data)
    else:
        response = omeka_api_post('/site_pages', {}, page_data)
    browse_page_id = response['o:id']

    existing_home_page = omeka_api_get('/site_pages', {'slug': 'constellations-home-page'})
    page_data = {
        '@type': 'o:SitePage',
        'o:title': site_data['title'],
        'o:slug': 'constellations-home-page',
        'o:site': {'o:id': OMEKA_SITE},
        'o:block': [
            {'o:layout': 'html', 'o:data': {'html': home_page_html(site_data)}, 'o:attachment': []},
        ]
    }
    if existing_home_page:
        page_data['o:id'] = existing_home_page[0]['o:id']
        response = omeka_api_put(f'/site_pages/{existing_home_page[0]['o:id']}', {}, page_data)
    else:
        print("new home page")
        response = omeka_api_post('/site_pages', {}, page_data)
    home_page_id = response['o:id']

    existing_map_page = omeka_api_get('/site_pages', {'slug': 'constellations-map-page'})
    if item_ids_by_slug:
        page_data = {
            '@type': 'o:SitePage',
            'o:title': 'Custom Maps Page',
            'o:slug': 'constellations-map-page',
            'o:site': {'o:id': OMEKA_SITE},
            'o:block': [
                {'o:layout': 'html', 'o:data': {'html': maps_page_html()}, 'o:attachment': []},
            ]
        }
        if existing_map_page:
            page_data['o:id'] = existing_map_page[0]['o:id']
            response = omeka_api_put(f'/site_pages/{existing_map_page[0]['o:id']}', {}, page_data)
        else:
            response = omeka_api_post('/site_pages', {}, page_data)
        map_page_id = response['o:id']
    else:
        if existing_map_page:
            map_page_id = existing_map_page[0]['o:id']

    important_places_page_id = omeka_api_get('/site_pages', {'slug': name_to_slug(important_places_title)})[0]['o:id']

    site_json = omeka_api_get(f'/sites/{OMEKA_SITE}', {})
    # site_json['o:assign_new_items'] = False
    site_json['o:homepage'] = {
        "o:id": home_page_id
    }
    site_json['o:navigation'] = [
        {
        "type": "page",
        "data": {
            "id": home_page_id,
            "is_public": 1,
            "label": "Home"
        },
        "links": []
        },
        {
        "type": "page",
        "data": {
            "id": browse_page_id,
            "is_public": 1,
            "label": "Browse"
        },
        "links": []
        },
        {
        "type": "page",
        "data": {
            "id": important_places_page_id,
            "is_public": 1,
            "label": ""
        },
        "links": []
        },
        {
        "type": "mapping",
        "data": {
            "label": "View Map",
            "basemap_provider": "CartoDB.Positron"
        },
        "links": []
        },
        {
        "type": "page",
        "data": {
            "id": map_page_id,
            "is_public": 1,
            "label": "Custom Map Page"
        },
        "links": []
        },
    ]
    omeka_api_put(f'/sites/{OMEKA_SITE}', {}, site_json)

def create_site():
    with open('site.json', 'r') as entity_file:
        site_json = json.load(entity_file)
    site_json['o:slug'] = OMEKA_SITE_SLUG
    response = omeka_api_post('/sites', {}, site_json)
    return response

def create_set():
    set_json = {
        "@type": "o:Set",
        "o:title": "Constellations Set",
        "o:is_public": True,
        'dcterms:title': [{'@value': 'Constellations Set', 'type': 'literal', 'property_label': 'Title', 'property_id': property_ids['dcterms:title']}],
    }
    response = omeka_api_post('/item_sets', {}, set_json)
    return response

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

    global data_path, OMEKA_ITEM_SET, OMEKA_SITE
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'wikidata-site/public/data')


    site = omeka_api_get(f'/sites?slug={OMEKA_SITE_SLUG}', {})
    if not site:
        site = create_site()
    else:
        site = site[0]
    OMEKA_SITE = site['o:id']
    item_set = omeka_api_get(f'/item_sets?property[0][property]=dcterms:title&property[0][text]={OMEKA_ITEMSET_TITLE}&property[0][type]=eq',{})
    if not item_set:
        item_set = create_set()
    else:
        item_set = item_set[0]
    OMEKA_ITEM_SET = item_set['o:id']
    print(f"Using Site ID: {OMEKA_SITE}, and Item Set ID: {OMEKA_ITEM_SET}")
    # load_data()
    update_site()


if __name__ == '__main__':
    main()