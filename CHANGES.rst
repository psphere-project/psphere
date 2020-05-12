0.6.0 (2020-05-12)
------------------

- Upgrade setup.py to setup.cfg


0.6.0a1 (2019-03-26)
--------------------

- use maintained suds-community


0.6.0a (2019-02-18)
-------------------

- support HTTPS by passing an ssl.SSLContext
- use more secure suds-jurko
- use `except Exception as e` syntax
- switch to zest.releaser

Version 0.5.2
-------------

(bugfix release, released on April 5th 2013)

- Add an example showing how to list VMs on a host
- Add a new example of powering on many VMs at once
- Fix regression that calls _init_logging() and remove the function for good.
- Update references from bitbucket to github
- Merge bitbucket pull request: Pierre-Yves D Fixed error when setting extraOptions on VM creation
- Merge bitbucket pull request: Saju M 3cbdf636d068 Adding example get_filesize_by_path
- MANIFEST.in: s/README/README.rst
- Updated managed objects to include new objects in sphere 5.0
- When pre-loading objects, don't try and pre-load them when the requested attributed contains an empty list. fixes #7
- Replace print calls with logging calls. fixes issue 8
- Remove use of sys.exit and raise exceptions instead. fixes issue 8
- Use `*args` to pass log strings (efficiency, as log mesages won't be string formatted unless they're actually logged). Remove _init_logging to mak
- Convert Windows path to WSDL file to URI format
- Documentation updates

Version 0.5.1
-------------

(bugfix release, released on August 19th 2011)

Version 0.5.0
-------------

(major release, released on August 11th 2011)

- The API has completely changed, programs written for 0.1.4 will not work in
  0.5.0 or later versions.
- Implements vSphere SDK 4.1
- All vSphere Managed Object's are implemented including all properties.
- Object properties are now lazily loaded on first access and cached for
  5 minutes.

Version 0.1.4
-------------

Released on July 15th 2011

- Primitive release of psphere for Aeolus Project to package into Fedora.
