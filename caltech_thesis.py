import xmltodict
from datacite import schema40
import glob,json,datetime

files = glob.glob('*.xml')
for f in files:
    with open(f) as fd:
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
    metadata['resourceType']={"resourceType":\
            "Dissertation ("+eprint['thesis_degree']+")",'resourceTypeGeneral':"Text"}
    metadata['identifier'] = {'identifier':eprint['doi'],'identifierType':"DOI"}
    metadata['descriptions'] =[{'descriptionType':"Abstract",\
            'description':eprint['abstract']}]

    #Subjects
    if "keywords" in eprint:
        subjects = eprint['keywords'].split(';')
        if len(subjects) == 1:
            subjects = eprint['keywords'].split(',')
        array = []
        for s in subjects:
            array.append({'subject':s})
        metadata['subjects']=array

    #Dates
    dates = []
    dates.append({"date":datetime.date.today().isoformat(),"dateType":"Issued"})
    if 'thesis_defense_date' in eprint:
        dates.append({"date":eprint['gradofc_approval_date'],"dateType":"Accepted"})
    metadata['dates'] = dates
    
    assert schema40.validate(metadata)
    #Debugging if this fails
    #v = schema40.validator.validate(metadata)
    #errors = sorted(v.iter_errors(instance), key=lambda e: e.path)
    #for error in errors:
    #        print(error.message)

    xml = schema40.tostring(metadata)

    outname = f.split('.xml')[0]+'_datacite.xml'
    outfile = open(outname,'w')
    outfile.write(xml)

