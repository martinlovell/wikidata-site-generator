import React, { useState, useEffect } from 'react';

const About = ({about, sparql})  => {
    let [latestVersion, setLatestVersion] = useState();
    const basename = document.querySelector('base')?.getAttribute('href') ?? '/'
    useEffect(()=>{
        fetch(`${basename}/LATEST_VERSION.txt`)
        .then(response => response.text())
        .then(data => {
            if (data.indexOf('html') < 0) {
                setLatestVersion(data)
            }
        })
        .catch(error => {console.error(error)});
    }, [basename]);
    return <>
        <h1>About</h1>
        <p>{about}</p>
        {sparql && <div><strong>SPARQL:</strong><pre>{sparql}</pre></div>}
        {latestVersion && <div><strong>Version Information</strong><pre>{latestVersion}</pre></div>}
    </>;
}

export default About;