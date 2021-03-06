#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

#with open('requirements.txt') as requirements_file:
#    requirements = [line for line in requirements_file]

requirements = [
    'Click>=6.0',
    'pyserial>=3.0',
    'easy_vector>=0.1.0',
    'gamepad>=0.1.1',
    'grbl-link>=0.1.4',
]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Darius Montez",
    author_email='darius.montez@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    description="Jog your GRBL-based CNC machines with a gamepad controller.",
    entry_points={
        'console_scripts': [
            'grbl_gamepad=grbl_gamepad.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='grbl_gamepad',
    name='grbl_gamepad',
    packages=find_packages(include=['grbl_gamepad']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/DariusMontez/grbl_gamepad',
    version='0.3.0',
    zip_safe=False,
)
