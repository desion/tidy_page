#!/usr/bin/env python
from __future__ import print_function
from setuptools import setup, find_packages
import sys

lxml_requirement = "lxml"
if sys.platform == 'darwin':
    import platform
    mac_ver = platform.mac_ver()[0]
    mac_ver_no = int(mac_ver.split('.')[1])
    if mac_ver_no < 9:
        print("Using lxml<2.4")
        lxml_requirement = "lxml<2.4"

setup(
    name="tidy-page",
    version="0.1.0",
    author="Desion Wang",
    author_email="wdxin1322@qq.com",
    description="html text parser,get the content form html page",
    long_description=open("README.rst").read(),
    license="MIT",
    url="https://github.com/desion/tidy_page",
    packages=['tidypage'],
    install_requires=[
        "beautifulsoup4",
        lxml_requirement
        ],
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Text Processing :: Indexing",
        "Topic :: Utilities",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
    ],
)
