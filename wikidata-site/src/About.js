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
        <div className='about-body'>
            <h1>Shining Light on Truth: Early Black Lives at Yale, 1830-1940</h1>
            <h2>About</h2>
            <p>{about}</p>
        </div>
        {latestVersion && <div><strong>Version Information</strong><pre>{latestVersion}</pre></div>}
    </>;
}

export default About;