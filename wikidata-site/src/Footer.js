import { format } from "date-fns"
import { useEffect, useLayoutEffect } from "react";


const removeClass = (element, className) => {
    let classes = (element.className?.split(' ') || []).filter(c => c != className).join(' ');
    element.className = classes;
}

const addClass = (element, className) => {
    let classes = element.className || '';
    classes = (classes.split(' ') || []).filter(c => c != className);
    classes.push(className);
    element.className = classes.join(' ')
}

const hideShowClick = (e)=> {
    const target = e.target;
    if (target.className.includes('btn-secondary')) {
        addClass(target, 'btn-primary');
        removeClass(target, 'btn-secondary')
        target.innerHTML = `Hide ${target.dataset.label}`
        addClass(document.getElementById('application'), target.dataset.classname)
    } else {
        addClass(target, 'btn-secondary');
        removeClass(target, 'btn-primary')
        target.innerHTML = `Show ${target.dataset.label}`
        removeClass(document.getElementById('application'), target.dataset.classname)
    }
    window.scrollTo(0, document.body.scrollHeight);
}

const Footer = ({copyright}) => {
    return <footer className="row bg-header">
        <div className="col">
            <div className="footer-rights">
                <div className="all-rights-reserved">
                    <br />
                    © {format(new Date(), 'yyyy')} {copyright} • All Rights Reserved
                    <br />
                    <br />
                </div>
            </div>
        </div>
    </footer>}


export default Footer