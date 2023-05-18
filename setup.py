import json

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("packages/reactivated/package.json", "r") as package:
    version = json.load(package)["version"]

setuptools.setup(
    name="reactivated",
    version=version,
    author="Silvio Gutierrez",
    author_email="silviogutierrez@gmail.com",
    description="A statically typed framework to create Django sites with a React frontend.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/silviogutierrez/django-react",
    packages=setuptools.find_packages(),
    package_data={"reactivated": ["py.typed", "templates/**/*"]},
    data_files=[('""', ["packages/reactivated/package.json"])],
    scripts=[],
    install_requires=[
        "requests==2.25.0",
        "requests-unixsocket==0.3.0",
        "mypy>=0.910",
        "simplejson>=3.16.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
