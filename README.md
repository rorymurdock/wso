# WSO-UEM-Py

[![Build Status](https://travis-ci.org/rorymurdock/WSO-UEM-Py.svg?branch=master)](https://travis-ci.org/rorymurdock/WSO-UEM-Py)
[![Maintainability](https://api.codeclimate.com/v1/badges/3be7fc89238b38fc0031/maintainability)](https://codeclimate.com/github/rorymurdock/WSO-UEM-Py/maintainability)
[![Documentation Status](https://readthedocs.org/projects/wso-uem-py/badge/?version=latest)](https://wso-uem-py.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/rorymurdock/WSO-UEM-Py/badge.svg?branch=master)](https://coveralls.io/github/rorymurdock/WSO-UEM-Py?branch=master)
[![Requirements Status](https://requires.io/github/rorymurdock/WSO-UEM-Py/requirements.svg?branch=master)](https://requires.io/github/rorymurdock/WSO-UEM-Py/requirements/?branch=master)

A Python framework for interacting with WSO UEM

Installation:

```shell
python3 -m pip install WSO
```

Usage:

First you'll need to write your credentials:

```shell
python3 configure_args.py
```

Next you can test it:

```python
from WSO.UEM import UEM

print(UEM().system_info())
```
