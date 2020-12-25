#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup


setup(
    name='fafav_downloader',
    version='1.0.1',
    license='GNU General Public License',
    description='Download FA favorites by username',
    author='Preocts',
    author_email='preocts@preocts.com',
    url='https://github.com/Preocts/fafav_downloader',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'requests',
        'progress'
    ],
    entry_points={
        'console_scripts': [
            'fadownload=fafavs.main:main',
            "fafix=fafavs.fix_extentions:main",
        ]
    },
    include_package_data=False
)
