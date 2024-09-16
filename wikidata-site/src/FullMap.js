import { useEffect, useState } from "react";
import Map from "./components/Map";

const compareProperties = (a,b) => {
    let c = a.property_name.localeCompare(b.property_name);
    if (c == 0) {
        let aN = a.entity_name.split(' ');
        let bN = b.entity_name.split(' ');
        while (aN.at(-1).endsWith('.')) aN.pop();
        while (bN.at(-1).endsWith('.')) bN.pop();
        c = aN.at(-1).localeCompare(bN.at(-1));
    }
    return c;
}

const processLocations = (locations) => {
    let places = Object.values(locations);
    places = places.map((place) => {
        place['value'] = '<ul>' + place.entity_properties.sort(compareProperties).map((p) => `<li><span class="map-property">${p.property_name}:</span> ${p.entity_name}</li>`).join('') + '</ul>';
        return place;
    })
    console.log(places)
    return places;
}

const FullMap = () => {
    let [locationInformation, setLocationInformation] = useState()
    const basename = document.querySelector('base')?.getAttribute('href') ?? '/'
    useEffect(() => {
        fetch(`${basename}/data/location_information.json`)
            .then(response => response.json())
            .then(data => setLocationInformation(data))
            .catch(error => console.error(error));
    }, [basename]);

    if (locationInformation) {
        return (
            <div className='container-fluid'>
                <Map places={processLocations(locationInformation)} id={'fullmap'} />
            </div>)
    } else {
        return <div>Loading...</div>
    }
}

export default FullMap