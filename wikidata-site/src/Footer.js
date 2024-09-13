import { format } from "date-fns"


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
        addClass(document.body, target.dataset.classname)
    } else {
        addClass(target, 'btn-secondary');
        removeClass(target, 'btn-primary')
        target.innerHTML = `Show ${target.dataset.label}`
        removeClass(document.body, target.dataset.classname)
    }
    window.scrollTo(0, document.body.scrollHeight);
}

const Footer = ({copyright}) =>
    <footer className="row bg-header">
        <div className="col-lg-8">
            <div className="footer-rights">
                <div className="all-rights-reserved">
                    <br />
                    © {format(new Date(), 'yyyy')} {copyright} • All Rights Reserved
                    <br />
                    <br />
                </div>
            </div>
        </div>
        <div className="col-lg-4">
            <div className="float-lg-end pb-5">
                <button className="btn btn-secondary active mt-4" data-label="Property Info" data-classname="show-properties" onClick={hideShowClick}>
                Show Property Info
                </button>
                <button className="btn btn-secondary active mt-4 ms-1" data-label="Change Highlights" data-classname="show-changes" onClick={hideShowClick}>
                Show Change Highlights
                </button>
            </div>
        </div>
    </footer>


export default Footer