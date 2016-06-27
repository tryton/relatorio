import os
import re
import codecs
from setuptools import setup, find_packages

def read(fname):
    return codecs.open(
        os.path.join(os.path.dirname(__file__), fname), 'r', 'utf-8').read()


def get_version():
    init = open(os.path.join(os.path.dirname(__file__), 'relatorio',
                             '__init__.py')).read()
    return re.search(r"""__version__ = '([0-9.]*)'""", init).group(1)

setup(
    name="relatorio",
    url="http://relatorio.tryton.org/",
    author="Nicolas Evrard",
    author_email="nicolas.evrard@b2ck.com",
    maintainer="Cedric Krier",
    maintainer_email="cedric.krier@b2ck.com",
    description="A templating library able to output odt and pdf files",
    long_description=read('README'),
    license="GPL License",
    version=get_version(),
    packages=find_packages(exclude=['examples']),
    package_data={
        'relatorio.tests': ['*.jpg', '*.odt', '*.png', 'templates/*.tmpl'],
        },
    install_requires=[
        "Genshi >= 0.5",
        "lxml >= 2.0"
    ],
    extras_require={
        'chart': ['pycha >= 0.4.0', 'pyyaml'],  # pycairo
        },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing",
    ],
    test_suite="relatorio.tests",
    use_2to3=True)
