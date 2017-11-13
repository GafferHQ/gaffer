Gaffer
======

Gaffer is an open source application framework designed specifically for creating tools for use in visual effects production. It builds on top of the Cortex libraries, adding a flexible node-based computation framework and a user interface framework for editing and viewing node graphs. Gaffer ships with a number of sample modules and applications, not least of which is a module for the on-demand generation of procedural scenes for rendering.

More information can be found on the [project homepage](http://gafferhq.org).

Developer notes are available on the [project wiki](https://github.com/GafferHQ/gaffer/wiki).

Easy way - Downloading
===========

If you want to give Gaffer a try, without going trough the complex building process, just download the latest compiled binary release from the [releases page](https://github.com/GafferHQ/gaffer/releases).

To run it, extract the archive and run the `gaffer` executable you will find in the `bin` directory.

For example, on linux (after you download it):

```
cd ~/apps
tar -xzf ~/Downloads/gaffer-*-linux.tar.gz
cd gaffer-*-linux
./bin/gaffer
```

More in detail information can be found on the [installation page](http://gafferhq.org/documentation/Installation)

Hard way - Building
========

[![Build Status](https://travis-ci.org/GafferHQ/gaffer.svg?branch=master)](https://travis-ci.org/GafferHQ/gaffer)

Gaffer is a fairly large project, and as such has a fairly complex build process. Before you start, you'll want to make sure you have the following prerequisites installed on your system - these will be used to perform the build itself :

- [SCons](http://www.scons.org)
- [Inkscape](http://inkscape.org)
- [Sphinx](http://www.sphinx-doc.org/) (optional, minimum version 1.3)

Gaffer also depends on a number of 3rd party libraries and python modules, many of which are not entirely straightforward to build. We therefore recommend using the latest prebuilt dependencies from the [gaffer dependencies project](https://github.com/GafferHQ/dependencies/releases). These are used in our automated test builds and so are guaranteed to be up to date with Gaffer's requirements.

Once you've downloaded the dependencies, you'll want to unpack them and move/rename them to the directory in which you want to make your Gaffer build. We'll refer to this location as `<BUILD_DIR>` in the instructions below - before continuing make sure the dependencies are unpacked as `<BUILD_DIR>/include`, `<BUILD_DIR>/lib` etc.

Next, get yourself a clone of the Gaffer source and change into that directory :

```
git clone https://github.com/GafferHQ/gaffer.git
cd gaffer
```

You can then build Gaffer itself as follows :

```
scons BUILD_DIR=<BUILD_DIR> build
```

If you encounter any problems, please get in touch via [the developer mailing list](https://groups.google.com/forum/#!forum/gaffer-dev) and we'll do our best to help get you up and running.

Contributing
============

Contributions to Gaffer are welcome. For small fixes we suggest just going ahead and making a pull request - for anything larger we recommend dicussing it on the [developer list](https://groups.google.com/forum/#!forum/gaffer-dev) first, to avoid duplication of effort and to ensure that your whizz-bang ideas fit in with the general direction of the project.

Copyright and License
=====================

© 2013, Image Engine Design Inc. © 2013, John Haddon under [the BSD license](https://github.com/GafferHQ/gaffer/blob/master/LICENSE)
