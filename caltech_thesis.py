import xmltodict
from datacite import DataCiteMDSClient,schema40
import glob,json,datetime,re,argparse,subprocess
import base32_crockford, random

def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

parser = argparse.ArgumentParser(description=\
        "Make DataCite standard metadata for records from CaltechTHESIS and register DOIs")
parser.add_argument('-mint', action='store_true', help='Mint DOIs')
parser.add_argument('-test', action='store_true', help='Only register test DOI')
args = parser.parse_args()

#Parse subjects file to create dictionary of Eprints keys and labels
infile = open('thesis-subjects.txt','r')
thesis_subjects = {}
for line in infile:
    split = line.split(':')
    thesis_subjects[split[0]]=split[1]

files = glob.glob('*.xml')
for f in files:
    if 'datacite' not in f:
        
        print(f)

        with open(f,encoding="utf8") as fd:
            eprint = xmltodict.parse(fd.read())['eprints']['eprint']
        print(eprint['title'])

        metadata = {}
    
        #Transforming Metadata
        #Creators
        newa = []
        info = eprint['creators']['item']
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
        new['creatorName'] = name['family']+','+name['given']
        new['givenName'] = name['given']
        new['familyName'] = name['family']
        newa.append(new)

        metadata['creators'] = newa
        metadata['titles'] = [{'title':eprint['title']}]
        metadata['publisher'] = "California Institute of Technology"
        metadata['publicationYear'] = eprint['date']
        #DataCite wants doctoral degrees tagged as dissertation
        if eprint['thesis_degree'] == 'PHD':
            metadata['resourceType']={"resourceType":\
            "Dissertation",'resourceTypeGeneral':"Text"}
        else:
            metadata['resourceType']={"resourceType":\
            thesis_subjects[eprint['thesis_type']],'resourceTypeGeneral':"Text"}
    
        if 'doi' in eprint:
            metadata['identifier'] = {'identifier':eprint['doi'],'identifierType':"DOI"}
        else:
            metadata['identifier'] = {'identifier':'10.5072/1','identifierType':"DOI"}

        metadata['alternateIdentifiers'] = [{'alternateIdentifier':eprint['eprintid'],
            'alternateIdentifierType':"Eprint_ID"}]

        metadata['descriptions'] =[{'descriptionType':"Abstract",\
            'description':cleanhtml(eprint['abstract'])}]
        metadata['formats'] = ['PDF']
        metadata['version'] = 'Final'
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
        if 'option_major' in eprint:
            if isinstance(eprint['option_major']['item'],list):
                for item in eprint['option_major']['item']:
                    text = thesis_subjects[item]
                    metadata['subjects'].append({'subject':text})
            else:
                text = thesis_subjects[eprint['option_major']['item']]
                metadata['subjects'].append({'subject':text})
        if 'option_minor' in eprint:
            if isinstance(eprint['option_minor']['item'],list):
                for item in eprint['option_minor']['item']:
                    text = thesis_subjects[item]
                    metadata['subjects'].append({'subject':text})
            else:
                text = thesis_subjects[eprint['option_minor']['item']]
                metadata['subjects'].append({'subject':text})
    
        if 'funders' in eprint:
            array = []
            if isinstance(eprint['funders']['item'],list):
                for item in eprint['funders']['item']:
                    award = {}
                    award['funderName'] = item['agency']
                    if 'grant_number' in item:
                        award['awardNumber'] = {'awardNumber':item['grant_number']}
                    array.append(award)
            else:
                item = eprint['funders']['item']
                award = {}
                award['funderName'] = item['agency']
                if 'grant_number' in item:
                    award['awardNumber'] = {'awardNumber':item['grant_number']}
                array.append(award)
            metadata['fundingReferences'] = array

        if 'rights' in eprint:
            metadata['rightsList'] = [{'rights':eprint['rights']}]

        if 'related_url' in eprint:
            array = []
            if isinstance(eprint['related_url']['item'],list):
                for item in eprint['related_url']['item']:
                    if 'CaltechDATA' in item['description']:
                        obj = {}
                        obj['relationType']='IsSupplementedBy'
                        obj['relatedIdentifierType']='DOI'
                        obj['relatedIdentifier']=item['url']
                        array.append(obj)
            else:
                item = eprint['related_url']['item']
                if 'CaltechDATA' in item['description']:
                    obj = {}
                    obj['relationType']='IsSupplementedBy'
                    obj['relatedIdentifierType']='DOI'
                    obj['relatedIdentifier']=item['url']
                    array.append(obj)
            metadata['relatedIdentifiers']=array

        #Dates
        dates = []
        if 'gradofc_approval_date' in eprint:
            dates.append({"date":eprint['gradofc_approval_date'],"dateType":"Accepted"})
        #These are scanned records, we just list when they were made available
        else:
            dates.append({"date":eprint['datestamp'],"dateType":"Available"})
        metadata['dates'] = dates
    
        #Validation fails on Windows
        #assert schema40.validate(metadata)
        #Debugging if this fails
        #v = schema40.validator.validate(metadata)
        #errors = sorted(v.iter_errors(instance), key=lambda e: e.path)
        #for error in errors:
        #        print(error.message)

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
            #test_mode=True
            )

            #Provide prefix to let DataCite generate DOI
            metadata['identifier'] = {'identifier':str(prefix),'identifierType':'DOI'}

            xml = schema40.tostring(metadata)

            result = d.metadata_post(xml)
            identifier = result.split('(')[1].split(')')[0]
            d.doi_post(identifier,eprint['official_url'])
            print('Minted DOI: '+identifier)


