#!/usr/bin/python
from BeautifulSoup import BeautifulSoup
import yaml

f = open("index-mo_types.html")
contents = f.read()
f.close()
soup = BeautifulSoup(contents)
mo_divs = soup.findAll(name="div", attrs={"id": ["AE", "FJ", "KO", "PT", "UZ"]})
managed_objects = []
for div in mo_divs:
    for a in div.findAll("a"):
        print("Generating information for %s" % a.string)
        mo = {}
        mo["name"] = str(a.string)
        print("Opening %s" % a["href"])
        f = open(a["href"])
        mo_contents = BeautifulSoup(f.read())
        f.close()
        for dt in mo_contents.findAll("dt"):
            if dt.string == "Extends":
                mo["extends"] = str(dt.nextSibling.nextSibling.a.string)
                print("%s extends %s" % (mo["name"], mo["extends"]))
                break
            else:
                mo["extends"] = None

        for p in mo_contents.findAll("p", attrs={"class": "table-title"}):
            if p.string == "Properties":
                prop_table = p.nextSibling.nextSibling

        mo["properties"] = []
        for tr in prop_table.findAll("tr", attrs={"class": ["r0", "r1"]}):
            if tr.td.attrs[0][1] == u"3":
                continue
            
            tds = tr.findAll("td", attrs={"nowrap": 1})
            property = {}
            property["name"] = str(tds[0].strong.string)
            print("Parsing %s property" % property["name"])
            if tds[0].nextSibling.string is not None:
                mo_type = tds[0].nextSibling.string
            else:
                mo_type = tds[0].nextSibling.a.string

            if mo_type.startswith("ManagedObjectReference"):
                property["mor"] = True
            else:
                property["mor"] = False

            if mo_type.endswith("[]"):
                property["multivalue"] = True
            else:
                property["multivalue"] = False

            mo["properties"].append(property)

        managed_objects.append(mo)
    print("\n")

outfile = open("output.yaml", "w")
yaml.dump(managed_objects, outfile)
outfile.close()
