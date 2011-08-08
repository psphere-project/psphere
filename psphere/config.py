import os
import sys
import yaml

PSPHERE_CONFIG = yaml.load(file(os.path.expanduser('~/.psphere/config.yml'),
                                "r"))
def _config_value(section, name, default):
    if name in PSPHERE_CONFIG[section]:
        file_value = PSPHERE_CONFIG[section][name]

    if default is None and file_value is None:
        print("You must set a %s" % name)
        sys.exit(1)

    if file_value:
        return file_value
    else:
        return default
