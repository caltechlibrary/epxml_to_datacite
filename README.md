# epxml_to_datacite

[![DOI](https://data.caltech.edu/badge/129455716.svg)](https://data.caltech.edu/badge/latestdoi/129455716)

Convert Eprints XML to DataCite XML.  In Development.  Only tested on Caltech
repositories.

## Contents

- caltech_thesis - Transform CaltechTHESIS records to DataCite
- 


## Setup

Requires: 

- Python 3 (Recommended via [Anaconda](https://www.anaconda.com/download)) 
- xmltodict (pip install xmltodict)
- datacite (pip install datacite)

If you will be minting DOIs, you need to create a file called `pw` using a text
editor that contains your DataCite password.  The username is hardcoded in the
script, since non-Caltech users will have to modify the script to work with
their Eprints installation.

If you want to download metadata from Eprints, you need to install
[eprint-tools](https://github.com/caltechlibrary/eprinttools)

You can also import the metadata transformation function into another python script by typing
`python setup.py install` in the epxml_to_datacite directory.  Then include 
`import caltech_thesis` at the top of your new script and you wil be able to
call `epxml_to_datacite(eprint)`, where eprint is the xml parsed by something
like:

```
infile = open('10271.xml',encoding="utf8")
eprint = xmltodict.parse(infile.read())['eprints']['eprint']
```

## Downloading Eprints XML files

You can use Eprints ids (e.g. 82938) to download Eprints xml files by adding a
`-ids` option to any command.  This requires eputil to be installed on your local systems.

Alternativly, you can provide a tsv file, where the first column is the Eprints
id using the `-id_file` option

## Using caltech_thesis.py

Download .xml files from thesis.library.caltech.edu/rest/eprint/1234.xml and put 
them in the folder with caltech_thesis.py.  Type `python caltech_thesis` and
DataCite XML files will appear.  If you want to mint DOIs add the `-mint`
option and if you want to make test DOIs add the `-test` option to the command
line.  

## Using caltech_authors_tech_report.py

Will only work with items with the `monograph` item type (Report or Paper).
