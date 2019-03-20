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

### Python Install

You need to have Python 3.7 on your machine
([Miniconda](https://docs.conda.io/en/latest/miniconda.html) is a great
installation option).  Test whether you have python installed by opening a terminal or
anaconda prompt window and typing `python -V`, which should print version 3.7
or greater. 

### Clone epxml_to_datacite

It's best to download this software using git.  To install git, type
`conda install git` in your terminal or anaconda prompt window.  Then find where you
want the epxml_to_datacite folder to live on your computer in File Explorer or Finder
(This could be the Desktop or Documents folder, for example).  Type `cd ` 
in anaconda prompt or terminal and drag the location from the file browser into
the terminal window.  The path to the location
will show up, so your terminal will show a command like 
`cd /Users/tmorrell/Desktop`.  Hit enter.  Then type 
`git clone https://github.com/caltechlibrary/epxml_to_datacite.git`. Once you
hit enter you'll see an epxml_to_datacite folder.  Type `cd epxml_to_datacite`

### Install

Now that you're in the epxml_to_datacite folder, type `pip install -r requirements.txt`
to install dependencies.  Then type `python setup.py install` to install
scripts.  

If you will be minting DOIs, you need to create a file called `pw` using a text
editor that contains your DataCite password.  The username is hardcoded in the
script, since non-Caltech users will have to modify the script to work with
their Eprints installation. If you don't have a text editor on your machine, type
`conda install -c swc nano`

### Updating

When there is a new version of the software, go to the epxml_to_datacite
folder in anaconda prompt or terminal and type `git pull`.  You shouldn't need to re-do
the installation steps unless there are major updates.

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
`-ids` option to any command.

`python caltech_thesis.py -ids 82938`

Alternativly, you can provide a tsv file, where the first column is the Eprints
id using the `-id_file` option

`python caltech_thesis.py -id_file ids.tsv`

## Mint DOIs

You can also have the script submit the metadata to DataCite and add the DOI to the source repository. Add the `-mint`
option and if you want to make test DOIs add the `-test` option to the command line.  

`python caltech_thesis.py -mint -ids 82938`

### Advanced

You can also import the metadata transformation function into another python
script by including `from caltech_thesis import epxml_to_datacite` at the top of your new script.
Then you will be able to call `epxml_to_datacite(eprint)`, where eprint is an
xml file parsed by something like:

```
infile = open('10271.xml',encoding="utf8")
eprint = xmltodict.parse(infile.read())['eprints']['eprint']
datacite = epxml_to_datacite(eprint)
```
