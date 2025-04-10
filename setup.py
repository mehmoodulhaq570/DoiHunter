from setuptools import setup, find_packages

# Read the README file for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="doi_hunter",  # Name of the package
    version="0.1.3",  # Version of the package
    author="Mehmood Ul Haq",  # Author name
    author_email="mehmoodulhaq1040@gmail.com",  # Author email
    description="A Python tool for downloading scientific papers using Crossref and SciHub",  # Short description
    long_description=long_description,  # Long description from README.md
    long_description_content_type="text/markdown",  # Markdown format for long description
    url="https://github.com/mehmoodulhaq570/DoiHunter",  # URL to the project
    project_urls={
        "Documentation": "https://github.com/mehmoodulhaq570/DoiHunter#readme",
        "Source": "https://github.com/mehmoodulhaq570/DoiHunter",
        "Bug Tracker": "https://github.com/mehmoodulhaq570/DoiHunter/issues",
    },
    packages=find_packages(),  # Automatically find all packages
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',  # Minimum required Python version
    install_requires=[
        "requests>=2.25.1",
        "beautifulsoup4>=4.9.3"
    ],
    entry_points={
        'console_scripts': [
            'doi-hunter=doi_hunter.__main__:main',  # CLI command
        ],
    },
    include_package_data=True,  # Include additional files from MANIFEST.in
    license="MIT",  # License type
)
