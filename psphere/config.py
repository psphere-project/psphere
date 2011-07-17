"""
Loads configuration, in the following order of preference:
- Command line options
- ~/.psphere/config.yml
- /etc/psphere/config.yml
"""

# Copyright 2010 Jonathan Kinred
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at:
# 
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import logging
import os
import yaml

user_config = "~/.psphere/config.yml"
system_config = "/etc/psphere/config.yml"

def _config_from_args(args):
    """Builds configuration from command line options."""
    # TODO: Actually parse command line arguments
    return {}

def _config_from_file(path):
    """Loads configuration from file.
    
    :param path: The path of the config file to load.
    :type path: str
    :returns: A dictionary containing the configuration values.
    :rtype: dict

    """
    f = open(path)
    config = yaml.safe_load(f)
    return config

def get_config():
    # Load the default configuration values
    config = {"general": {},
               "logging": {"destination": os.path.expanduser("~/.psphere/psphere.log"),
                           "level": "INFO"}}
    # Load configuration from files, if they exist
    if os.path.isfile(system_config):
        system = _config_from_file(system_config) 
        for key in config:
            try:
                config[key] = system[key]
            except KeyError:
                pass

    if os.path.isfile(os.path.expanduser(user_config)):
        user = _config_from_file(os.path.expanduser(user_config))
        for key in config:
            try:
                config[key] = user[key]
            except KeyError:
                pass

    cli = _config_from_args(None)
    for key in config:
        try:
            config[key] = cli[key]
        except KeyError:
            pass

    # Convert the level string to the logging module const
    config["logging"]["level"] = getattr(logging, config["logging"]["level"])

    # TODO: Ensure logging destination is valid
    return config
