import os
import sys
import yaml

config_path = os.path.expanduser('~/.psphere/config.yml')
try:
    config_file = open(config_path, "r")
except IOError:
    print("Configuration file could not be opened, perhaps you"
          " haven't created one?")
    pass

PSPHERE_CONFIG = yaml.load(config_file)
config_file.close()

def _config_value(section, name, default=None):
    if name in PSPHERE_CONFIG[section]:
        file_value = PSPHERE_CONFIG[section][name]

    if default is None and file_value is None:
        print("You must set a %s" % name)
        sys.exit(1)

    if file_value:
        return file_value
    else:
        return default
