import os,subprocess,requests,re

def download_records(ids,username,password):
    for idv in ids:
        url = 'https://'+username+':'+password+'@authors.library.caltech.edu/rest/eprint/'
        record_url = url + str(idv) +'.xml'
        execp = os.path.join(os.path.dirname(__file__),'eputil')
        record = subprocess.check_output([execp,record_url]).decode('utf-8')
        with open(idv+'.xml','w',encoding='utf8') as outfile:
            outfile.write(record)

def update_repo_doi(record_number,repo_url,identifier,username,password):
    url = repo_url + '/rest/eprint/'+str(record_number)+'/doi.txt'
    headers = {'content-type':'text/plain'}
    response = requests.put(url,data=identifier,headers=headers,auth=(username,password))
    print(response)

def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

