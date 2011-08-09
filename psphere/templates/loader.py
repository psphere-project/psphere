import glob
import os
import yaml

from psphere import config
from psphere.errors import TemplateNotFoundError

template_path = os.path.expanduser(config._config_value("general",
                                                        "template_dir"))

def merge(first, second):
    """Merge a list of templates.
    
    The templates will be merged with values in higher templates
    taking precedence.

    :param templates: The templates to merge.
    :type templates: list

    """
    return dict(first.items() + second.items())

def load(name=None):
    """Loads a template of the specified name.

    Templates are placed in the <template_dir> directory in YAML format with
    a .yaml extension.

    If no name is specified then the function will return the default
    template (<template_dir>/default.yaml) if it exists.
    
    :param name: The name of the template to load.
    :type name: str (default: default)

    """
    if name is None:
        name = "default"

    print("Loading template with name %s" % name)
    try:
        template_file = open("%s/%s.yaml" % (template_path, name))
    except IOError:
        raise TemplateNotFoundError

    template = yaml.safe_load(template_file)
    template_file.close()
    if "extends" in template:
        print("Merging %s with %s" % (name, template["extends"]))
        template = merge(load(template["extends"]), template)

    return template


def complex_load(name="default"):
    """Loads a template of the specified name.

    Templates are placed in the <template_dir> directory in YAML format with
    a .yaml extension.

    If no name is specified then the function will return the default
    template (<template_dir>/default.yaml) if it exists.
    
    :param name: The name of the template to load.
    :type name: str (default: default)

    """
    try:
        default_file = open("%s/default.yaml" % template_path)
    except IOError:
        # Don't worry if the default template doesn't exist
        pass

    default_template = yaml.safe_load(default_file)
    default_file.close()

    templates = []
    templates.append(default_template)

    try:
        template_file = open("%s/%s.yaml" % (template_path, name))
    except IOError:
        raise TemplateNotFoundError

    template = yaml.safe_load(template_file)
    template_file.close()
    # TODO: Some work to combine the templates

    return template


def list_templates():
    """Returns a list of all templates."""
    templates = [f for f in glob.glob(os.path.join(template_path, '*.yaml'))]
    return templates
