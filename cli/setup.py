#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Spotify AB

import codecs
import os
import re

from setuptools import find_packages
from setuptools import setup


HERE = os.path.abspath(os.path.dirname(__file__))


#####
# Helper functions
#####
def read(*filenames, **kwargs):
    """
    Build an absolute path from ``*filenames``, and  return contents of
    resulting file.  Defaults to UTF-8 encoding.
    """
    encoding = kwargs.get("encoding", "utf-8")
    sep = kwargs.get("sep", "\n")
    buf = []
    for fl in filenames:
        with codecs.open(os.path.join(HERE, fl), "rb", encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


def find_meta(meta):
    """Extract __*meta*__ from META_FILE."""
    re_str = r"^__{meta}__ = ['\"]([^'\"]*)['\"]".format(meta=meta)
    meta_match = re.search(re_str, META_FILE, re.M)
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError("Unable to find __{meta}__ string.".format(meta=meta))


#####
# Project-specific constants
#####
NAME = "klio-cli"
PACKAGE_NAME = "klio_cli"
PACKAGES = find_packages(where="src")
META_PATH = os.path.join("src", PACKAGE_NAME, "__init__.py")
CLASSIFIERS = [
    "Development Status :: 1 - Planning",
    "Natural Language :: English",
    "Operating System :: POSIX :: Linux",
    "Operating System :: MacOS :: MacOS X",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: Implementation :: CPython",
]
META_FILE = read(META_PATH)
INSTALL_REQUIRES = [
    "click",
    "dateparser",
    "docker",
    "emoji",
    "jinja2",
    "glom",
    "google-api-core",
    "google-api-python-client",
    "google-cloud-monitoring",
    # API breaking change w google-api-core
    "google-cloud-pubsub<=1.4.0",
    "google-cloud-storage",
    # API breaking change w google-cloud-monitoring
    "googleapis-common-protos<1.50.0",
    "klio-core",
    "protobuf",
    "pyyaml",
    "setuptools",
]
EXTRAS_REQUIRE = {
    "docs": ["sphinx", "interrogate"],
    "tests": [
        "coverage",
        "mock",  # for py2 - remove when dropping support
        "pytest>=4.3.0",  # 4.3.0 dropped last use of `convert`
        "pytest-cov",
        "pytest-mock",
    ],
}
EXTRAS_REQUIRE["dev"] = (
    EXTRAS_REQUIRE["docs"]
    + EXTRAS_REQUIRE["tests"]
    + ["klio-devtools", "bumpversion", "wheel"]
)

setup(
    name=NAME,
    version=find_meta("version"),
    description=find_meta("description"),
    url=find_meta("uri"),
    author=find_meta("author"),
    author_email=find_meta("email"),
    maintainer=find_meta("author"),
    maintainer_email=find_meta("email"),
    packages=PACKAGES,
    package_dir={"": "src"},
    include_package_data=True,
    classifiers=CLASSIFIERS,
    zip_safe=False,
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    entry_points={"console_scripts": ["klio = klio_cli.cli:main"]},
)