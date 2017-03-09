from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='monitort',

    version='1.0.0a1',

    description='Asyncio tcp monitor',
    long_description=long_description,

    url='https://github.com/teddybear/monitort',

    author='Alexey Ismailov',
    author_email='aismailov@ya.ru',

    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Systems Administration',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='hr test monitor tcp asyncio',

    py_modules=["monitort"],

    install_requires=["aiohttp", "motor"],


    entry_points={
        'console_scripts': [
            'monitort-rest=monitort.rest:main',
            'monitort-checker=monitort.checker:main',
        ],
    },
)
