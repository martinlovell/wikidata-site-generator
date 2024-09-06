import { format } from "date-fns"

const Footer = ({copyright}) =>
    <footer className="row bg-header">
        <div className="col-12">
            <div className="footer-rights">
                <div className="all-rights-reserved">
                    <br />
                    © {format(new Date(), 'yyyy')} {copyright} • All Rights Reserved
                    <br />
                    <br />

                </div>
            </div>
        </div>
    </footer>


export default Footer