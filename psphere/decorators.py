# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# he Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

class ReadOnlyCachedAttribute(object):
    """Retrieves attribute value from server and caches it in the instance.
    Source: Python Cookbook
    Author: Denis Otkidach http://stackoverflow.com/users/168352/denis-otkidach
    This decorator allows you to create a property which can be computed once
    and accessed many times.
    """
    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__
        self.__doc__ = method.__doc__

    def __get__(self, inst, cls):
        # If we're being accessed from the class itself, not from an object
        if inst is None:
            print("inst is None")
            return self
        # Else if the attribute already exists, return the existing value
        elif self.name in inst.__dict__:
            print("Using cached value for %s" % self.name)
            return inst.__dict__[self.name]
        # Else, calculate the desired value and set it
        else:
            print("Retrieving and caching value for %s" % self.name)
            # TODO: Check if it's an array or a single value
            result = self.method(inst)
            # Set the object value to desired value
            inst.__dict__[self.name] = result
            return result

    def __set__(self, inst, value):
        raise AttributeError("%s is read-only" % self.name)

    def __delete__(self, inst):
        del inst.__dict__[self.name]
