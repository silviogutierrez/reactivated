#!/usr/bin/env python
import sys
import os

import reactivated

module_directory = os.path.dirname(reactivated.__file__)
conf_directory = os.path.join(module_directory, 'conf')

mypy = os.path.join(conf_directory, 'mypy.ini')
tsconfig = os.path.join(conf_directory, 'tsconfig.json')

def create_symlink(path: str, name: str) -> None:
    if os.path.isfile(name):
        os.remove(name)
    os.symlink(path, name)


create_symlink(mypy, 'mypy.ini')
create_symlink(mypy, 'mypy.ini')
