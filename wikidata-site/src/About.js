import React, { useState, useEffect } from 'react';

const About = ({about, sparql})  => {
    let [latestVersion, setLatestVersion] = useState();
    const basename = document.querySelector('base')?.getAttribute('href') ?? '/'
    useEffect(()=>{
        fetch(`${basename}/LATEST_VERSION`)
        .then(response => response.text())
        .then(data => {
            setLatestVersion(data)
        })
        .catch(error => {});
    }, [basename]);
    return <>
        <h1>About</h1>
        <p>{about}</p>
        {sparql && <div><strong>SPARQL:</strong><pre>{sparql}</pre></div>}
        {latestVersion && <div>Version: {latestVersion}</div>}
    </>;
}

export default About;