

import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useLayoutEffect, useRef } from 'react';
import { imagePath } from "../Utilities";


var defaultIcon = L.icon({
    iconUrl: imagePath('/geo-alt-fill.svg'),
    iconSize: [20, 20],
    iconAnchor: [10, 20],
    popupAnchor: [0, -20]
});
var primaryIcon = L.icon({
    iconUrl: imagePath('/geo-alt-fill.svg'),
    iconSize: [16 * 2, 16 * 2],
    iconAnchor: [8 * 2, 16 * 2],
    popupAnchor: [0, -32]
});

const Map = ({id, places, highlightedPlace, fullscreen, className, refpass}) => {
    let map = useRef(null);
    if (refpass) {
        map = refpass;
    }
    useLayoutEffect(() => {
        try {
            if (!map.current && places?.length) {
                let centerLat = places?.[0]?.lat || 41.31755569862629;
                let centerLong = places?.[0]?.long || -72.92211258237327;
                map.current = L.map(id, {
                    fullscreenControl: true,
                    fullscreenControlOptions: {
                        position: 'topleft'
                    }
                }).setView([centerLat, centerLong], -1);
                L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 18,
                    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                }).addTo(map.current);
                let points = [];
                places?.forEach((place)=>{
                    let x = L.marker([place.lat, place.long], {'icon': place.primary ? primaryIcon : defaultIcon, '_id': `${place.value}-${place.lat}-${place.long}` }).addTo(map.current);
                    if (place.primary) {
                        x.bindPopup(`<div class="map-tooltip"><strong>${place.value}</strong></div>`)
                        x.openPopup();
                    } else {
                        x.bindTooltip(`<div class="map-tooltip"><strong>${place.label}:</strong><br />${place.value}</div>`);
                    }
                    points.push([place.lat, place.long]);
                });
                if (points.length > 1) {
                    map.current.fitBounds(points);
                    if (map.current.getZoom() > 6) {
                        map.current.setZoom(6);
                    }
                } else {
                    map.current.setZoom(6);
                }
                let fullscreenchange = null;
                if ('onfullscreenchange' in document) {
                    fullscreenchange = 'fullscreenchange';
                } else if ('onmozfullscreenchange' in document) {
                    fullscreenchange = 'mozfullscreenchange';
                } else if ('onwebkitfullscreenchange' in document) {
                    fullscreenchange = 'webkitfullscreenchange';
                }
                if (fullscreenchange) {
                    document.addEventListener(fullscreenchange, (e)=>{
                        if (e.target?.id == id) {
                            if (points.length > 1) {
                                map.current.fitBounds(points);
                                if (map.current.getZoom() > 6) {
                                    map.current.setZoom(6);
                                }
                            } else {
                                map.current.setZoom(6);
                            }
                        }
                    })
                }


            }
        } catch (e) {
            console.error(e);
        }

        if (places.length > 0 && map.current && highlightedPlace) {
            map.current.eachLayer(function (layer) {
                if (layer.options._id == highlightedPlace) {
                    layer.openTooltip();
                } else {
                    layer.closeTooltip();
                }
            });
        }

    }, [id, places, highlightedPlace, fullscreen]);
    return <div id={id} className={className} ></div>
}

export default Map;