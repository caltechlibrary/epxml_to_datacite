from setuptools import setup
setup(
        name = 'epxml_to_datacite',
        version ='0.9',
        py_modules = ["caltech_thesis"],
        data_files=[('.',['thesis-subjects.txt'])],
        install_requires=[
            'xmltodict',
            'datacite'
        ]
    )
