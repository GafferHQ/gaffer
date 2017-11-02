Installation
============

To install Gaffer, simply download and unpackage the appropriate bundle for your platform from the [GitHub release page](https://github.com/GafferHQ/gaffer/releases/!GAFFER_VERSION!). The resulting directory will contain the complete application ready to use, and you can launch Gaffer immediately by running the `bin/gaffer` script from within that directory.

The gaffer distribution can be moved to any suitable location on the filesystem. For convenience, you should add `<GAFFER_INSTALL_PATH>/bin` to the `PATH` environment variable so that Gaffer can be run more simply as `gaffer` (where `<GAFFER_INSTALL_PATH>` is the location where you have moved the gaffer directory).

> Note :
>
> This section and the next assume you have basic proficiency in using shell commands.
> If you don't, the following should be enough to launch Gaffer for the first time.
> Assuming your web browser has placed the download in your Downloads folder, open a terminal
> and enter these commands :
>
> ```shell
> cd ~/Downloads
> tar -xzf gaffer-!GAFFER_VERSION!-linux.tar.gz
> cd gaffer-!GAFFER_VERSION!-linux
> ./bin/gaffer
> ```
>
> If installing on OS X, then please substitute **osx** for **linux** above.

Configuring 3rd party tools
---------------------------

Gaffer is shipped with the open source Appleseed renderer, ready to use with no further configuration. To set up a 3rd party renderer or dispatcher, it is necessary to set some environment variables as described below.

> Note :
>
> The examples below all assume your are installing Gaffer for **Linux**. For **OS X**, please
> substitute `DYLD_LIBRARY_PATH` for all occurrences of `LD_LIBRARY_PATH`.

### 3delight

- Ensure that `$DELIGHT` points to the location where 3delight is installed.

### Arnold

- Ensure that `$ARNOLD_ROOT` points to the location where Arnold is installed.

### Tractor

- Add the location of the `tractor` python module to the `$PYTHONPATH` environment
  variable.


