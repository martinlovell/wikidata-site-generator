import React, { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { BoxArrowUpRight, GeoAltFill, InfoCircleFill } from 'react-bootstrap-icons';
import { formatWikiDateTime, showImages } from './Utilities';
import UVViewer from './components/UV'
import {OverlayTrigger, Tooltip } from 'react-bootstrap';
import Map from './components/Map';
import { VideoViewer } from './components/VideoViewer';
import CommonsMedia from './components/CommonsMedia';
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import PropertyInfo from './components/PropertyInfo';

// P569 DOB   P19(place)
// P570 DOD   P20(place)
// P18 image

const propertyOrder = ['P18', 'P154', 'P569', 'P19', 'P570', 'P20', 'P69', 'P108'];
const noNamePropeties = ['P18', 'P154'];
const specialProperties = ['P31', 'P21', 'P18', 'P6108', 'P10'];
const startTime = 'P580';
const endTime = 'P582';
const pointInTime = 'P585';


const sortProperties = (props) => {
    props.sort((a,b)=> {
        let aIndex = propertyOrder.indexOf(a.key)
        let bIndex = propertyOrder.indexOf(b.key)
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
    if (value['data'] && value['data']['properties'] && value['data']['properties']['P625']) {
        const pvalue = value['data']['properties']['P625']['values'][0]
        if (pvalue['value-type'] === 'globe-coordinate') {
            const long = pvalue['longitude'];
            const lat = pvalue['latitude'];
            additional_data.push(<a key='2' href={`https://maps.google.com/?q=${lat},${long}`}
                onClick={(e)=>{e.preventDefault(); map.current && map.current.toggleFullscreen()}}
                onMouseEnter={(e)=>{e.preventDefault(); setHighlightedPlace(`${value['text']}-${lat}-${long}`);}} target='_blank' rel="noreferrer" ><GeoAltFill className='info-icon'/></a>)
        }
    }
    return <>{value['text']} {additional_data.map((d)=>d)}</>;
}

const Time = ({value}) => {
    let time = value['text'];
    return <>{formatWikiDateTime(time)}</>
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
      {publication['link'] && <a href={publication['link']} title={publication['title']} target="_blank"><BoxArrowUpRight className='info-icon' /></a> }
    </div>
}


function listPublications(publications, publicationsStatus) {
    if (publications)
        return <div className={publicationsStatus && `status-${publicationsStatus}` || ''}><h3 className='property-name'>Publications</h3><div className='publications'>{publications.map((p, ix) => <Publication publication={p} ix={ix} />)}</div></div>
}

function listProperties(properties, setHighlightedPlace, map) {
    return sortProperties(Object.values(properties)).filter((property) => !specialProperties.includes(property.key)).map((property, index) => {
        return <div key={index} className={property['status'] && `status-${property['status']}` || ''}>{!noNamePropeties.includes(property.key) && <h3 className='property-name'>{property.property.label}</h3>}
            <PropertyInfo property={property} />
            {property.values.map((value, index) =>
                    <div className='property-values' key={index}>
                        <div className='font-weight-bold'><PropertyValue value={value} setHighlightedPlace={setHighlightedPlace} map={map}/>{dateQualifiers(value['qualifiers'])}
                            {(value.references) &&
                            <OverlayTrigger
                                placement='right'
                                overlay={
                                    <Tooltip id={`tooltip-${index}`} className='bg-header'>
                                        {value.references && <><strong className='section-label'>References</strong> {listReferences(value.references, setHighlightedPlace, map)}</>}
                                    </Tooltip>
                                }
                            >
                                <InfoCircleFill className='info-icon'/>
                            </OverlayTrigger>}
                        </div>
                        {value['qualifiers'] && <div className='qualifiers'>{listQualifiers(value['qualifiers'], setHighlightedPlace, map)}</div>}
                    </div>
            )}
        </div>;
    });
}

function dateQualifiers(properties) {
    if (!properties) return <></>;
    const startProp = properties.find((property) => property.key === startTime);
    const endProp = properties.find((property) => property.key === endTime);
    const pointInTimeProp = properties.find((property) => property.key === pointInTime);
    if (startProp || endProp) {
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

function listQualifiers(properties, setHighlightedPlace, map) {
    const specialProps = [startTime, endTime, pointInTime];
    return properties.map((property, index) => {
            if (specialProps.includes(property.key)) return;
            return (
                <div key={index} className='row'>
                    <div className='col-auto font-italic' key='label'>{property.property.label}:</div>
                    {property.values.map((value, index) =>
                                <div className='col-auto' key={index}><PropertyValue value={value} setHighlightedPlace={setHighlightedPlace} map={map} /></div>
                    )}
                </div> );
        })
}


function listReferences(references, setHighlightedPlace, map) {
    const specialProps = [startTime, endTime, pointInTime];
    return references.map( (properties) => properties.map((property, index) => {
            if (specialProps.includes(property.key)) return <></>;
            return (
                <div key={index}>
                    {property.values.map((value, index) =>
                                <PropertyValue value={value} setHighlightedPlace={setHighlightedPlace} map={map}/>
                    )}
                </div> );
        })
    )
}

function extractPlaces(entityData) {
    if (!entityData) return;
    let primaryLocations = [];
    Object.values(entityData.properties).filter(property => property?.values[0]?.['value-type'] === 'globe-coordinate').forEach((property)=>{
        let value = property.values[0];
        const long = value['longitude'];
        const lat = value['latitude'];
        let title = property.property.label;
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
                        let title = property.property.label;
                        let label = title;
                        let propValue = null;
                        if (title === 'coordinate location') {
                            title = `${entityProperty.property.label}: ${entityValue?.data?.label}`;
                            label = entityProperty.property.label;
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

const WikidataEntity = () => {
    let { id } = useParams();
    let [entityData, setEntityData] = useState(null);
    let [highlightedPlace, setHighlightedPlace] = useState(null);
    let map = useRef(null);
    const basename = document.querySelector('base')?.getAttribute('href') ?? '/'
    useEffect(() => {
        fetch(`${basename}/data/${id}.json`)
            .then(response => response.json())
            .then(data => setEntityData(data))
            .catch(error => console.error(error));
    }, [id, basename]);

    if (entityData) {
        return <>
            {entityData.biographyMarkdown ? <></> : <><h1 className={(entityData['labelStatus'] && ` status-${entityData['labelStatus']}` || '')}>{entityData.label}</h1>{entityData.description && <h2 className={(entityData['descriptionStatus'] && ` status-${entityData['descriptionStatus']}` || '')}>{entityData.description}</h2>}</>}
            <UVViewer manifestProperties={entityData.properties['P6108']} />
            <VideoViewer videoProperties={entityData.properties['P10']} />
            <div className='row'>
                <div className='col-lg order-2 order-lg-1 properties-list mt-3'>
                {entityData.biographyMarkdown && <div className={'markdown' + (entityData['biographyMarkdownStatus'] && ` status-${entityData['biographyMarkdownStatus']}` || '')}><Markdown remarkPlugins={[remarkGfm]}>{entityData.biographyMarkdown}</Markdown></div>}
                {
                    entityData['publications'] && listPublications(entityData['publications'], entityData['publicationsStatus'])
                }
                {
                    listProperties(entityData.properties, setHighlightedPlace, map)
                }
                </div>
                <div className='col-lg order-1 order-lg-2 mt-3'><div className='float-lg-end'><PropertyInfo property={entityData.properties['P18']}/>{showImages(entityData.properties)}<Map id='places' refpass={map} className={'map-view'} highlightedPlace={highlightedPlace} places={extractPlaces(entityData)}></Map></div></div>
            </div>
        </>;
    } else {
        return <h1>Loading</h1>;
    }
}

export default WikidataEntity;