"""
iodized's grinder.

A simple daemon to convert iodized's json to salt states.

Currently supported commands are:
  salt_states: List all salt states
  salt_version: Print out salt's version

Usage:
  grinder (salt_states|salt_version)
"""
import inspect
import salt
from docopt import docopt


def get_salt_states():
    """
    Return a tuple of salt state and state parameters
    """
    l = salt.loader._create_loader({"extension_modules": ""},
                                   'modules',
                                   'module')
    return sorted([(k, inspect.getargspec(v).args) for k, v
                   in l.gen_functions().items()], key=lambda i: i[0])


def main():
    arguments = docopt(__doc__, version='grinder 0.0.1')
    if arguments["salt_states"]:
        for state, parameters in get_salt_states():
            print "%s: %s" % (state, parameters)
    elif arguments["salt_version"]:
        print "salt version is", salt.__version__
    else:
        pass
