#
# Copyright 2017 University of Southern California
# Distributed under the GNU GPL 3.0 license. See LICENSE for more info.
#

""" Installation script for the bdbag_gui utility.
"""

from setuptools import setup, find_packages

setup(
    name="bdbag_gui",
    description="Graphical User Interface for BDBag Utility",
    url='https://github.com/ini-bdds/bdbag_gui/',
    maintainer='USC Information Sciences Institute, Informatics Systems Research Division',
    maintainer_email='isrd-support@isi.edu',
    version="0.2.3",
    packages=find_packages(),
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
    install_requires=['bdbag>=1.1.3'],
    license='GNU GPL 3.0',
    classifiers=[
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ]
)

