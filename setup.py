from setuptools import setup

import imp

_version = imp.load_source("htmltools._version", "htmltools/_version.py")

setup(
    name="htmltools",
    version=_version.__version__,
    author="Carson Sievert",
    author_email="carson@rstudio.com",
    license="MIT",
    url="https://github.com/rstudio/htmltools",
    description="Tools for HTML generation and output.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="html python",
    python_requires=">=3.5",
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
    packages=["htmltools"],
    package_data={
        "htmltools": ["py.typed"],
    },
    include_package_data=True,
)
