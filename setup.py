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

doc_requires = ['sphinx', 'sphinx_rtd_theme']
test_requires = ['pytest', 'pytest-cov']
coverage_requires = ['coverage', 'codecov']
lint_requires = ['pylint', 'mypy']
pkg_requires = ['twine', 'wheel']

setup(
    name='clac',
    version=vr.__release__,
    description='CLAC Layerizes Application Configuration',
    long_description=__long_description__,
    long_description_content_type='text/markdown',
    url='https://github.com/scruffystuffs/clac',
    author='Wesley Van Melle',
    author_email='van.melle.wes@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries',
    ],
    keywords='configuration environment',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    python_requires='~=3.6',
    install_requires=[],
    extras_require={
        'fulldev': test_requires + doc_requires + lint_requires + coverage_requires,
        'test': test_requires,
        'docs': doc_requires,
        'lint': lint_requires,
        'cov': coverage_requires,
        'pkg': pkg_requires,
    },
    zip_safe=False,
)
