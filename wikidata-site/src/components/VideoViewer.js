import { useState } from "react";
import CommonsMedia from "./CommonsMedia";
import { ButtonGroup } from "react-bootstrap";


export const VideoViewer = ({videoProperties}) => {
  let [video, setVideo] = useState(videoProperties?.values[0]);
  if (video) {
    return <div className='mb-3'>
            <div className="row">
                <div className="col">
                <div className="video-content" >
                    <CommonsMedia value={video} video={true}></CommonsMedia>
                </div>
                </div>
            </div>
            <div className="row">
                <div className="col">
                <div className="video-content clearfix" >
                    {
                    videoProperties.values.length > 1 && (<ButtonGroup className="p-1">
                        {videoProperties.values.map((value, index)=> {
                            return <button onClick={()=>setVideo(value)} className={`btn btn-default ${value === video ? 'active':''}`} >{index + 1}</button>
                        })}
                        </ButtonGroup>
                    )
                    }
                </div>
                </div>
            </div>
            </div>
  }
}