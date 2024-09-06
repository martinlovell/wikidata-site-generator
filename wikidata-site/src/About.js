import React from 'react';

const About = ({about, sparql}) =>
    <>
        <h1>About</h1>
        <p>{about}</p>
        {sparql && <><strong>SPARQL:</strong><pre>{sparql}</pre></>}
    </>;

export default About;