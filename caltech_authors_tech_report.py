import xmltodict
from datacite import DataCiteMDSClient,schema40
import glob,json,datetime,re
import os,argparse,subprocess

def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def epxml_to_datacite(eprint):
    
    metadata = {}
    
    #Transforming Metadata
    #Creators
    newa = []
    if isinstance(eprint['creators']['item'],list) == False:
        eprint['creators']['item'] = [eprint['creators']['item']]
    for info in eprint['creators']['item']:
        new = {}
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
    metadata['contributors'] = newc

    metadata['titles'] = [{'title':eprint['title']}]
    if 'publisher' in eprint:
        metadata['publisher'] = eprint['publisher']
    else:
        metadata['publisher'] = "California Institute of Technology"
    if len(eprint['date']) != 4:
        metadata['publicationYear'] = eprint['date'].split('-')[0]
    else:
        metadata['publicationYear'] = eprint['date']
    metadata['resourceType']={'resourceTypeGeneral':"Text",'resourceType':"Technical Report"}

    if 'doi' in eprint:
            metadata['identifier'] = {'identifier':eprint['doi'],'identifierType':"DOI"}
    else:
            metadata['identifier'] = {'identifier':'10.5072/1','identifierType':"DOI"}

    #Waterfall for determining series name and number
    description = [{'descriptionType':"Abstract",\
            'description':cleanhtml(eprint['abstract'])}]
    name_and_series = []
    ids = []

    #All numbering systems get added to ids
    if 'other_numbering_system' in eprint:
        if isinstance(eprint['other_numbering_system']['item'],list) == False:
            #Deal with single item listings
            eprint['other_numbering_system']['item'] = [eprint['other_numbering_system']['item']]
        for item in eprint['other_numbering_system']['item']:
            ids.append({'alternateIdentifier':item['id'],'alternateIdentifierType':item['name']})

    if 'series_name' in eprint and if 'number' in eprint:
        name_and_series = [eprint['series_name'],eprint['number']]
    elif 'other_numbering_system' in eprint:
        ids = []
        #Assume first is correct
        item = eprint['other_numbering_system']['item'][0]
        name_and_series = [item['name'],item['id']]
    elif 'local_group' in eprint:
        resolver = eprint['official_url'].split(':')
        number = resolver[-1].split('.')[1]
        name_and_series = [eprint['local_group']['item'],number]
    else:
        resolver = eprint['official_url'].split(':')
        name = resolver[1].split('/')[-1]
        number = resolver[-1].split('.')[1]
        name_and_series = [name,number]
    
    #Save Series Info
    description = [{'descriptionType':"Abstract",\
            'description':cleanhtml(eprint['abstract'])}]
    description +=\
    [{'descriptionType':'SeriesInfo','description',name_and_series[0]+' '+name_and_series[1]}] 
    metadata['descriptions'] = description

    ids.append({'alternateIdentifier':name_and_series[1],'alternateIdentifierType':name_and_series[0]})

    metadata['alternateIdentifiers'] = ids

    metadata['language'] = 'English'

    #Subjects
    if "keywords" in eprint:
        subjects = eprint['keywords'].split(';')
        if len(subjects) == 1:
            subjects = eprint['keywords'].split(',')
        array = []
        for s in subjects:
            array.append({'subject':s.strip()})
        metadata['subjects']=array
   
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

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=\
        "Make DataCite standard metadata for records from CaltechAUTHORS and register DOIs")
    parser.add_argument('-mint', action='store_true', help='Mint DOIs')
    parser.add_argument('-test', action='store_true', help='Only register test DOI')
    args = parser.parse_args()

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

            if args.mint != True:

                xml = schema40.tostring(metadata)

                outname = f.split('.xml')[0]+'_datacite.xml'
                outfile = open(outname,'w',encoding='utf8')
                outfile.write(xml)

            else:
                if args.test== True:
                    prefix = '10.5072'
                else:
                    prefix = '10.7907'

                #Get our DataCite password
                infile = open('pw','r')
                password = infile.readline().strip()

                # Initialize the MDS client.
                d = DataCiteMDSClient(
                username='CALTECH.LIBRARY',
                password=password,
                prefix=prefix,
                )

                #Provide prefix to let DataCite generate DOI
                metadata['identifier'] = {'identifier':str(prefix),'identifierType':'DOI'}

                xml = schema40.tostring(metadata)

                result = d.metadata_post(xml)
                identifier = result.split('(')[1].split(')')[0]
                d.doi_post(identifier,eprint['official_url'])
                print('Minted DOI: '+identifier)


