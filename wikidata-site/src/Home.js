import React from 'react';
import { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { formatWikiDateTime, showImages } from './Utilities';

const extractFirstPropertyValue = (properties, propertyKey) => {
    if (properties[propertyKey]) {
        let prop = properties[propertyKey];
        let values = prop['values'];
        if (values && values.length) {
            let valueText = values[0]['text'];
            if (values[0]['value-type'] === 'time') {
                valueText = formatWikiDateTime(valueText);
            }
            return valueText || '';
        }
    }
    return '';
}

const extractPropertyList = (properties, propertyKey) => {
    if (properties[propertyKey]) {
        let prop = properties[propertyKey];
        let values = prop['values'];
        return <ul className='compact-list'>{values.map((value, index)=> {
            let valueText = value['text'];
            return <li key={index}><small>{valueText}</small></li>
        })}</ul>
    }
}

const EntityLink = ({id, description, label, properties, status}) => {
    let link = `/entity/${id}`
    let additionalProperties = []
    let dob = extractFirstPropertyValue(properties, 'P569');
    let dod = extractFirstPropertyValue(properties, 'P570');
    if (dob || dod) additionalProperties.push(`${dob} - ${dod}`);

    return <div className={'card link-card' + (status && ` status-${status}` || '')} key={id}>
                {status != 'removed' && <Link to={link} className="stretched-link"></Link>}
                {showImages(properties)}
                <div className="card-body">
                    <h5 className="card-title">{label}</h5>
                    <p className="card-text">{description}</p>
                    {/* {additionalProperties.map((p, index)=><p key={index} className="card-text">{p}</p>)}
                    {extractPropertyList(properties, 'P69')} */}
                    {status != 'removed' && <Link to={link} className="visually-hidden">View</Link>}
                </div>
           </div>
}


const entitySort = (a,b) => {
    let aa = a.label.split(' ');
    let bb = b.label.split(' ');
    while (aa[aa.length-1].endsWith('.')) aa.pop();
    while (bb[bb.length-1].endsWith('.')) bb.pop();
    a = aa[aa.length-1] + a.label.replace(',','').replace('.','');
    b = bb[bb.length-1] + b.label.replace(',','').replace('.','');
    return (a > b) ? 1 : -1;
}

const Home = () => {
    let { json_file } = useParams();
    let [entityList, setEntityList] = useState(null);
    const basename = document.querySelector('base')?.getAttribute('href') ?? '/'
    useEffect(() => {
        fetch(`${basename}/data/${json_file || 'entity_list'}.json`)
            .then(response => response.json())
            .then(data => setEntityList(data))
            .catch(error => console.error(error));
    }, [json_file, basename]);

    if (entityList) {
        return (
            <div className='container-fluid'>
                <div className="row justify-content-center">
                {
                    entityList.sort(entitySort).map((entityRef, index) => {
                        return <div className="col-auto" key={index}><EntityLink {...entityRef} /></div>
                    })
                }
                </div>
            </div>)
    } else {
        return <h1>Loading</h1>;
    }
}

export default Home;