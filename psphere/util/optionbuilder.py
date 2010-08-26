#!/usr/bin/env python
"""
Parse command line options, allow users to append their own options and
read predefined configuration from the users .visdkrc file.
"""

import os, optparse

class OptionBuilder(object):
    def __init__(self):
        self.required_opts = []
        # The vars that are valid in the .visdkrc file
        self.config_vars = ['url', 'username', 'password']
        # The file in which to find configurable vars
        self.visdkrc = os.path.expanduser('~/.visdkrc')

        usage = ('usage: %prog --url https://<host>/sdk --username <username> '
                 '--password <password>')
        self.parser = optparse.OptionParser(usage)
        self.parser.add_option('--url', dest='url',
                               help='the url of the vSphere server')
        self.parser.add_option('--username', dest='username',
                               help='the username to connnect with')
        self.parser.add_option('--password', dest='password',
                               help='the password to connect with')

        self.required_opts.append('url')
        self.required_opts.append('username')
        self.required_opts.append('password')

    def read_visdk(self):
        # Read the visdkrc file, use values that are in there or append
        pass

    def add_option(self, opt, dest, help, required):
        self.parser.add_option(opt, dest=dest, help=help)
        # TODO: Append to usage
        # Add to the list of required options which we'll use later
        if required:
            self.required_opts.append(dest)

    def get_options(self):
        """Get the options that have been set.

        Called after the user has added all their own options
        and is ready to use the variables.

        """
        (options, args) = self.parser.parse_args()

        # Set values from .visdkrc, but only if they haven't already been set
        visdkrc_opts = self.read_visdkrc()
        for opt in self.config_vars:
            if not getattr(options, opt):
                # Try and use value from visdkrc
                if opt in visdkrc_opts:
                    setattr(options, opt, visdkrc_opts[opt])

        # Ensure all the required options are set
        for opt in self.required_opts:
            if opt not in dir(options) or getattr(options, opt) == None:
                self.parser.error('%s must be set!' % opt)

        return options

    def read_visdkrc(self):
        try:
            config = open(self.visdkrc)
        except IOError, e:
            if e.errno == 2:
                # Doesn't exist, ignore it
                pass
            elif e.errno == 13:
                print('Permission denied opening %s' % self.visdkrc)
            else:
                print('Could not open %s: %s' % (self.visdkrc, e.strerror))

        lines = config.readlines()
        config.close()

        parsed_opts = {}
        for line in lines:
            (key, value) = line.split('=')
            parsed_opts[key] = value.rstrip('\n')

        visdkrc_opts = {}
        if('VI_PROTOCOL' in parsed_opts and 'VI_SERVER' in parsed_opts and
           'VI_SERVICEPATH' in parsed_opts):
            visdkrc_opts['url'] = '%s://%s%s' % (parsed_opts['VI_PROTOCOL'],
                                               parsed_opts['VI_SERVER'],
                                               parsed_opts['VI_SERVICEPATH'])
        if 'VI_USERNAME' in parsed_opts:
            visdkrc_opts['username'] = parsed_opts['VI_USERNAME']

        if 'VI_PASSWORD' in parsed_opts:
            visdkrc_opts['password'] = parsed_opts['VI_PASSWORD']

        return visdkrc_opts
