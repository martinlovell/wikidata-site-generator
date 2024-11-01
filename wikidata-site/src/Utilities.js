import { format } from "date-fns";
import { Accordion, Carousel } from 'react-bootstrap';
import CommonsMedia from "./components/CommonsMedia";
import PropertyInfo from "./components/PropertyInfo";

const basename = document.querySelector('base')?.getAttribute('href') ?? '/';

export const imagePath = (path) => path.startsWith('/') ? `${basename}${path}` : path;

export const showImages = (properties) => {
    if (properties['P18'] && properties['P18']['values'] && properties['P18']['values'].length > 1) {
        return <div className='carousel-images'>
            <Carousel>
            {properties['P18']['values'].map((value, index) => {
                if (value['value-type'] === 'commonsMedia') return <Carousel.Item key={index}><CommonsMedia value={value} className={"wiki-image"}/></Carousel.Item>
                else return <></>
            })}
            </Carousel>
        </div>
    } else if (properties['P18'] && properties['P18']['values'] && properties['P18']['values'].length === 1) {
        return <CommonsMedia value={properties['P18']['values'][0]} className={'wiki-image commons-image'}/>
    } else {
        return <img className='wiki-image-nf' src={imagePath('/assets/img-not-found.png')} alt='missing'/>
    }
}

export const formatWikiDateTime = (time) => {
    time = time?.replaceAll('-00', '-01').replace('Z', '').replace('+', '')
    try {
        const date = new Date(time);
        if (date) {
            let dateStr = format(date, 'yyyy');
            if (dateStr.startsWith('01/01/')) {
                dateStr = dateStr.replace('01/01/', '');
            }
            return dateStr;
        }
    } catch (e) {
        return time;
    }
}
