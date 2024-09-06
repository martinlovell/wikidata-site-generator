# Wikidata Website Generator

## Description
- A Python script to take a list of IDs or a SPARQL Query and generate JSON files.
- A React website to display the JSON.

## Requirements
- python3.12
- node
- nvm

## Quick Start
```
# Checkout and setup environment
git clone https://github.com/martinlovell/wikidata-site-generator.git
cd wikidata-site-generator
python3 -m venv .venv
. ./.venv/bin/activate
pip3 install -r requirements.txt

# Extract data from Wikidata
python wikiloader.py --site-file demo-sites/site-cats.json

# Run the website locally
cd wikidata-site
npm install
npm start
```

## Deploy
### Webserver Configuration
#### nginx
Add the following location to your nginx config to return `index.html` when the requested file is not found so ReactRouter will work. This config will also work if you run the website(s) from a subdirectory.
```
  location ~* ^/(.+?)/.*$ {
	try_files $uri $uri/ /$1/index.html /index.html;
  }
```
### Build the Webapp
#### For the root of the webserver
```
cd wikidata-site
npm run build
```
#### For a subdirectory
```
cd wikidata-site
PUBLIC_URL=/cats npm run build
```
#### Copy files to the website document root
```
cd build
mkdir /usr/share/nginx/html/cats
cp -prv * /usr/share/nginx/html/cats/
```

## Customization
- Customizing the title and about page by editing site files. Create your own site files using the [demo-sites](demo-sites)
- Customize some styling by editing [wikidata-site/src/Style.scss](wikidata-site/src/Style.scss)
- More style changes can be in [wikidata-site/src/App.scss](wikidata-site/src/App.scss)