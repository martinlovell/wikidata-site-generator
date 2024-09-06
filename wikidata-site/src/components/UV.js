import { useState } from "react";
import { ButtonGroup } from "react-bootstrap";
import { imagePath } from "../Utilities";

const UV = ({manifest}) => {
    return <div className='uv-wrapper'><iframe
      key={manifest}
      className='uv-iframe'
      title="Universal Viewer"
      src={imagePath(`/uv/uv.html#?manifest=${manifest}`)}
      allowFullScreen
      data-testid="uv-viewer"
    /></div>
}

export const UVViewer = ({manifestProperties}) => {
  let [manifest, setManifest] = useState(manifestProperties?.values[0]?.text);
  if (manifest) {
      return <div className='mb-3'>
          <div className="row">
              <div className="col">
              <div className="uv-content" >
                  <UV manifest={manifest}></UV>
                </div>
              </div>
          </div>
          <div className="row">
              <div className="col">
                <div className="uv-content clearfix" >
                  {
                    manifestProperties.values.length > 1 && (<ButtonGroup className="p-1">
                        {manifestProperties.values.map((value, index)=> {
                          return <button onClick={()=>setManifest(value.text)} className={`btn btn-default ${value.text === manifest ? 'active':''}`} >{index + 1}</button>
                        })}
                      </ButtonGroup>
                    )
                  }
                  <a href={manifest} target='_blank' className='float-end btn btn-default'>View Manifest</a>
                </div>
              </div>
          </div>
          </div>

  }
}



export default UVViewer;