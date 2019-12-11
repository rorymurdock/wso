# wso

[![Build Status](https://github.com/rorymurdock/wso/workflows/Pytest/badge.svg)](https://github.com/rorymurdock/wso/actions)
[![Maintainability](https://api.codeclimate.com/v1/badges/3be7fc89238b38fc0031/maintainability)](https://codeclimate.com/github/rorymurdock/wso/maintainability)
[![Documentation Status](https://readthedocs.org/projects/wso/badge/?version=latest)](https://wso.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/rorymurdock/wso/badge.svg?branch=master)](https://coveralls.io/github/rorymurdock/wso?branch=master)
[![Requirements Status](https://requires.io/github/rorymurdock/wso/requirements.svg?branch=master)](https://requires.io/github/rorymurdock/wso/requirements/?branch=master)

A package for working with VMWare Workspace ONE UEM

## Purpose

Provides a Python interface for WSO UEM

## Usage

Getting started is easy, first install the package using `pip install wso` next open an interactive python shell `python3`

```python
from wso import WSO
```

```python
WSO()
```

This will start interactive config mode where you will be asked for the URL, username, password, tentant code

Once you have setup your config you can query UEM for information. Check the examples directory for some examples of what you can do.

```python
WSO().system_info()
```
