#!/usr/bin/env python

from setuptools import setup, find_packages
import sys
import wp2md

sys.path.insert(0, '.')
sys.path.insert(0, 'lib')

setup(
    name=wp2md.__name__,
    description=wp2md.__doc__,
    version=wp2md.__version__,
    license=wp2md.__license__,
    author=wp2md.__author__,
    author_email=wp2md.__email__,
    url=wp2md.__url__,
    long_description=open('README.md').read(),
    platforms=['any'],
    packages=find_packages(),
    py_modules=['wp2md'],
    install_requires=['markdown', 'html2text'],
    entry_points={'console_scripts': ['wp2md = wp2md:main']},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
       'Development Status :: 5 - Production/Stable',
       'Intended Audience :: Developers',
       'License :: OSI Approved :: GNU General Public License (GPL)',
       'Programming Language :: Python',
       'Programming Language :: Python :: 2.7',
       # TODO: Test and add other versions
    ],
    dependency_links=[
        'https://github.com/aaronsw/html2text/tarball/master#egg=html2text'
    ],
)
