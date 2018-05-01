"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""
import codecs
from os import path
from setuptools import setup, find_packages

from clac import __version__ as vr

__here__ = path.abspath(path.dirname(__file__))

with codecs.open(path.join(__here__, 'README.md'), encoding='utf-8') as f:
    __long_description__ = f.read()

setup(
    name='clac',
    version=vr.__version__,
    description='CLAC Layerizes Application Configuration',
    long_description=__long_description__,
    url='https://github.com/iamtheauthor/clac',
    author='Wesley Van Melle',
    author_email='van.melle.wes@gmail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Configuration',
    ],
    keywords='configuration environment',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=[],
    extras_require={
        'test': ['pytest'],
    },
    zip_safe=False,
)
