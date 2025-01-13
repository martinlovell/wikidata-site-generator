import 'bootstrap/scss/bootstrap.scss';
import './App.scss';
import 'leaflet.fullscreen/Control.FullScreen.js'
import 'leaflet.fullscreen/Control.FullScreen.css'
import Home from './Home';
import About from './About';
import WikidataEntity from './WikidataEntity';
import { Routes, Route, useLocation } from 'react-router-dom';
import Header from './Header';
import People from './People';
import Footer from './Footer';
import { useEffect, useState } from 'react';
import FullMap from './FullMap';
import lunr from "lunr";
import Search from './Search';
import News from './News';

const quotedText = (s) => {
  let r = [];  let parts = s.split('"');
  for (let y in parts) {
    if (y%2 !== 0 && parts[y]) r.push(normalize(parts[y]))
  }
  return r;
}

const normalize = (s) => {
  if (Array.isArray(s)) return s.map(v=>normalize(v)).join(' ');
  return s && s.replace(/[.,-/#!$%^&*;:{}=\-_`~()@+?"'><[\]+']/g, '').replace(/\s{2,}/g," ").toLowerCase();
}

function ScrollToTop() {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
}

function App() {
  const [title, setTitle] = useState('')
  const [about, setAbout] = useState('')
  const [copyright, setCopyright] = useState('')
  const [idx, setIdx] = useState()
  const [searchData, setSearchData] = useState()
  const [searchString, setSearchString] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [unquotedResults, setUnquotedResults] = useState(null);

  const basename = document.querySelector('base')?.getAttribute('href') ?? '/'
  useEffect(()=>{
      fetch(`${basename}/data/site.json`)
      .then(response => response.json())
      .then(data => {
        setTitle(data['title']);
        document.title = data['title'];
        setAbout(data['about']);
        setCopyright(data['copyright']);
      })
      .catch(error => console.error(error));
  }, [basename]);

  useEffect(()=>{
    if (searchString && idx) {
      setSearchResults(search(idx, searchString));
    }
  }, [searchString, idx]);

  useEffect(()=>{
    fetch(`${basename}/data/search_index.json`)
    .then(response => response.json())
    .then(data => {
      const idx = lunr(function () {
        this.ref('id');
        this.field('Biography');
        this.field('Publications');
        this.field('Label');
        this.field('AllText');
        let searchData = {};
        data.forEach(function (doc) {
          this.add(doc);
          searchData[doc['id']] = doc;
        }, this)
        setSearchData(searchData);
      });
      setIdx(idx);
    })
    .catch(error => {
      console.error(error);
    })}
    , [basename]);

  const search = (idx, term) => {
    if (!idx) return;
    let results = idx.search(normalize(term)).map((result)=>{return {...searchData[result['ref']]}});
    let unquoted = null;
    let terms = quotedText(term);
    if (terms.length) {
      let filtered = results.filter( r => {
        for (let k in r) {
          for (let term of terms) {
            let vals = r[k]
            if (!Array.isArray(r[k])) {
              vals = [vals];
            }
            for (let val of vals) {
              if (normalize(val) === term) {
                r['exacts'] = r['exacts'] || [];
                if (k==='Label') r['exacts'].push('Name')
                else r['exacts'].push(k)
              }
            }
          }
        }
        return r['exacts'] || (Object.values(r)).some(v => v && terms.some( t => {
          return normalize(v).includes(t)}))
      });
      if (filtered.length) {
        if (results.length > filtered.length) {
          unquoted = results.filter(r => !filtered.includes(r));
        }
        results = filtered;
      }
    }
    setSearchResults(results);
    setUnquotedResults(unquoted);
    return results;
  }

  const searchFor = (term) => {
    setSearchString(term);
  }


  return (
    <div id='application' className='container-fluid' style={{minHeight: '100vh', position: 'relative'}}>
      <Header title={title} searchString={searchString}></Header>
      <div className='container'>
        <ScrollToTop />
        <Routes>
          <Route path="/" element={<Home />} base />
          <Route path="/people" element={<People />} base />
          <Route path="entity/:id" element={<WikidataEntity />} />
          <Route path="about" element={<About about={about} />} />
          <Route path="news" element={<News />} />
          <Route path="map" element={<FullMap />} />
          <Route path="search" element={<Search searchFor={searchFor} searchResults={searchResults} searchString={searchString} unquotedResults={unquotedResults} />} />
          <Route path="search/:searchparam" element={<Search searchFor={searchFor} searchResults={searchResults} searchString={searchString} unquotedResults={unquotedResults}/>} />
        </Routes>
      </div>
      <Footer copyright={copyright} ></Footer>
    </div>
  );
}

export default App;
