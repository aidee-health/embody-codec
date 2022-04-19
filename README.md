# EmBody protocol codec

This is a Python based implementation library for the EmBody/HyperSension communication protocol.

# Installing package with pip

This package is not distributed to PyPi as a regular open source Python package. To use this package in other
projects, install it from the file system as described in the 
[Pip Documentation](https://pip.pypa.io/en/latest/cli/pip_install/).

Example:
```
pip install --no-index --find-links=/local/dir/embody-protocol-codec embodycodec 
```

You can also create a separate requirements-local.txt for instance, to accomplish the same with requirements. 

requirements-local.txt:
```
--no-index
--find-links=/local/dir/embody-protocol-codec

embodycodec >= 0.0.1
```

Then you can reference this from your requirements.txt file with `-r requirements-local.txt` on a separate line.

# Resources

* [Python Package tutorial](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
* [Struct documentation with pack/unpack and format options](https://docs.python.org/3/library/struct.html)
* [Best practices for project structure according to pytest](https://docs.pytest.org/en/latest/explanation/goodpractices.html)