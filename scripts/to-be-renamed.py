#!/usr/bin/env python
import sys
import os

import django_react

module_directory = os.path.dirname(django_react.__file__)
conf_directory = os.path.join(module_directory, 'conf')
mypy = os.path.join(conf_directory, 'mypy.ini')

os.symlink(mypy, 'mypy.ini')
