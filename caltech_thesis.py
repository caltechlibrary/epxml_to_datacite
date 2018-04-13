import xmltodict
import glob,json

files = glob.glob('*.xml')
for f in files:
    with open(f) as fd:
        eprint = xmltodict.parse(fd.read())['eprints']['eprint']
    print(eprint['title'])
    #print(json.dumps(eprint))
