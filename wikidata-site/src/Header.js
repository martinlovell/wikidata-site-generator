import { Link } from "react-router-dom"
import { imagePath } from "./Utilities"

const Header = ({title}) =>
    <div className="row bg-header">
        <div className="col-12 header">
        <Link className="navbar-brand mr-auto text-font-family text-decoration-none" to="/"><img alt="constellations" src={imagePath('/assets/header.png')} /></Link>
        </div>
        <div className="col-12">
            <nav aria-label="primary">
                <div className="navbar navbar-expand-md navbar-dark">

                    <div className="collapse navbar-collapse" id="navbarMainNav">
                        <ul className="navbar-nav ml-md-2">
                            <li className="nav-item">
                                <Link className="nav-link text-decoration-none small" to="/">People</Link>
                            </li>
                        </ul>
                        <ul className="navbar-nav ml-md-2">
                            <li className="nav-item">
                                <Link className="nav-link text-decoration-none small" to="/map">Places</Link>
                            </li>
                        </ul>
                        <ul className="navbar-nav ml-md-2">
                            <li className="nav-item">
                                <Link className="nav-link text-decoration-none small" to="/about">About</Link>
                            </li>
                        </ul>
                        <ul className="navbar-nav ml-md-2">
                            <li className="nav-item">
                                <Link className="nav-link text-decoration-none small" to="/news">News</Link>
                            </li>
                        </ul>
                        <ul className="navbar-nav ml-md-2">
                            <li className="nav-item">
                                <Link className="nav-link text-decoration-none small" to="/search">Advanced Search</Link>
                            </li>
                        </ul>
                    </div>
                    <div className="collapse navbar-collapse justify-content-end" id="navbarMainNav">
                        <ul className="navbar-nav ml-md-2">
                            <li className="nav-item me-auto">
                                <Link className="nav-link text-decoration-none small" to="/about">Contact Us</Link>
                            </li>
                        </ul>
                    </div>
                </div>
            </nav>
        </div>
    </div>


export default Header