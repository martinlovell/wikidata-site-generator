import { Link } from "react-router-dom"
import { imagePath } from "./Utilities"
import { Button, Dropdown, DropdownButton, DropdownMenu, DropdownToggle } from "react-bootstrap"
import { List, MenuButton } from "react-bootstrap-icons"

const Header = ({title, searchString}) =>
    <div className="row bg-header header">
        <div className="col-lg-6">
            <Link to="/"><img alt="constellations" src={imagePath('/assets/header.png')} /></Link>
            <div className="dropdown d-inline-block d-md-none">
                <Dropdown>
                    <Dropdown.Toggle><List /></Dropdown.Toggle>
                    <Dropdown.Menu>
                        <Dropdown.Item><Link to="/">Home</Link></Dropdown.Item>
                        <Dropdown.Item><Link to="/people">People</Link></Dropdown.Item>
                        <Dropdown.Item><Link to="/map">Places</Link></Dropdown.Item>
                        <Dropdown.Item><Link to="/about">About</Link></Dropdown.Item>
                        <Dropdown.Item><Link to="/news">News</Link></Dropdown.Item>
                        <Dropdown.Item><Link to="/about">Contact Us</Link></Dropdown.Item>
                        <Dropdown.Item><Link to={`/search/${searchString}`}>Search</Link></Dropdown.Item>
                    </Dropdown.Menu>
                </Dropdown>
            </div>
        </div>
        <div className="col-lg-6 mt-lg-3 text-center text-lg-end d-none d-md-block">
            <Link to="/">Home</Link>
            <Link to="/people">People</Link>
            <Link to="/map">Places</Link>
            <Link to="/about">About</Link>
            <Link to="/news">News</Link>
            <Link to="/about">Contact Us</Link>
            <Link to={`/search/${searchString}`}>Search</Link>
        </div>
    </div>


export default Header