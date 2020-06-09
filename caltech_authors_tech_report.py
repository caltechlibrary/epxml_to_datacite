import xmltodict
from datacite import DataCiteRESTClient, schema43
import glob, json, datetime, re, getpass, csv
import os, argparse, subprocess, requests
from epxml_support import download_records, update_repo_doi, cleanhtml


def epxml_to_datacite(eprint, customization=None):

    print(eprint["type"])
    if eprint["type"] not in ["monograph", "teaching_resource"]:
        raise Exception("This code has only been tested on tech reports")

    metadata = {}

    item_types = {
        "discussion_paper": "Discussion Paper",
        "documentation": "Documentation",
        "manual": "Manual",
        "other": "Other",
        "project_report": "Project Report",
        "report": "Report",
        "technical_report": "Technical Report",
        "white_paper": "White Paper",
        "working_paper": "Working Paper",
    }

    # Transforming Metadata
    # Creators
    newa = []
    if isinstance(eprint["creators"]["item"], list) == False:
        eprint["creators"]["item"] = [eprint["creators"]["item"]]
    for info in eprint["creators"]["item"]:
        new = {}
        if "orcid" in info:
            idv = []
            nid = {}
            nid["nameIdentifier"] = info["orcid"]
            nid["nameIdentifierScheme"] = "ORCID"
            idv.append(nid)
            new["nameIdentifiers"] = idv
        name = info["name"]
        new["name"] = name["family"] + ", " + name["given"]
        new["givenName"] = name["given"]
        new["familyName"] = name["family"]
        newa.append(new)
    metadata["creators"] = newa

    # Contributors
    newc = []
    if "contributors" in eprint:
        if isinstance(eprint["contributors"]["item"], list) == False:
            # Deal with single item listings
            eprint["contributors"]["item"] = [eprint["contributors"]["item"]]
        for info in eprint["contributors"]["item"]:
            new = {}
            if "orcid" in info:
                idv = []
                nid = {}
                nid["nameIdentifier"] = info["orcid"]
                nid["nameIdentifierScheme"] = "ORCID"
                idv.append(nid)
                new["nameIdentifiers"] = idv
            new["contributorType"] = "Other"
            name = info["name"]
            new["name"] = name["family"] + ", " + name["given"]
            new["givenName"] = name["given"]
            new["familyName"] = name["family"]
            newc.append(new)
    if "local_group" in eprint:
        group_field = eprint["local_group"]["item"]
        if type(group_field) is str:
            newc.append({"name": group_field, "contributorType": "ResearchGroup"})
        else:
            for group in group_field:
                newc.append({"name": group, "contributorType": "ResearchGroup"})
    metadata["contributors"] = newc

    metadata["titles"] = [{"title": eprint["title"]}]
    if "publisher" in eprint:
        metadata["publisher"] = eprint["publisher"]
    else:
        metadata["publisher"] = "California Institute of Technology"
    if len(eprint["date"]) != 4:
        metadata["publicationYear"] = eprint["date"].split("-")[0]
    else:
        metadata["publicationYear"] = eprint["date"]
    metadata["types"] = {
        "resourceTypeGeneral": "Text",
        "resourceType": item_types[eprint["monograph_type"]],
    }

    # Waterfall for determining series name and number
    if "abstract" in eprint:
        description = [
            {
                "descriptionType": "Abstract",
                "description": cleanhtml(eprint["abstract"]),
            }
        ]
    else:
        description = []
    name_and_series = []
    ids = []

    # All numbering systems get added to ids
    if "other_numbering_system" in eprint:
        if isinstance(eprint["other_numbering_system"]["item"], list) == False:
            # Deal with single item listings
            eprint["other_numbering_system"]["item"] = [
                eprint["other_numbering_system"]["item"]
            ]
        for item in eprint["other_numbering_system"]["item"]:
            ids.append({"identifier": item["id"], "identifierType": item["name"]})

    if "series_name" in eprint and "number" in eprint:
        name_and_series = [eprint["series_name"], eprint["number"]]
    elif "other_numbering_system" in eprint:
        ids = []
        # Assume first is correct
        item = eprint["other_numbering_system"]["item"][0]
        name_and_series = [item["name"]["#text"], item["id"]]
    elif "local_group" in eprint:
        resolver = eprint["official_url"].split(":")
        number = resolver[-1]
        name_and_series = [eprint["local_group"]["item"][0], number]
    else:
        resolver = eprint["official_url"].split(":")
        name = resolver[1].split("/")[-1]
        number = resolver[-1]
        name_and_series = [name, number]

    # Add DOI to identifiers
    if "doi" in eprint:
        ids.append({"identifier": eprint["doi"], "identifierType": "DOI"})

    # Save Series Info, dependent on customization
    if customization == "KISS":
        metadata["publisher"] = "Keck Institute for Space Studies"
    else:
        description += [
            {
                "descriptionType": "SeriesInformation",
                "description": name_and_series[0] + " " + name_and_series[1],
            }
        ]
        ids.append(
            {"identifier": name_and_series[1], "identifierType": name_and_series[0]}
        )
    if ids != []:
        metadata["identifiers"] = ids

    metadata["descriptions"] = description

    metadata["language"] = "English"

    # Subjects
    sub_arr = []
    if "keywords" in eprint:
        subjects = eprint["keywords"].split(";")
        if len(subjects) == 1:
            subjects = eprint["keywords"].split(",")
        for s in subjects:
            sub_arr.append({"subject": s.strip()})

    if "classification_code" in eprint:
        sub_arr.append({"subject": eprint["classification_code"]})

    if len(sub_arr) != 0:
        metadata["subjects"] = sub_arr

    if "funders" in eprint:
        array = []
        if isinstance(eprint["funders"]["item"], list):
            for item in eprint["funders"]["item"]:
                award = {}
                award["funderName"] = item["agency"]
                if "grant_number" in item:
                    if item["grant_number"] != None:
                        award["awardNumber"] = item["grant_number"]
                array.append(award)
        else:
            item = eprint["funders"]["item"]
            award = {}
            award["funderName"] = item["agency"]
            if "grant_number" in item:
                if item["grant_number"] != None:
                    award["awardNumber"] = item["grant_number"]
            array.append(award)
        metadata["fundingReferences"] = array

    if "rights" in eprint:
        metadata["rightsList"] = [{"rights": eprint["rights"]}]

    if "related_url" in eprint:
        array = []
        if isinstance(eprint["related_url"]["item"], list):
            for item in eprint["related_url"]["item"]:
                if "description" in item:
                    obj = {}
                    obj["relationType"] = "IsSupplementedBy"
                    obj["relatedIdentifierType"] = "DOI"
                    obj["relatedIdentifier"] = item["url"]
                    array.append(obj)

        else:
            item = eprint["related_url"]["item"]
            if "description" in item:
                obj = {}
                obj["relationType"] = "IsSupplementedBy"
                obj["relatedIdentifierType"] = "DOI"
                obj["relatedIdentifier"] = item["url"]
                array.append(obj)
        metadata["relatedIdentifiers"] = array

    # Dates - only if record release date present
    if "datestamp" in eprint:
        dates = []
        dates.append({"date": eprint["datestamp"], "dateType": "Available"})
        metadata["dates"] = dates

    metadata["schemaVersion"] = "http://datacite.org/schema/kernel-4"

    return metadata


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Make DataCite standard metadata for records from CaltechAUTHORS and register DOIs"
    )
    parser.add_argument("-mint", action="store_true", help="Mint DOIs")
    parser.add_argument("-test", action="store_true", help="Only register test DOI")
    parser.add_argument(
        "-ids", nargs="*", help="CaltechAUTHORS IDs to download XML files"
    )
    parser.add_argument(
        "-id_file", nargs="*", help="TSV file with CaltechAUTHORS records to mint DOIs"
    )
    parser.add_argument(
        "-doi", nargs=1, help="Specific DOI to use, can only run one at a time"
    )
    parser.add_argument("-prefix", help="DOI Prefix")
    args = parser.parse_args()

    r_user = input("Enter your CaltechAUTHORS username: ")
    r_pass = getpass.getpass()

    existing = glob.glob("*.xml")
    if len(existing) > 0 and (args.ids or args.id_file):
        response = input(
            "There are existing xml files in your directory. They will be used to mint DOIs unless you delete them. Do you want delete them? (Y or N)"
        )
        if response == "Y":
            files = glob.glob("*.xml")
            for f in files:
                os.remove(f)

    if args.ids != None:
        download_records(args.ids, "authors", r_user, r_pass)

    if args.id_file != None:
        fname = args.id_file[0]
        with open(fname) as infile:
            ids = []
            extension = fname.split(".")[-1]
            if extension == "csv":
                reader = csv.reader(infile, delimiter=",")
            elif extension == "tsv":
                reader = csv.reader(infile, delimiter="\t")
            else:
                print(fname, " Type not known")
                exit()
            for row in reader:
                if row[0] != "Eprint ID":
                    ids.append(row[0])
        print("Downloading records")
        download_records(ids, "authors", r_user, r_pass)

    files = glob.glob("*.xml")
    for f in files:
        if "datacite" not in f:

            print(f)

            with open(f, encoding="utf8") as fd:
                eprint = xmltodict.parse(fd.read())["eprints"]["eprint"]
            print(eprint["title"])

            # KISS has customizations
            customization = None
            if args.prefix != None:
                prefix = args.prefix
                if prefix == "10.26206":
                    customization = "KISS"
            else:
                prefix = "10.7907"

            metadata = epxml_to_datacite(eprint, customization)

            # Validation fails on Windows
            if os.name == "nt":
                valid = True
            else:
                valid = schema43.validate(metadata)
            # Debugging if verification fails
            if valid == False:
                v = schema43.validator.validate(metadata)
                errors = sorted(v.iter_errors(instance), key=lambda e: e.path)
                for error in errors:
                    print(error.message)

            if args.mint != True:

                xml = schema40.tostring(metadata)

                outname = f.split(".xml")[0] + "_datacite.xml"
                outfile = open(outname, "w", encoding="utf8")
                outfile.write(xml)

            else:

                # What record in eprints are we dealing with?
                record_number = eprint["eprintid"]

                if args.prefix != None:
                    prefix = args.prefix
                else:
                    prefix = "10.7907"

                # Get our DataCite password
                infile = open("pw", "r")
                password = infile.readline().strip()

                if args.test == True:
                    # Existing test record
                    record_number = 5756
                    d = DataCiteRESTClient(
                        username="CALTECH.LIBRARY",
                        password=password,
                        prefix="10.33569",
                        test_mode=True,
                    )
                    repo_url = "http://authorstest.library.caltech.edu"
                else:
                    d = DataCiteRESTClient(
                        username="CALTECH.LIBRARY", password=password, prefix="10.7907",
                    )
                    repo_url = "https://authors.library.caltech.edu"

                # Command line option sets DOI
                if args.doi:
                    if "doi" in eprint:
                        print(
                            "Record ",
                            eprint["eprintid"],
                            " already has a DOI: ",
                            eprint["doi"],
                        )
                        print("Minting a new DOI will replace the one in Eprints")
                        print("But the origional DOI will still exist")
                        response = input(
                            "Are you SURE you want to mint a new DOI? (Type Yes to continue): "
                        )
                        if response != "Yes":
                            print(
                                "Exiting - please remove records where you don't want to mint DOIs"
                            )
                            exit()

                    metadata["identifier"] = {
                        "identifier": args.doi[0],
                        "identifierType": "DOI",
                    }
                elif "doi" in eprint:
                    doi = eprint["doi"]
                    d.update_doi(doi, metadata)
                    print(
                        "Record ",
                        eprint["eprintid"],
                        " already has a DOI: ",
                        eprint["doi"],
                    )
                    print("We have updated the metadata with DataCite")
                else:
                    doi = d.public_doi(metadata, eprint["official_url"])
                    print("Minted DOI: " + doi)
                    update_repo_doi(record_number, repo_url, doi, r_user, r_pass)
                os.remove(f)
