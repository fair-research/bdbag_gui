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
    url='https://github.com/fair-research/bdbag_gui/',
    maintainer='USC Information Sciences Institute, Informatics Systems Research Division',
    maintainer_email='isrd-support@isi.edu',
    version="1.0.0-beta.1",
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
    install_requires=['bdbag>=1.5.6'],
    extras_require={
        'PyQt5': ["PyQt5>=5.11.3"],
    },
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
        'Programming Language :: Python :: 3.7'
    ]
)

