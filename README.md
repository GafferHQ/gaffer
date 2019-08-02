![Gaffer Logo](resources/GafferLogo.svg)

# Gaffer #

Gaffer is a VFX application that enables look developers, lighters, and compositors to easily build, tweak, iterate, and render scenes. Gaffer supports in-application scripting in Python and [OSL](https://github.com/imageworks/OpenShadingLanguage), so VFX artists and technical directors can design shaders, automate processes, and build production workflows.

An open-source project, Gaffer also provides an application framework for studios to design and create their own VFX production pipeline tools. Built using the [Cortex](https://github.com/ImageEngine/cortex) libraries, Gaffer ships with a multi-threaded, deferred evaluation engine and a flexible user interface framework.

More information about Gaffer and its use in studios can be found at [GafferHQ](https://gafferhq.org).

Users can learn how to use Gaffer through the [documentation](https://gafferhq.org/documentation).

Developer notes are available on the [Gaffer developer wiki](https://github.com/GafferHQ/gaffer/wiki).

Participating in the Gaffer community requires abiding by the project's [Code of Conduct](CODE_OF_CONDUCT.md).


## Download ##

Compiled binary releases are available for download from the [releases page](https://github.com/GafferHQ/gaffer/releases).


## Building ##

[![Build Status](https://travis-ci.com/GafferHQ/gaffer.svg?branch=master)](https://travis-ci.com/GafferHQ/gaffer)

[![Build Status](https://dev.azure.com/GafferHQ/Gaffer/_apis/build/status/GafferHQ.gaffer?branchName=master)](https://dev.azure.com/GafferHQ/Gaffer/_build/latest?definitionId=1&branchName=master)

Gaffer is a fairly large project, and as such has a fairly complex build process. Before you start, make sure you have the following prerequisites installed on your system, which will be used to perform the build itself.


### Build requirements ###

From time to time, this list may change. For a complete, accurate, and up-to-date method of installing the prerequisites on CentOS, refer to the [Docker setup](https://github.com/GafferHQ/build/blob/master/Dockerfile) we use for building automatic releases.

> **Note:** Specific package names may differ depending on your Linux distribution and repository.


#### Main build requirements ####

> **Note:** Large Linux distros focused on usability, such as CentOS and Ubuntu, ship with many of these packages by default.

Package Name | Minimum Version
------------ |:--------------:
**General** | -
[gcc](https://gcc.gnu.org/index.html) | 6.3.1
[scons](http://www.scons.org) |
**OpenGL** | -
[libX11-devel](https://www.x.org) |
[libXi-devel](https://www.x.org) |
[libXmu-devel](https://www.x.org) |
[mesa-libGL-devel](https://www.mesa3d.org) |
[mesa-libGLU-devel](https://www.mesa3d.org) |


#### Documentation build requirements ####

> **Note:** Building the documentation is optional.

Package Name | Minimum Version
------------ |:--------------:
[sphinx](http://www.sphinx-doc.org/) | 1.4
[inkscape](http://inkscape.org) |

> **Note:** We recommend using [pip](https://pypi.org/project/pip) to manage Python modules.

Python Module |
---------- |
sphinx_rtd_theme |
recommonmark |


### Build process ###

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


## Questions and troubleshooting ##

If you have any questions about using Gaffer, or encounter problems setting it up, feel free to ask on the [Gaffer community group](https://groups.google.com/forum/#!forum/gaffer-dev). Our users and contributors are happy to help.


## Requesting features ##

If there is a feature you would like to see in Gaffer, request it on the [Gaffer community group](https://groups.google.com/forum/#!forum/gaffer-dev). Do not create an Issue for it on GitHub.


## Contributions and bugs reports ##

Please see the project's [contribution guidelines](CONTRIBUTING.md).


## Copyright and license ##

© 2011–2019 John Haddon. All rights reserved.

© 2011–2019 Image Engine Design Inc. All rights reserved.

Distributed under the [BSD license](LICENSE).
