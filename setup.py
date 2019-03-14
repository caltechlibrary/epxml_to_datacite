from setuptools import setup,find_packages

import sys
import os
import shutil
import json

def read(fname):
    with open(fname, mode = "r", encoding = "utf-8") as f:
        src = f.read()
    return src

def read_requirements():
    """Parse requirements from requirements.txt."""
    reqs_path = os.path.join('.', 'requirements.txt')
    with open(reqs_path, 'r') as f:
        requirements = [line.rstrip() for line in f]
    return requirements

codemeta_json = "codemeta.json"

# Let's pickup as much metadata as we need from codemeta.json
with open(codemeta_json, mode = "r", encoding = "utf-8") as f:
    src = f.read()
    meta = json.loads(src)

# Let's make our symvar string
version = meta["version"]

# Now we need to pull and format our author, author_email strings.
author = ""
author_email = ""
for obj in meta["author"]:
    given = obj["givenName"]
    family = obj["familyName"]
    email = obj["email"]
    if len(author) == 0:
        author = given + " " + family
    else:
        author = author + ", " + given + " " + family
    if len(author_email) == 0:
        author_email = email
    else:
        author_email = author_email + ", " + email

# Setup for our Go based executable as a "data_file".
platform = os.uname().sysname
exec_path = "exec/Linux/eputil"
OS_Classifier = "Operating System :: POSIX :: Linux"
if platform.startswith("Darwin"):
    exec_path = "exec/MacOS/eputil"
    platform = "Mac OS X"
    OS_Classifier = "Operating System :: MacOS :: MacOS X"
elif platform.startswith("Win"):
    exec_path = "exec/Win/eputil"
    platform = "Windows"
    OS_Classifier = "Operating System :: Microsoft :: Windows :: Windows 10"

if os.path.exists(exec_path) == False:
    print("Missing executable " + exec_path + " in epxml_to_dataset module")
    sys.exit(1)

setup(
        name = 'epxml_to_datacite',
        version = version,
        description = "Convert Eprints XML to DataCite XML ato Mint DOIs",
        author = author,
        author_email = author_email,
        url = "https://caltechlibrary.github.io/epxml_to_datacite",
        download_url = "https://github.com/caltechlibrary/epxml_to_datacite/latest/releases",
        license = meta["license"],
        packages=find_packages(),
        #py_modules = ["caltech_thesis","caltech_authors_tech_report"],
        data_files=[('.',['thesis-subjects.txt']),
                    ('epxml_to_datacite',[exec_path])],
        install_requires=read_requirements(),
        classifiers = [
        "Development Status :: Beta",
        "Environment :: Console",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        OS_Classifier
    ]
)

