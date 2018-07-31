![Gaffer Logo](resources/GafferLogo.svg)

# Gaffer #

Gaffer is an open source application framework designed for creating tools for use in VFX production. It builds on top of the Cortex libraries, adding a flexible node-based computation framework and a user interface framework for editing and viewing node graphs. Gaffer ships with a number of sample modules and applications, not least of which is a module for the on-demand generation of procedural scenes for rendering.

More information can be found on the [Gaffer homepage](https://gafferhq.org).

Developer notes are available on the [Gaffer developer wiki](https://github.com/GafferHQ/gaffer/wiki).

Participating in the Gaffer community requires abiding by the project's [Code of Conduct](https://github.com/GafferHQ/gaffer/blob/master/CODE_OF_CONDUCT.md).


## Download ##

Compiled binary releases are available for download from the [releases page](https://github.com/GafferHQ/gaffer/releases).


## Building ##

[![Build Status](https://travis-ci.org/GafferHQ/gaffer.svg?branch=master)](https://travis-ci.org/GafferHQ/gaffer)

Gaffer is a fairly large project, and as such has a fairly complex build process. Before you start, make sure you have the following prerequisites installed on your system, which will be used to perform the build itself:

- [SCons](https://www.scons.org)
- [Inkscape](https://inkscape.org)
- [Sphinx](https://www.sphinx-doc.org/) 1.4 or higher (optional)

Gaffer also depends on a number of 3rd-party libraries and python modules, many of which are not entirely straightforward to build. We therefore recommend using the latest pre-built dependencies from the [Gaffer dependencies project](https://github.com/GafferHQ/dependencies/releases). These are used in our automated test builds and so are guaranteed to be up-to-date with Gaffer's requirements.

Once you've downloaded the dependencies, unpack them and move/rename them to the directory in which you want to make your Gaffer build. We'll refer to this location as `<BUILD_DIR>` in the instructions below. Before continuing, make sure the dependencies are unpacked as `<BUILD_DIR>/include`, `<BUILD_DIR>/lib`, etc.

Next, clone the Gaffer source and `cd` into its directory:

```bash
git clone https://github.com/GafferHQ/gaffer.git
cd gaffer
```

You can then build Gaffer with `scons`:

```bash
scons BUILD_DIR=<BUILD_DIR> build
```


## Questions and Troubleshooting ##

If you have any questions about using Gaffer, or encounter problems setting it up, feel free to ask on the [Gaffer community group](https://groups.google.com/forum/#!forum/gaffer-dev). Our users and contributors are happy to help.


## Requesting Features ##

If there is a feature you would like to see in Gaffer, request it on the [Gaffer community group](https://groups.google.com/forum/#!forum/gaffer-dev). Do not create an Issue for it on GitHub.


## Contributions and Bugs Reports ##

Please see the project's [Contributing](https://github.com/GafferHQ/gaffer/blob/master/CONTRIBUTING.md) guidelines.


## Copyright and License ##

© 2018 John Haddon. All rights reserved.

© 2018 Image Engine Design Inc. All rights reserved.

Distributed under the [BSD license](https://github.com/GafferHQ/gaffer/blob/master/LICENSE).
