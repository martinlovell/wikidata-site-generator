import { useState } from "react";
import { Button } from "react-bootstrap";
import { Copy } from "react-bootstrap-icons";

function unsecuredCopyToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.focus({preventScroll:true});
    textArea.select();
    try {
      document.execCommand('copy');
    } catch (err) {
      console.error('Unable to copy to clipboard', err);
    }
    document.body.removeChild(textArea);
  }


const PropertyInfo = ({property}) => {
    let [copied, setCopied] = useState(false)
    if (!property) return <></>
    const doCopy = async () => {
        // index the json 4 spaces
        let propertyJson = `"${property['key']}": #{${JSON.stringify(property, null, 4).split('\n').map((l, index)=>index>0? '    ' + l: l).join('\n')}`
        try {
            await navigator.clipboard.writeText(propertyJson);
            setCopied(true);
            setTimeout(()=>setCopied(false), 500);
        } catch (error) {
            console.error("Failed to copy to clipboard:", error);
            try {
                unsecuredCopyToClipboard(propertyJson);
                setCopied(true);
                setTimeout(()=>setCopied(false), 500);
            } catch (error2) {
                console.error("Failed unsecured also", error);
            }
        }
    }
    const copyPropertyInfo = (e) => {
        e.stopPropagation();
        doCopy();
    }
    return <div className="properties-info" key={property['key']} >
            {property['key']}<a className="btn btn-link" type="button" alt="Copy Property JSON" onClick={copyPropertyInfo}><Copy/></a>{copied && <sup> JSON Copied! </sup>}
        </div>
}

export default PropertyInfo;