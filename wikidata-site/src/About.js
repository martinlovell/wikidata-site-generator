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
        <div className='row'>
            <div className='col-lg-4 home-text'>
                <h1><span className='subheader'>Shining Light on Truth:</span> Early Black Students at Yale</h1>
                <h2>A project to identify and share research about early Black students at Yale, 1830 to 1940</h2>
            </div>
            <div className='col-lg-8 about-body'>
                {about}
            </div>
        </div>
        {latestVersion && <div><strong>Version Information</strong><pre>{latestVersion}</pre></div>}
    </>;
}

export default About;