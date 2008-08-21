# -*- encoding: utf-8 -*-
import relatorio
from setuptools import setup, find_packages

setup(
    name="relatorio",
    url="http://relatorio.openhex.org",
    author="Nicolas Evrard",
    author_email="nicoe@openhex.org",
    description="A templating library able to output odt and pdf files",
    long_description="""
relatorio
========

A templating library which provides a way to easily output odt and pdf file.

relatorio also provides a report repository allowing you to link python objects
and report together, find reports by mimetypes/name/pyhon objects.
""",
    license="GPL License",
    version=relatorio.__version__,
    packages=find_packages(exclude=['relatorio.tests', 'examples']),
    install_requires=[
        "Genshi >= 0.5",
        "lxml >= 2.0.0"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing",
    ],
    test_suite="nose.collector",
    entry_points={
        "relatorio.templates.engines": [
            "oo.org = relatorio.templates.opendocument:Template",
            "pdf = relatorio.templates.pdf:Template",
            "text = genshi.template:TextTemplate",
            "xml = genshi.template:MarkupTemplate",
        ],
    })
