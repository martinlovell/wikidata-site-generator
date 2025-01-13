import { format } from "date-fns";
import CommonsMedia from "./components/CommonsMedia";

const basename = document.querySelector('base')?.getAttribute('href') ?? '/';

export const imagePath = (path) => path.startsWith('/') ? `${basename}${path}` : path;

export const showImages = (properties, classNames, nfClassNames) => {
    if (properties['image'] && properties['image']['values'] && properties['image']['values'].length > 0) {
        return <CommonsMedia value={properties['image']['values'][0]} className={classNames}/>
    } else {
        return <img className={nfClassNames || 'wiki-image-nf'} src={imagePath('/assets/img-not-found.png')} alt='missing'/>
    }
}

export const formatWikiDateTime = (time) => {
    time = time?.replaceAll('-00', '-01').replace('Z', '').replace('+', '')
    try {
        const date = new Date(time);
        if (date) {
            let dateStr = format(date, 'yyyy');
            return dateStr;
        }
    } catch (e) {
        return time;
    }
}
