import { imagePath } from "../Utilities";

export const CommonsImage = ({imageInfo, className, video}) => {
    let mime = imageInfo['mime'];
    if (mime.startsWith('image') && imageInfo['url']) {
        return <img className={className} src={imagePath(imageInfo['url'])} alt='CommonsImage'/>
    } else if ((mime.startsWith('video') || mime.startsWith('application/ogg') || video) && imageInfo['url']) {
        return <video autoplay
        playsInline
        muted
        autoPlay
        loop
        controls
        key={imageInfo['url']}
        preload="metadata">
                    <source src={imageInfo['url']} type={imageInfo['mime']}/>
                    Your browser does not support the video tag.
                </video>
    } else {
        //console.log(imageInfo);
    }
}

export const CommonsMedia = ({value, className, video}) => {
    if (value['image-info']) {
        return value['image-info'].map((info, index) => <CommonsImage key={index} imageInfo={info} className={className} video={video}/>)
    }
}


export default CommonsMedia;