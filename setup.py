import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="django_react",
    version="0.0.2",
    author="Silvio Gutierrez",
    author_email="silviogutierrez@gmail.com",
    description="A statically typed framework to create Django sites with a React frontend.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/silviogutierrez/django-react",
    packages=setuptools.find_packages(),
    package_data={
        'django_react': [
            'conf/mypy.ini',
            'py.typed',
        ],
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
