import xmltodict
from datacite import DataCiteMDSClient,schema43
import glob,json,datetime,re,getpass
import os,argparse,subprocess,csv,glob
from epxml_support import download_records,update_repo_doi,cleanhtml
import requests

def epxml_to_datacite(eprint):
    
    #Parse subjects file to create dictionary of Eprints keys and labels
    ref_file = os.path.join(os.path.dirname(__file__),'thesis-subjects.txt')
    infile = open(ref_file,'r')
    thesis_subjects = {}
    for line in infile:
        split = line.split(':')
        thesis_subjects[split[0]]=split[1]
    
    metadata = {}
    
    #Transforming Metadata
    newa = []
    if isinstance(eprint['creators']['item'],list) == False:
        eprint['creators']['item'] = [eprint['creators']['item']]
    for info in eprint['creators']['item']:
        new = {}
        new['affiliation'] = [
            {'name':"California Institute of Technology",
            'affiliationIdentifier':"https://ror.org/05dxps055",
            'affiliationIdentifierScheme':"ROR",
            'schemeURI':'https://ror.org'}]
        if 'orcid' in info:
            idv = []
            nid = {}
            nid['nameIdentifier'] = info['orcid']
            nid['nameIdentifierScheme'] ='ORCID'
            idv.append(nid)
            new['nameIdentifiers']=idv
        name = info['name']
        new['name'] = name['family']+', '+name['given']
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
            new['affiliations'] = [
            {'name':"California Institute of Technology",
            'affiliationIdentifier':"https://ror.org/05dxps055",
            'affiliationIdentifierScheme':"ROR",
            'schemeURI':'https://ror.org'}]
            if 'orcid' in info:
                idv = []
                nid = {}
                nid['nameIdentifier'] = info['orcid']
                nid['nameIdentifierScheme'] ='ORCID'
                idv.append(nid)
                new['nameIdentifiers']=idv
            new['contributorType'] = 'Other'
            name = info['name']
            new['name'] = name['family']+', '+name['given']
            new['givenName'] = name['given']
            new['familyName'] = name['family']
            newc.append(new)
    if 'local_group' in eprint:
        group_field = eprint['local_group']['item']
        if type(group_field) is str:
            newc.append({'name':group_field,'contributorType':'ResearchGroup'})
        else:
            for group in group_field:
                newc.append({'name':group,'contributorType':'ResearchGroup'})
    metadata['contributors'] = newc

    metadata['creators'] = newa
    metadata['titles'] = [{'title':eprint['title']}]
    metadata['publisher'] = "California Institute of Technology"
    if len(eprint['date']) != 4:
        metadata['publicationYear'] = eprint['date'].split('-')[0]
    else:
        metadata['publicationYear'] = eprint['date']
    #DataCite wants doctoral degrees tagged as dissertation
    if eprint['thesis_degree'] == 'PHD':
        metadata['types']={"resourceType":\
        "Dissertation",'resourceTypeGeneral':"Text"}
    else:
        metadata['types']={"resourceType":\
        thesis_subjects[eprint['thesis_type']],'resourceTypeGeneral':"Text"}

    if 'doi' in eprint:
            metadata['identifier'] = {'identifier':eprint['doi'],'identifierType':"DOI"}
    else:
            metadata['identifier'] = {'identifier':'10.5072/1','identifierType':"DOI"}

    metadata['alternateIdentifiers'] = [{'alternateIdentifier':eprint['eprintid'],
            'alternateIdentifierType':"Eprint_ID"}]

    if 'other_numbering_system' in eprint:
        ids = []
        if isinstance(eprint['other_numbering_system']['item'],list) == False:
            #Deal with single item listings
            eprint['other_numbering_system']['item'] = [eprint['other_numbering_system']['item']]
        for item in eprint['other_numbering_system']['item']:
            ids.append({'alternateIdentifier':item['id'],'alternateIdentifierType':item['name']['#text']})
        metadata['alternateIdentifiers'] = ids

    metadata['descriptions'] =[{'descriptionType':"Abstract",\
            'description':cleanhtml(eprint['abstract'])}]
    metadata['formats'] = ['PDF']
    metadata['version'] = 'Final'
    metadata['language'] = 'English'

    #Subjects
    #Need to remove duplicates
    subj = []
    if "keywords" in eprint:
        subjects = eprint['keywords'].split(';')
        if len(subjects) == 1:
            subjects = eprint['keywords'].split(',')
        array = []
        for s in subjects:
            if s not in subj:
                subj.append(s)
                array.append({'subject':s.strip()})
        metadata['subjects']=array
    if 'option_major' in eprint:
        if isinstance(eprint['option_major']['item'],list):
            for item in eprint['option_major']['item']:
                text = thesis_subjects[item]
                if text not in subj:
                    subj.append(text)
                    if 'subjects' in metadata:
                        metadata['subjects'].append({'subject':text})
                    else:
                        metadata['subjects'] = [{'subject':text}]
        else:
            text = thesis_subjects[eprint['option_major']['item']]
            if text not in subj:
                subj.append(text)
                if 'subjects' in metadata:
                    metadata['subjects'].append({'subject':text})
                else:
                    metadata['subjects'] = [{'subject':text}]

    if 'option_minor' in eprint:
        if isinstance(eprint['option_minor']['item'],list):
            for item in eprint['option_minor']['item']:
                text = thesis_subjects[item]
                if text not in subj:
                    subj.append(text)
                    if 'subjects' in metadata:
                        metadata['subjects'].append({'subject':text})
                    else:
                        metadata['subjects'] = [{'subject':text}]
        else:
            text = thesis_subjects[eprint['option_minor']['item']]
            if text not in subj:
                subj.append(text)
                if 'subjects' in metadata:
                    metadata['subjects'].append({'subject':text})
                else:
                    metadata['subjects'] = [{'subject':text}]

    if 'funders' in eprint:
        array = []
        if isinstance(eprint['funders']['item'],list):
            for item in eprint['funders']['item']:
                award = {}
                award['funderName'] = item['agency']
                if 'grant_number' in item:
                    if item['grant_number'] != None:
                        award['awardNumber'] = item['grant_number']
                array.append(award)
        else:
            item = eprint['funders']['item']
            award = {}
            award['funderName'] = item['agency']
            if 'grant_number' in item:
                if item['grant_number'] != None:
                    award['awardNumber'] = item['grant_number']
            array.append(award)
        metadata['fundingReferences'] = array

    if 'rights' in eprint:
        metadata['rightsList'] = [{'rights':eprint['rights']}]

    if 'related_url' in eprint:
        array = []
        if isinstance(eprint['related_url']['item'],list):
            for item in eprint['related_url']['item']:
                if 'description' in item:
                    if 'CaltechDATA' in item['description']:
                        obj = {}
                        obj['relationType']='IsSupplementedBy'
                        obj['relatedIdentifierType']='DOI'
                        obj['relatedIdentifier']=item['url']
                        array.append(obj)
        else:
            item = eprint['related_url']['item']
            if 'description' in item:
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

    #Identifiers
    if 'doi' in eprint:
        metadata['identifiers']=[{'identifier':eprint['doi'],'identifierType':'DOI'}]
    else:
        #DOI to be minted, just put prefix in identifier block
        metadata['identifiers']=[{'identifier':'10.7907','identifierType':'DOI'}]

    metadata["schemaVersion"] = "http://datacite.org/schema/kernel-4"

    return metadata

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=\
        "Make DataCite standard metadata for records from CaltechTHESIS and register DOIs")
    parser.add_argument('-mint', action='store_true', help='Mint DOIs')
    parser.add_argument('-test', action='store_true', help='Only register test DOI')
    parser.add_argument('-ids',nargs='*',help="CaltechTHESIS IDs to download XML files")
    parser.add_argument('-id_file',nargs='*',help="TSV file with CaltechTHESIS records to mint DOIs")
    parser.add_argument('-doi',nargs=1,help='Specific DOI to use, can only run one at a time')
    args = parser.parse_args()

    r_user = input('Enter your CaltechTHESIS username: ')
    r_pass = getpass.getpass()

    existing = glob.glob('*.xml')
    if len(existing) > 0 and (args.ids or args.id_file) :
        response = input("There are existing xml files in your directory. They will be used to mint DOIs unless you delete them. Do you want delete them? (Y or N)")
        if response == 'Y':
            files = glob.glob('*.xml')
            for f in files:
                os.remove(f)

    if args.ids != None:
        download_records(args.ids,'thesis',r_user,r_pass)

    if args.id_file != None:
        fname = args.id_file[0]
        with open(fname) as infile:
            ids = []
            extension = fname.split('.')[-1]
            if extension == 'csv':
                reader = csv.reader(infile, delimiter=',')
            elif extension == 'tsv':
                reader = csv.reader(infile, delimiter='\t')
            elif extension == 'txt':
                reader = csv.reader(infile, delimiter='\n')
            else:
                print(fname," Type not known")
                exit()
            for row in reader:
                if row != []:
                    if row[0] != 'Eprint ID':
                        ids.append(row[0])    
        print("Downloading records")
        download_records(ids,'thesis',r_user,r_pass)

    files = glob.glob('*.xml')
    for f in files:
        if 'datacite' not in f:
        
            print(f)

            with open(f,encoding="utf8") as fd:
                eprint = xmltodict.parse(fd.read())['eprints']['eprint']
            print(eprint['title'])

            metadata = epxml_to_datacite(eprint)
    
            #Validation fails on Windows
            #if os.name == 'nt':
            #    valid = True
            #else:
            #    valid =  schema43.validate(metadata)
            #Debugging if verification fails
            #if valid == False:
            #    v = schema43.validator.validate(metadata)
            #    errors = sorted(v.iter_errors(instance), key=lambda e: e.path)
            #    for error in errors:
            #        print(error.message)

            if args.mint != True:

                xml = schema43.tostring(metadata)

                outname = f.split('.xml')[0]+'_datacite.xml'
                outfile = open(outname,'w',encoding='utf8')
                outfile.write(xml)

            else:

                #What record in eprints are we dealing with?
                record_number = eprint['eprintid']

                if args.test== True:
                    #Existing test record
                    record_number=5756
                    prefix = '10.33569'
                    url = 'https://mds.test.datacite.org'
                    repo_url = 'http://authorstest.library.caltech.edu'
                else:
                    prefix = '10.7907'
                    url='https://mds.datacite.org'
                    repo_url = 'https://thesis.library.caltech.edu'

                #Get our DataCite password
                infile = open('pw','r')
                password = infile.readline().strip()

                # Initialize the MDS client.
                d = DataCiteMDSClient(
                username='CALTECH.LIBRARY',
                password=password,
                prefix=prefix,
                url=url
                )


                if 'doi' in eprint:
                        print("Record ",eprint['eprintid']," already has a DOI: ",eprint['doi'])
                        print("Minting a new DOI will replace the one in Eprints")
                        print("But the origional DOI will still exist")
                        response = input("Are you SURE you want to mint a new DOI? (Type Yes to continue): ")
                        if response != 'Yes':
                            print("Exiting - please remove records where you don't want to mint DOIs")
                            exit()

                #Command line option sets DOI
                if args.doi:
                    if 'doi' in eprint:
                        print("Record ",eprint['eprintid']," already has a DOI: ",eprint['doi'])
                        print("Minting a new DOI will replace the one in Eprints")
                        print("But the origional DOI will still exist")
                        response = input("Are you SURE you want to mint a new DOI? (Type Yes to continue): ")
                        if response != 'Yes':
                            print("Exiting - please remove records where you don't want to mint DOIs")
                            exit()

                    metadata['identifier'] = {'identifier':args.doi[0],'identifierType':'DOI'}
        
                xml = schema43.tostring(metadata)

                result = d.metadata_post(xml)
                identifier = result.split('(')[1].split(')')[0]
                d.doi_post(identifier,eprint['official_url'])
                print('Minted DOI: '+identifier)
                update_repo_doi(record_number,repo_url,identifier,r_user,r_pass)
                os.remove(f)
