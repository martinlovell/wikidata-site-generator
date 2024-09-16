import 'bootstrap/scss/bootstrap.scss';
import './App.scss';
import 'leaflet.fullscreen/Control.FullScreen.js'
import 'leaflet.fullscreen/Control.FullScreen.css'
import Home from './Home';
import About from './About';
import WikidataEntity from './WikidataEntity';
import { Routes, Route } from 'react-router-dom';
import Header from './Header';
import Footer from './Footer';
import { useEffect, useState } from 'react';
import FullMap from './FullMap';

function App() {
  const [title, setTitle] = useState('')
  const [about, setAbout] = useState('')
  const [sparql, setSparql] = useState('')
  const [copyright, setCopyright] = useState('')
  const basename = document.querySelector('base')?.getAttribute('href') ?? '/'
  useEffect(()=>{
      fetch(`${basename}/data/site.json`)
      .then(response => response.json())
      .then(data => {
        setTitle(data['title']);
        document.title = data['title'];
        setAbout(data['about']);
        setCopyright(data['copyright']);
        setSparql(data['sparql'])
      })
      .catch(error => console.error(error));
  }, [basename]);
  return (
    <div id='application' className='container-fluid' style={{minHeight: '100vh', position: 'relative'}}>
      <Header title={title}></Header>
      <div className='container' style={{paddingBottom:'150px'}}>
        <Routes>
          <Route path="/" element={<Home />} base />
          <Route path="entity/:id" element={<WikidataEntity />} />
          <Route path="about" element={<About about={about} sparql={sparql}/>} />
          <Route path="map" element={<FullMap />} />
          <Route path=":list/entity/:id" element={<WikidataEntity />} />
          <Route path=":json_file" element={<Home />} />
        </Routes>
      </div>
      <Footer copyright={copyright} ></Footer>
    </div>
  );
}

export default App;
