# EmBody protocol codec

This is a Python based implementation library for the EmBody/HyperSension communication protocol.

# Installing package with pip from github

This package is not distributed to PyPi as a regular open source Python package. 

To use this package in other projects, install it from its Github repository, either from the command line:

```
pip install "git+https://github.com/aidee-health/embody-protocol-codec@main#egg=embodycodec" 
```

Or you can add it to your `requirements.txt` (just the URL to the repository):
```
git+https://github.com/aidee-health/embody-protocol-codec@main#egg=embodycodec
```

Then, run `pip install -r requirements.txt`

:warning: **Note!** This installs the latest version from master. You can also use any tag, commit id or git ref like
this:

```
git+https://github.com/aidee-health/embody-protocol-codec@v0.0.1#egg=embodycodec
git+https://github.com/aidee-health/embody-protocol-codec@da39a3ee5e6b4b0d325ef95601890afd80709#egg=embodycodec
git+https://github.com/aidee-health/embody-protocol-codec@refs/pull/123/head#egg=embodycodec
```

# Resources

* [Python Package tutorial](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
* [Struct documentation with pack/unpack and format options](https://docs.python.org/3/library/struct.html)
* [Best practices for project structure according to pytest](https://docs.pytest.org/en/latest/explanation/goodpractices.html)
* [Using GitHub as a private PiPI server](https://medium.com/network-letters/using-github-as-a-private-python-package-index-server-798a6e1cfdef)