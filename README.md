# epxml_to_datacite

[![DOI](https://data.caltech.edu/badge/129455716.svg)](https://data.caltech.edu/badge/latestdoi/129455716)

Convert Eprints XML to DataCite XML.  In Development.  Only tested on Caltech
repositories.

## Contents

- caltech_thesis - Generate DataCite metadata and DOIs from CaltechTHESIS
- caltech_authors_tech_report - Generate DataCite metadata and DOIs from
  CaltechAUTHORS tech reports
- caltech_authors_to_data - Make DataCite metadata for data files in
  CaltechAUTHORS

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

## Options

There are three different scripts

- `caltech_thesis.py`
- `caltech_authors_to_data.py` (Prepares metadata from CaltechAUTHORS for submission to CaltechDATA)
- `caltech_authors_tech_report.py` (Prepares metadata from CaltechAUTHORS tech reports  with `monograph` item type (Report or Paper))

In this documentation we use `caltech_thesis.py` as the example script, but in most cases you can substitute one of the other sources.

## Basic operation

If you have Eprints XML files (from thesis.library.caltech.edu/rest/eprint/1234.xml, for example), put them in the epxml_to_datacite folder.  Type

`python caltech_thesis.py`

And you'll get '\_datacite.xml' for each xml file in the folder

## Downloading Eprints XML

You can use Eprints ids (e.g. 82938) to download Eprints xml files by adding a
`-ids` option to any command.  This requires eputil to be installed on your local systems.

`python caltech_thesis.py -ids 82938`

Alternativly, you can provide a tsv file, where the first column is the Eprints
id using the `-id_file` option

`python caltech_thesis.py -id_file ids.tsv`

## Mint DOIs

You can also have the script submit the metadata to DataCite and add the DOI to the source repository. Add the `-mint`
option and if you want to make test DOIs add the `-test` option to the command line.  

`python caltech_thesis.py -mint -ids 82938`

### Advanced

You can also import the metadata transformation function into another python script by typing
`python setup.py install` in the epxml_to_datacite directory.  Then include 
`import caltech_thesis` at the top of your new script and you wil be able to
call `epxml_to_datacite(eprint)`, where eprint is the xml parsed by something
like:

```
infile = open('10271.xml',encoding="utf8")
eprint = xmltodict.parse(infile.read())['eprints']['eprint']
```
