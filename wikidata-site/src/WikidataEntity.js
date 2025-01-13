import React, { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { BoxArrowUpRight, GeoAltFill } from 'react-bootstrap-icons';
import { formatWikiDateTime, imagePath, showImages } from './Utilities';
import Map from './components/Map';
import CommonsMedia from './components/CommonsMedia';
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import PropertyInfo from './components/PropertyInfo';

// P569 DOB   P19(place)
// P570 DOD   P20(place)
// P18 image

const propertyOrder = ['image', 'logo image', 'date of birth', 'place of birth', 'date of death', 'place of death', 'educated at', 'employer'];
const noNamePropeties = ['image', 'logo image'];
const specialProperties = ['instance of', 'sex or gender', 'image', 'IIIF manifest URL', 'video'];
const startTime = 'start time';
const endTime = 'end time';
const pointInTime = 'point in time';
const kinship = 'kinship to subject';


const sortProperties = (props) => {
    props.sort((a,b)=> {
        let aIndex = propertyOrder.indexOf(a.label)
        let bIndex = propertyOrder.indexOf(b.label)
        aIndex = aIndex >= 0 ? aIndex : propertyOrder.length
        bIndex = bIndex >= 0 ? bIndex : propertyOrder.length
        // push external ids to the bottom of the list
        if (a?.values[0]?.['value-type'] === 'external-id') aIndex++;
        if (b?.values[0]?.['value-type'] === 'external-id') bIndex++;
        return aIndex - bIndex
    })
    return props;
}

const ExternalId = ({value}) => <>{value.text}</>

const WikidataItem = ({value, setHighlightedPlace, map}) => {
    const additional_data = [];
    if (value['data'] && value['data']['properties'] && value['data']['properties']['coordinate location']) {
        const pvalue = value['data']['properties']['coordinate location']['values'][0]
        if (pvalue['value-type'] === 'globe-coordinate') {
            const long = pvalue['longitude'];
            const lat = pvalue['latitude'];
            additional_data.push(<a key='2' href={`https://maps.google.com/?q=${lat},${long}`}
                onClick={(e)=>{e.preventDefault(); map.current && map.current.toggleFullscreen()}}
                onMouseEnter={(e)=>{e.preventDefault(); setHighlightedPlace(`${value['text']}-${lat}-${long}`);}} target='_blank' rel="noreferrer" ><GeoAltFill className='info-icon'/></a>)
        }
    }
    return <><Link to={`/search/"${value['text']}"`} >{value['text']}</Link> {additional_data.map((d)=>d)}</>;
}

const Time = ({value}) => {
    let time = value['text'];
    return <><Link to={`/search/${formatWikiDateTime(time)}`} >{formatWikiDateTime(time)}</Link></>
}

const Url = ({value}) => {
    const url = value['text'];
    return <><a href={url}>{url}</a></>
}

const GlobeCoordinate = ({value}) => {
    const long = value['longitude'];
    const lat = value['latitude'];
    return <><a href={`https://maps.google.com/?q=${lat},${long}`} target='_blank' rel="noreferrer">{lat} x {long} <GeoAltFill /></a></>

}

const format_amount = (amount) => {
    if (amount.startsWith('+')) amount = amount.replace('+', '');
    return amount;
}

const PropertyValue = ({value, setHighlightedPlace, map}) => {
    if (value['value-type'] === 'external-id') return <ExternalId value={value}/>
    if (value['value-type'] === 'commonsMedia') return <CommonsMedia value={value} className={'max-80'} />
    if (value['value-type'] === 'wikibase-item') return <WikidataItem value={value} setHighlightedPlace={setHighlightedPlace} map={map} />
    if (value['value-type'] === 'time') return <Time value={value} />
    if (value['value-type'] === 'url') return <Url value={value} />
    if (value['value-type'] === 'globe-coordinate') return <GlobeCoordinate value={value} />
    if (value['value-type'] === 'string' || value['value-type'] === 'monolingualtext' || value['value-type'] === 'wikibase-form') return <>{value['text']}</>
    if (value['value-type'] === 'quantity') return <>{format_amount(value['amount'])}</>
    return <div className='highlight'>{value['value-type']}</div>
}

//'title', 'date', 'link', 'journal', 'role', 'authors']
const Publication = ({publication, ix}) => {
    return <div key={ix}>{publication['role'] && `${publication['role']}: `}
      <em>{publication['title']}</em>
      {publication['journal'] && `, ${publication['journal']}`}
      {publication['date'] && ` - ${publication['date']}`}
      {publication['authors'] && ` (with: ${publication['authors']})`}
      {publication['link'] && <a href={publication['link']} title={publication['title']}  rel="noreferrer" target="_blank"><BoxArrowUpRight className='info-icon' /></a> }
    </div>
}


function listPublications(publications, publicationsStatus) {
    if (publications)
        return <div className={(publicationsStatus && `status-${publicationsStatus}`) || ''}><div className='property-name'>Publications</div><div className='publications'>{publications.map((p, ix) => <Publication publication={p} ix={ix} />)}</div></div>
}

function listProperties(properties, setHighlightedPlace, map) {
    return sortProperties(Object.values(properties)).filter((property) => !specialProperties.includes(property.label)).map((property, index) => {
        return <div key={index} className={(property['status'] && `status-${property['status']}`) || ''}>{!noNamePropeties.includes(property.label) && <div className='property-name'>{property.label}</div>}
            <PropertyInfo property={property} />
            {property.values.map((value, index) =>
                    // check for duplicates
                    <div className='property-values' key={index}>
                        <div className='font-weight-bold'><PropertyValue value={value} setHighlightedPlace={setHighlightedPlace} map={map}/>{showQualifiers(value['qualifiers'])}
                        </div>
                    </div>
            )}
        </div>;
    });
}

function showQualifiers(properties) {
    if (!properties) return <></>;
    const startProp = properties.find((property) => property.label === startTime);
    const endProp = properties.find((property) => property.label === endTime);
    const pointInTimeProp = properties.find((property) => property.label === pointInTime);
    const kinshipProp = properties.find((property) => property.label === kinship)
    if (kinshipProp) {
        return <> &mdash; {kinshipProp['values'][0]['text']}</>

    } else if (startProp || endProp) {
        const startValue = (startProp && formatWikiDateTime(startProp['values'][0]['text'])) || '';
        const endValue = (endProp && formatWikiDateTime(endProp['values'][0]['text'])) || '';
        const rangeStr = `${startValue} - ${endValue}`
        return <> ({rangeStr})</>;
    } else if (pointInTimeProp) {
        const pitValue = formatWikiDateTime(pointInTimeProp['values'][0]['text']);
        return <> ({pitValue})</>;
    } else {
        return
    }
}

function extractPlaces(entityData) {
    if (!entityData) return;
    let primaryLocations = [];
    Object.values(entityData.properties).filter(property => property?.values[0]?.['value-type'] === 'globe-coordinate').forEach((property)=>{
        let value = property.values[0];
        const long = value['longitude'];
        const lat = value['latitude'];
        let title = property.label;
        if (title === 'coordinate location') {
            title = entityData['label'];
        }
        primaryLocations.push({'lat': lat, 'long': long, 'title': title, 'label': 'Location of', 'value': title, 'primary': true});
    });
    if (!primaryLocations.length) {
        Object.values(entityData.properties).forEach((entityProperty)=>{
            entityProperty.values.forEach((entityValue) => {
                let properties = entityValue?.data?.properties;
                properties && Object.values(properties).filter(property => property?.values[0]?.['value-type'] === 'globe-coordinate').forEach(
                    (property)=>{
                        let value = property.values[0];
                        const long = value['longitude'];
                        const lat = value['latitude'];
                        let title = property.label;
                        let label = title;
                        let propValue = null;
                        if (title === 'coordinate location') {
                            title = `${entityProperty.label}: ${entityValue?.data?.label}`;
                            label = entityProperty.label;
                            propValue = entityValue?.data?.label;
                        }
                        primaryLocations.push({'lat': lat, 'long': long, 'title': title, 'label': label, 'value': propValue});
                    }
                )
            })
        });
    }
    return primaryLocations;
}

const adjustData = (d) => {
    if (d.biographyMarkdown) {
        d.biographyMarkdown = d.biographyMarkdown.replace("##", "####")
    }
    return d;
}

const WikidataEntity = () => {
    let { id } = useParams();
    let [entityData, setEntityData] = useState(null);
    let [highlightedPlace, setHighlightedPlace] = useState(null);
    let map = useRef(null);
    const basename = document.querySelector('base')?.getAttribute('href') ?? '/'
    useEffect(() => {
        fetch(`${basename}/data/${id}.json`)
            .then(response => response.json())
            .then(data => setEntityData(adjustData(data)))
            .catch(error => console.error(error));
    }, [id, basename]);

    if (entityData) {
        return <>
            {entityData.biographyMarkdown ? <></> : <><h1 className={((entityData['labelStatus'] && ` status-${entityData['labelStatus']}`) || '')}>{entityData.label}</h1>{entityData.description && <h4 className={((entityData['descriptionStatus'] && ` status-${entityData['descriptionStatus']}`) || '')}>{entityData.description}</h4>}</>}
            <div className='row'>
                <div className='col-md mt-3'>
                    {showImages(entityData.properties, 'w-100', 'wiki-image-nf-page')}
                </div>
                <div className='col-md properties-list mt-3'>
                {entityData.biographyMarkdown && <div className={'markdown' + ((entityData['biographyMarkdownStatus'] && ` status-${entityData['biographyMarkdownStatus']}`) || '')}><Markdown remarkPlugins={[remarkGfm]}>{entityData.biographyMarkdown}</Markdown></div>}
                {
                    entityData['publications'] && listPublications(entityData['publications'], entityData['publicationsStatus'])
                }
                {entityData.publicationsMarkdown && <div className={'markdown'}><h2>Publications</h2><Markdown remarkPlugins={[remarkGfm]}>{entityData.publicationsMarkdown}</Markdown></div>}
                {
                    listProperties(entityData.properties, setHighlightedPlace, map)
                }
                <div className='property-name'>Important Places</div>
                <Map id='places' refpass={map} className={'map-view'} highlightedPlace={highlightedPlace} places={extractPlaces(entityData)}></Map>
                <div key='links' >
                    <div className='property-name'>Links</div>
                        <div className='property-values' key={'links'}>
                            <div className='font-weight-bold'>
                                <a href={`https://www.wikidata.org/wiki/${id}`} rel="noreferrer" target='_blank'>View Wikidata</a>
                            </div>
                            <div className='font-weight-bold'>
                                <a href={imagePath(`/data/${id}.json`)} rel="noreferrer" target='_blank'>View Exhibit Data</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>


        </>;
    } else {
        return <h1>Loading</h1>;
    }
}

export default WikidataEntity;