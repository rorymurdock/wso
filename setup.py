import setuptools

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

setuptools.setup(
    name="wso",
    version="1.0.3",
    author="Rory Murdock",
    author_email="rory@itmatic.com.au",
    description="A Library for interacting with WSO UEM",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/rorymurdock/wso",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=['reqrest', 'basic_auth'],
)
