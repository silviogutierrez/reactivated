import setuptools
import os

def find_stubs(package):
    stubs = []
    for root, dirs, files in os.walk(package):
        for file in files:
            path = os.path.join(root, file).replace(package + os.sep, '', 1)
            stubs.append(path)
    return {package: stubs}

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="reactivated",
    version="0.0.6",
    author="Silvio Gutierrez",
    author_email="silviogutierrez@gmail.com",
    description="A statically typed framework to create Django sites with a React frontend.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/silviogutierrez/django-react",
    packages=setuptools.find_packages(),
    package_data={
        'reactivated': [
            'conf/mypy.ini',
            'py.typed',
        ],
        **find_stubs('django-stubs'),
        **find_stubs('custom_user-stubs'),
    },
    scripts=[
        'scripts/to-be-renamed.py',
    ],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
