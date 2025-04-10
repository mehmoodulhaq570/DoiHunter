<<<<<<< HEAD
# setup.py
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='doi_hunter',
    version='0.1.0',
    description='A Python tool for downloading scientific papers using Crossref, and SciHub.',
    author='Mehmood Ul Haq',
    author_email='mehmoodulhaq1040@gmail.com',
    url='https://github.com/mehmoodulhaq570/doi_hunter',  # Optional, if hosted on GitHub
    packages=find_packages(),  # Automatically find and include all packages in the directory
    install_requires=[
        'requests',
        'beautifulsoup4'
    ],
    entry_points={
        'console_scripts': ['doi_hunter=doi_hunter.__main__:main'],
    },
    python_requires='>=3.6',  # Specify the minimum Python version required
)
=======
# setup.py
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='doi_hunter',
    version='0.1.1',
    description='A Python tool for downloading scientific papers using Crossref, and SciHub.',
    author='Mehmood Ul Haq',
    author_email='mehmoodulhaq1040@gmail.com',
    url='https://github.com/mehmoodulhaq570/doi_hunter',  # Optional, if hosted on GitHub
    packages=find_packages(),  # Automatically find and include all packages in the directory
    install_requires=[
        'requests',
        'beautifulsoup4'
    ],
    entry_points={
        'console_scripts': ['doi_hunter=doi_hunter.__main__:main'],
    },
    python_requires='>=3.6',  # Specify the minimum Python version required
)
>>>>>>> 23ac95e (Updated the version to the)
