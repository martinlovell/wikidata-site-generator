import React from 'react';


const News = () => {
    const newsItems = [
        {heading: "News Item 1", text: "New Item 1 text. A project to identify and share research about early Black students at Yale, 1830 to 1940. A project to identify and share research about early Black students at Yale, 1830 to 1940. A project to identify and share research about early Black students at Yale, 1830 to 1940."},
        {heading: "News Item 2", text: "New Item 2 text. A project to identify and share research about early Black students at Yale, 1830 to 1940. A project to identify and share research about early Black students at Yale, 1830 to 1940. A project to identify and share research about early Black students at Yale, 1830 to 1940."},
        {heading: "News Item 3", text: "New Item 3 text. A project to identify and share research about early Black students at Yale, 1830 to 1940. A project to identify and share research about early Black students at Yale, 1830 to 1940. A project to identify and share research about early Black students at Yale, 1830 to 1940."},
        {heading: "News Item 4", text: "New Item 4 text. A project to identify and share research about early Black students at Yale, 1830 to 1940. A project to identify and share research about early Black students at Yale, 1830 to 1940. A project to identify and share research about early Black students at Yale, 1830 to 1940."},
        {heading: "News Item 5", text: "New Item 5 text. A project to identify and share research about early Black students at Yale, 1830 to 1940. A project to identify and share research about early Black students at Yale, 1830 to 1940. A project to identify and share research about early Black students at Yale, 1830 to 1940."},
        {heading: "News Item 6", text: "New Item 6 text. A project to identify and share research about early Black students at Yale, 1830 to 1940. A project to identify and share research about early Black students at Yale, 1830 to 1940. A project to identify and share research about early Black students at Yale, 1830 to 1940."}
    ];
    return <div className='container-fluid'>
        <div className="row justify-content-center home-body">
            <div className='col-lg-4 home-text'>
                <h1><span className='subheader'>Shining Light on Truth:</span> Early Black Students at Yale</h1>
                <h2>News about a project to identify and share research about early Black students at Yale, 1830 to 1940</h2>
            </div>
            <div className='col-lg-8 news-items'>
                <h2>News</h2>
                <ul>
                    {newsItems.map((newsItem)=><li>
                        <h3>{newsItem.heading}</h3>
                        <div>{newsItem.text}</div>
                    </li>)}
                </ul>
            </div>
        </div>
    </div>
}

export default News;