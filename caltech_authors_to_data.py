import xmltodict
from datacite import DataCiteMDSClient,schema40
import glob,json,datetime,re,getpass
import os,argparse,subprocess
from epxml_to_datacite import download_records,update_repo_doi,cleanhtml

def epxml_to_datacite(eprint):
    
    metadata = {}
    
    #Transforming Metadata
    #Creators
    newa = []
    if isinstance(eprint['creators']['item'],list) == False:
        eprint['creators']['item'] = [eprint['creators']['item']]
    for info in eprint['creators']['item']:
        new = {}
        new['affiliations'] = ["California Institute of Technology"]
        if 'orcid' in info:
            idv = []
            nid = {}
            nid['nameIdentifier'] = info['orcid']
            nid['nameIdentifierScheme'] ='ORCID'
            idv.append(nid)
            new['nameIdentifiers']=idv
        name = info['name']
        new['creatorName'] = name['family']+', '+name['given']
        new['givenName'] = name['given']
        new['familyName'] = name['family']
        newa.append(new)
    metadata['creators'] = newa

    #Contributors
    newc = []
    if 'contributors' in eprint:
        if isinstance(eprint['contributors']['item'],list) == False:
            #Deal with single item listings
            eprint['contributors']['item'] = [eprint['contributors']['item']]
        for info in eprint['contributors']['item']:
            new = {}
            new['affiliations'] = ["California Institute of Technology"]
            if 'orcid' in info:
                idv = []
                nid = {}
                nid['nameIdentifier'] = info['orcid']
                nid['nameIdentifierScheme'] ='ORCID'
                idv.append(nid)
                new['nameIdentifiers']=idv
            new['contributorType'] = 'Other'
            name = info['name']
            new['contributorName'] = name['family']+', '+name['given']
            new['givenName'] = name['given']
            new['familyName'] = name['family']
            newc.append(new)
    if 'local_group' in eprint:
        newc.append({'contributorName':eprint['local_group']['item'],'contributorType':'ResearchGroup'})
    metadata['contributors'] = newc

    metadata['titles'] = [{'title':eprint['title']}]
    metadata['publisher'] = "CaltechDATA"
    if len(eprint['date']) != 4:
        metadata['publicationYear'] = eprint['date'].split('-')[0]
    else:
        metadata['publicationYear'] = eprint['date']
    metadata['resourceType']={'resourceTypeGeneral':"Dataset"}

    if 'doi' in eprint:
            metadata['identifier'] = {'identifier':eprint['doi'],'identifierType':"DOI"}
    else:
            metadata['identifier'] = {'identifier':'10.5072/1','identifierType':"DOI"}

    if 'other_numbering_system' in eprint:
        ids = []
        if isinstance(eprint['other_numbering_system']['item'],list) == False:
            #Deal with single item listings
            eprint['other_numbering_system']['item'] = [eprint['other_numbering_system']['item']]
        for item in eprint['other_numbering_system']['item']:
            print
            ids.append({'alternateIdentifier':item['id'],'alternateIdentifierType':item['name']['#text']})
        metadata['alternateIdentifiers'] = ids

    metadata['descriptions'] =[{'descriptionType':"Abstract",\
            'description':cleanhtml(eprint['abstract'])}]
    metadata['language'] = 'English'

    #Subjects
    sub_arr = []
    if "keywords" in eprint:
        subjects = eprint['keywords'].split(';')
        if len(subjects) == 1:
            subjects = eprint['keywords'].split(',')
        for s in subjects:
            sub_arr.append({'subject':s.strip()})

    if 'classification_code' in eprint:
        sub_arr.append({'subject':eprint['classification_code']})

    if len(sub_arr) != 0:
        metadata['subjects']=sub_arr

    if 'funders' in eprint:
        array = []
        if isinstance(eprint['funders']['item'],list):
            for item in eprint['funders']['item']:
                award = {}
                award['funderName'] = item['agency']
                if 'grant_number' in item:
                    if item['grant_number'] != None:
                        award['awardNumber'] = {'awardNumber':item['grant_number']}
                array.append(award)
        else:
            item = eprint['funders']['item']
            award = {}
            award['funderName'] = item['agency']
            if 'grant_number' in item:
                if item['grant_number'] != None:
                    award['awardNumber'] = {'awardNumber':item['grant_number']}
            array.append(award)
        metadata['fundingReferences'] = array

    if 'rights' in eprint:
        metadata['rightsList'] = [{'rights':eprint['rights']}]

    if 'related_url' in eprint:
        array = []
        if isinstance(eprint['related_url']['item'],list):
            for item in eprint['related_url']['item']:
                if 'description' in item:
                    obj = {}
                    obj['relationType']='IsSupplementedBy'
                    obj['relatedIdentifierType']='DOI'
                    obj['relatedIdentifier']=item['url']
                    array.append(obj)

        else:
            item = eprint['related_url']['item']
            if 'description' in item:
                obj = {}
                obj['relationType']='IsSupplementedBy'
                obj['relatedIdentifierType']='DOI'
                obj['relatedIdentifier']=item['url']
                array.append(obj)
        metadata['relatedIdentifiers']=array

    #Dates
    dates = []
    dates.append({"date":eprint['datestamp'],"dateType":"Available"})
    metadata['dates'] = dates

    return metadata

def download_records(ids):
    username = input('Enter your CaltechAUTHORS username: ')
    password = getpass.getpass()

    for idv in ids:
        url = 'https://'+username+':'+password+'@authors.library.caltech.edu/rest/eprint/'
        record_url = url + str(idv) +'.xml'
        record = subprocess.check_output(["eputil",record_url],universal_newlines=True)
        outfile = open(idv+'.xml','w')
        outfile.write(record)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=\
        "Make DataCite standard metadata for records from CaltechAUTHORS and register DOIs")
    parser.add_argument('-ids',nargs='*',help="CaltechAUTHORS IDs to download XML files")
    args = parser.parse_args()

    if len(args.ids) > 0:
        download_records(args.ids)

    files = glob.glob('*.xml')
    for f in files:
        if 'datacite' not in f:
        
            print(f)

            with open(f,encoding="utf8") as fd:
                eprint = xmltodict.parse(fd.read())['eprints']['eprint']
            print(eprint['title'])

            metadata = epxml_to_datacite(eprint)
    
            #Validation fails on Windows
            valid =  schema40.validate(metadata)
            #Debugging if this fails
            if valid == False:
                v = schema40.validator.validate(metadata)
                errors = sorted(v.iter_errors(instance), key=lambda e: e.path)
                for error in errors:
                    print(error.message)

            xml = schema40.tostring(metadata)

            outname = f.split('.xml')[0]+'_datacite.xml'
            outfile = open(outname,'w',encoding='utf8')
            outfile.write(xml)

            outname = f.split('.xml')[0]+'_datacite.json'
            outfile = open(outname,'w',encoding='utf8')
            json.dump(metadata,outfile)

