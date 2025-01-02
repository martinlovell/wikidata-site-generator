import { Link } from "react-router-dom"
import { imagePath } from "./Utilities"
import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom";
import { useParams } from "react-router";
import { Col, Row } from "react-bootstrap";

const Search = ({searchResults, searchFor, unquotedResults}) => {

    const params = useParams() || {};
    const searchString = params.searchparam;
    let [searchField, setSearchField] = useState(searchString || '');
    const navigate = useNavigate();

    useEffect(()=>{
        searchFor(searchString || "");
    }, [searchString]);

    const onSearchChange = (e) => {
        setSearchField(e.target.value);
    }

    const onGetResults = () => {
        navigate('/search/' + searchField)
    }

    const onClearSearch = () => {
    }

    return <div>
        <h1>Search</h1>
        <div className="d-flex flex-row mb-5">
            <div className="flex-grow-1 me-2"><input onChange={onSearchChange} className="w-100" value={searchField} onKeyDown={e => e.key === 'Enter' && onGetResults()}/></div>
            <div>
                <button className="btn btn-search" onClick={onGetResults}>
                    <img alt="Search" src="/assets/search.png"/>
                    <img alt="Search" src="/assets/search-hover.png"/>
                </button>
            </div>
        </div>
        <div className="search-results-body">
        {searchResults && <div>
                <h5>{searchResults.length} results for {searchString}</h5>
                <div className="search-results">
                {searchResults.map((result)=><SearchResult key={result['id']} result={result} />)}
                </div>
            </div>}
        {unquotedResults && searchResults.length < 3 && <div>
            <h5 className="pt-5">{unquotedResults.length} additional results for {searchString} without quotes</h5>
                <div className="search-results">
                   {unquotedResults.map((result)=><SearchResult key={result['id']} result={result} />)}
                </div>
            </div>}
        </div>
    </div>
}



export default Search

function SearchResult({result}) {
    let link = `/entity/${result['id']}`;
    return <div className="card" key={result['id']}><Link to={link} className="stretched-link"></Link>
        <div className="d-flex  flex-wrap flex-sm-nowrap">
            <div className="">
                <img src={`/data/${result['id']}.jpg`}
                    onError={({ currentTarget }) => {
                        currentTarget.onerror = null; // prevents looping
                        currentTarget.src = "/assets/img-not-found.png";
                    } } />
            </div>
            <div className="">
                <div className="text">
                    <h4>{result['Label']}</h4>
                    {result['Description']}
                    {result['exacts'] && <div>{result['exacts'].map((e, index)=><span className="qual-label">{e}{index < result['exacts'].length - 1 && ', '}</span>)}</div>}
                </div>
            </div>
        </div>
    </div>;
}
