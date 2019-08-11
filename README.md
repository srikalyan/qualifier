# qualifier

[![Build Status](https://travis-ci.org/srikalyan/qualifier.svg?branch=master)](https://travis-ci.org/srikalyan/qualifier)

## Description:
A simple python project used for updating the qualifier part of the version for python projects.

## Expectation:
This project expects setup.py of this format

```python
from setuptools import setup

__QUALIFIER__ = ""

setup(
    name="qualifier",
    version="1.0.0" + __QUALIFIER__,
    ...)
```

On running the command `update_qualifier` which is provided on installing this project as shell command,
`__QUALIFIER__` would be update based the rules.

## Rules:

1. If the HEAD is tagged and the branch is master then `__QUALIFIER__` will not be updated
2. If the HEAD is not tagged and the branch is master then `__QUALIFIER__` will be updated to `rc<epoch>`
3. If the HEAD is not tagged and the branch is not master then `__QUALIFIER__` will be updated to `.dev<epoch>`  
