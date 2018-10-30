from setuptools import setup
setup(
        name = 'epxml_to_datacite',
        version ='0.10',
        py_modules = ["caltech_thesis","caltech_authors_tech_report"],
        data_files=[('.',['thesis-subjects.txt'])],
        install_requires=[
            'xmltodict',
            'datacite'
        ]
    )
