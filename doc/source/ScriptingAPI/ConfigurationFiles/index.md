# Configuration Files #

Gaffer applications <!-- TODO: reference article on applications --> are intended to be easily extensible and customizable, and to this end provide many scripting hooks for registering new behaviours and customizing the UI. At startup, Gaffer looks for user configuration files to execute, providing an opportunity for you to configure it for your needs, whether in a studio environment or at home.


## Startup File Locations ##

The location of Gaffer's configuration files are specified by the `GAFFER_STARTUP_PATHS` environment variable. This is a colon-separated list of paths to directories where any startup files reside. The contents of the directory at the end of the list are executed first, allowing them to be overridden by directories earlier in the list.

When launched, Gaffer automatically adds the `~/gaffer/startup` configuration directory to `GAFFER_STARTUP_PATHS`, to allow users to create their own config files without needing to make any changes to their environment. This user-level config is run last, allowing it to override studio-level configuration files.

Within a startup directory, config files are stored in subdirectories, by application name. Each application executes the files in their appropriate directory. For example, the GUI app executes any files in the `~/gaffer/startup/gui` directory.


## See Also ##

- [Tutorial: Creating Configuration Files](../../Tutorials/Scripting/CreatingConfigurationFiles/index.md)
