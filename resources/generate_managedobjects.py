#!/usr/bin/python
"""A script that parses vSphere API documentation and generates a YAML
dump of the Managed Object's and their properties.

It expects to run from the SDK/doc/ReferenceGuide/ directory and
is quite kludgy so I expect that it is highly version dependent.
"""
# Copyright 2010 Jonathan Kinred

from BeautifulSoup import BeautifulSoup
import yaml

# This file is the starting point for managed objects
f = open("index-mo_types.html")
contents = BeautifulSoup(f.read())
f.close()

# <div>'s with these attributes are the ones that contain managed objects
mo_divs = contents.findAll(name="div",
                           attrs={"id": ["AE", "FJ", "KO", "PT", "UZ"]})

# Collect the parsed managed object's in this list
unordered_managed_objects = []

# Here, we look at all the <div>'s, find the file which it links to,
# opens it and parses the information inside
for div in mo_divs:
    # The <a> node contain the stuff we want
    for a in div.findAll("a"):
        # Collect the parsed managed object in this dict
        mo = {}
        mo["name"] = str(a.string)
        print("Generating information for %s" % mo["name"])
        # Open up the HTML page for the MO and load a new BS data structure
        print("Opening %s for parsing" % a["href"])
        f = open(a["href"])
        mo_contents = BeautifulSoup(f.read())
        f.close()
        # Search through all the <dt>'s at the top of the page and
        # see if any of them refer to MO's that this MO extends
        for dt in mo_contents.findAll("dt"):
            # Set the extends key to the name of the MO this MO
            # extends, otherwise set it to None
            if dt.string == "Extends":
                mo["extends"] = str(dt.nextSibling.nextSibling.a.string)
                print("%s extends %s" % (mo["name"], mo["extends"]))
                # No need to process any further <dt> tags
                break
            else:
                mo["extends"] = None

        # Locate the table that contains the properties
        for p in mo_contents.findAll("p", attrs={"class": "table-title"}):
            if p.string == "Properties":
                prop_table = p.nextSibling.nextSibling

        # Collect the properties of this MO in this list
        mo["properties"] = []
        for tr in prop_table.findAll("tr", attrs={"class": ["r0", "r1"]}):
            # Arrgh! Use this kludge to skip over the 
            # "Properties inherited from" rows at the bottom of the table
            if tr.td.attrs[0][1] == u"3":
                continue
            
            # The <td> with the nowrap attribute set to 1 is what we want
            prop_td = tr.findAll("td", attrs={"nowrap": 1})[0]

            # Collect the info about the property in this dict
            property = {}

            property["name"] = str(prop_td.strong.string)
            print("Parsing %s property" % property["name"])

            # If the nextSibling along has a string, it should
            # be a string like xsd:xxxx, in which case there won't
            # be any <a> tag linking somewhere else. In this case
            # we use it as our mo_type otherwise we get the string
            # of the nextSibling's <a> tag as our mo_type
            if prop_td.nextSibling.string is not None:
                mo_type = prop_td.nextSibling.string
            else:
                mo_type = prop_td.nextSibling.a.string

            # If the mo_type starts with this, then it's a
            # MOR, otherwise it's a DataObject, Enum or complexType
            if mo_type.startswith("ManagedObjectReference"):
                property["mor"] = True
            else:
                property["mor"] = False

            # If the mo_type ends with [] then it's a list
            if mo_type.endswith("[]"):
                property["multivalue"] = True
            else:
                property["multivalue"] = False

            # Append this property to the MO's property list
            mo["properties"].append(property)

        # Append this MO to the list of MO's
        unordered_managed_objects.append(mo)
        print("\n")


managed_objects = []
added_mos = []
for mo in unordered_managed_objects:
    print("Looking at %s" % mo["name"])
    # If this MO has already been added (by a dependent MO) then
    # just skip over it here
    if mo["name"] in added_mos:
        print("%s is already added" % mo["name"])
        continue

    # If this MO doesn't extend another or the MO that it extends
    # has already been added to the list, then this MO can be added
    # and report that it has been added
    if mo["extends"] is None or mo["extends"] in added_mos:
        print("MO has no dependencies or dependency %s already added" % mo["extends"])
        managed_objects.append(mo)
        added_mos.append(mo["name"])
        continue

    print("%s has unadded dependency %s" % (mo["name"], mo["extends"]))

    # We have an MO that extends another and the one that it extends
    # hasn't been added yet, so here we must add the extended MO
    for mo2 in unordered_managed_objects:
        print("Seeing if %s is the dependency" % mo2["name"])
        if mo2["name"] == mo["extends"]:
            print("%s is the dependency, seeing if it has a dependency" % mo2["name"])
            if mo2["extends"] is None or mo2["extends"] in added_mos:
                managed_objects.append(mo2)
                added_mos.append(mo2["name"])
                break
            else:
                print("Dependency of dependency not added, adding it")
                for mo3 in unordered_managed_objects:
                    print("Seeing if %s is the dependency" % mo3["name"])
                    if mo3["name"] == mo2["extends"]:
                        print("%s is the dependency" % mo3["name"])
                        if mo3["extends"] is not None and mo3["extends"] not in added_mos:
                            print("ERROR: Uncaptured 3rd level dependency!")
                            exit()
                        managed_objects.append(mo3)
                        added_mos.append(mo3["name"])
                        break

            if mo2["extends"] is None or mo2["extends"] in added_mos:
                managed_objects.append(mo2)
                added_mos.append(mo2["name"])
                break


    # Now that we've added our dependency we can add ourself
    managed_objects.append(mo)
    added_mos.append(mo["name"])

outfile = open("managed_object_graph.yaml", "w")
yaml.dump(managed_objects, outfile)
outfile.close()
