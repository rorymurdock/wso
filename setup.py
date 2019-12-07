import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="wso",
    version="1.0.0",
    author="Rory Murdock",
    author_email="rory@itmatic.com.au",
    description="A Library for interacting with WSO UEM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rorymurdock/wso",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
          'reqrest'
    ],
)