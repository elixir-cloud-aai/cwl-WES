"""Package setup."""

from pathlib import Path
from setuptools import setup, find_packages

root_dir = Path(__file__).parent.resolve()

with open(root_dir / "cwl_wes" / "version.py", encoding="utf-8") as _file:
    exec(_file.read())  # pylint: disable=exec-used

with open(root_dir / "README.md", encoding="utf-8") as _file:
    LONG_DESCRIPTION = _file.read()

with open(root_dir / "requirements.txt", encoding="utf-8") as _file:
    INSTALL_REQUIRES = _file.read().splitlines()

setup(
    name="cwl-wes",
    version=__version__,  # noqa: F821  # pylint: disable=undefined-variable
    author="Elixir Cloud & AAI",
    author_email="alexander.kanitz@alumni.ethz.ch",
    description="Flask- and MongoDB-powered GA4GH WES server",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    license="Apache License 2.0",
    url="https://github.com/elixir-cloud-aai/cwl-WES.git",
    packages=find_packages(),
    keywords=(
        "ga4gh wes workflow elixir rest restful api app server openapi "
        "swagger mongodb python flask"
    ),
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.7",
    ],
    install_requires=INSTALL_REQUIRES,
)
