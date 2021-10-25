#
# Copyright 2017 University of Southern California
# Distributed under the GNU GPL 3.0 license. See LICENSE for more info.
#

""" Installation script for the bdbag_gui utility.
"""
import io
import re
from setuptools import setup, find_packages

__version__ = re.search(
    r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
    io.open('bdbag_gui/__init__.py', encoding='utf_8_sig').read()
    ).group(1)

setup(
    name="bdbag_gui",
    description="Graphical User Interface for BDBag Utility",
    url='https://github.com/fair-research/bdbag_gui/',
    maintainer='USC Information Sciences Institute, Informatics Systems Research Division',
    maintainer_email='isrd-support@isi.edu',
    version=__version__,
    packages=find_packages(),
    package_data={'bdbag_gui': ['images/bag.ico', 'images/bag.icns', 'images/bag.png']},
    entry_points={
        'gui_scripts': [
            'bdbag-gui = bdbag_gui.__main__:main',
        ]
    },
    requires=[
        'os',
        'sys',
        'logging',
        'PyQt5'],
    install_requires=[
        'bdbag[boto,globus]>=1.6.0',
        'PyQt5'],
    license='GNU GPL 3.0',
    classifiers=[
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ]
)

