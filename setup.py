#!/usr/bin/env python

"""The setup script."""
from typing import List

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements: List[str] = [ ]

test_requirements = ['pytest>=3', ]

setup(
    author="Nikita Toloknov",
    author_email='4170407@gmail.com',
    python_requires='>=3.9',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="tinkoff_invest_bot",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='tinkoff_invest_bot',
    name='tinkoff_invest_bot',
    packages=find_packages(include=['tinkoff_invest_bot', 'tinkoff_invest_bot.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/amp1re/tinkoff_invest_bot',
    version='0.1.0',
    zip_safe=False,
)
