import React from 'react';
import { useNavigate } from 'react-router-dom';
import { imagePath } from './Utilities';


const Home = () => {
    const navigate = useNavigate();
    return <div className='container-fluid'>
        <div className="row justify-content-center home-body">
            <div className='col-lg-8 hero'><img alt="home hero image" className='hero-img' src={imagePath('/assets/hero-1.png')} /></div>
            <div className='col-lg-4 home-text'>
                <h1>Early Black Students at Yale</h1>
                <h2>A project to identify and share research about early Black students at Yale, 1830 to 1940</h2>
                <div className='search-link'>
                    <button className='btn-const' onClick={()=>navigate('/search/')}>
                        <div className='btn-inner'>Search
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 -2 20 20" stroke="currentColor" fill='none' strokeWidth={1.5} >
                                <circle cx="8" cy="8" r="8" />
                                <path d="M6.5 2 L12 8 L6.5 14"/>
                            </svg>
                        </div>
                    </button>
                </div>
            </div>
        </div>
    </div>
}

export default Home;