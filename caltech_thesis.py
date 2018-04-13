import xmltodict
from datacite import schema40
import glob,json

files = glob.glob('*.xml')
for f in files:
    with open(f) as fd:
        eprint = xmltodict.parse(fd.read())['eprints']['eprint']
    print(eprint['title'])

    metadata = eprint

    assert schema40.validate(metadata)
    #Debugging if this fails
    #v = schema40.validator.validate(metadata)
    #errors = sorted(v.iter_errors(instance), key=lambda e: e.path)
    #for error in errors:
    #        print(error.message)

    xml = schema40.tostring(metadata)
    #print(json.dumps(eprint))
