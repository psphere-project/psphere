import yaml

managed_objects = yaml.safe_load(open("managed_object_graph.yaml"))
header_text = "from psphere import ManagedObject, cached_property\n\n"

footer_text = "classmap = dict((x.__name__, x) for x in (\n"

# Basic text to import these base classes from psphere

body_text = ""
for i, mo in enumerate(managed_objects):
    if mo["extends"] is None:
        mo["extends"] = "ManagedObject"

    body_text += "class %s(%s):\n" % (mo["name"], mo["extends"])
    props = []
    for prop in mo["properties"]:
        props.append("%s" % prop["name"])
    body_text += "    _valid_attrs = set(%s)\n" % props
    body_text += "    def __init__(self, mo_ref, client):\n"
    body_text += "        %s.__init__(self, mo_ref, client)\n" % (mo["extends"])
    body_text += ("        self._valid_attrs = set.union(self._valid_attrs, %s._valid_attrs)\n" % mo["extends"])
    for prop in mo["properties"]:
        body_text += "    @cached_property\n"
        body_text += "    def %s(self):\n" % prop["name"]
        if prop["mor"] is True:
            body_text += ("       return self._get_mor(\"%s\", %s)\n" %
                     (prop["name"], prop["multivalue"]))
        else:
            body_text += ("       return self._get_dataobject(\"%s\", %s)\n" %
                     (prop["name"], prop["multivalue"]))

    body_text += "\n\n"

    footer_text += "    %s" % mo["name"]
    # Put a comma at the end of every line but the last
    if i < (len(managed_objects) - 1):
        footer_text += ",\n"
    else:
        footer_text += "\n"

footer_text += "))\n"
footer_text += "def classmapper(name):\n"
footer_text += "    return classmap[name]"

f = open("output.py", "w")
f.write(header_text)
f.write(body_text)
f.write(footer_text)
f.close()
