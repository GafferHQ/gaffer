<!-- !NO_SCROLLSPY -->

# Launching Gaffer for the First Time #

Once Gaffer has been installed, you will probably want to try it out right away before performing any additional configuration. To launch it, you can run its application file directly from the binary directory.

> Note :
> For these instructions, we will assume you have Gaffer installed to the `/opt/` directory. If you have installed it elsewhere, replace `/opt/` with the directory you installed it to.

> Caution :
> When you run Gaffer from a terminal, its continued operation is dependent on that terminal window. If you close the terminal, it will also close Gaffer, and you may lose any unsaved data.


## Launching in Linux ##

To launch Gaffer for the first time in Linux:

1. Open a terminal.

2. Navigate to the Gaffer binary directory and run the Gaffer application:
    ```shell
    user@desktop ~ $ cd /opt/gaffer-!GAFFER_VERSION!-linux/bin
    user@desktop /opt/gaffer-!GAFFER_VERSION!-linux/bin $ ./gaffer
    ```

Gaffer will launch in a new window.


## Launching in macOS ##

To launch Gaffer for the first time in macOS:

1. Open the terminal (Finder > Go > Utilities > Terminal).

2. Navigate to the Gaffer binary directory and run the Gaffer application:
    ```shell
    MacBook:~ user$ cd /opt/gaffer-!GAFFER_VERSION!-macos/bin
    MacBook:/opt/gaffer-!GAFFER_VERSION!-macos/bin user$ ./gaffer
    ```

Gaffer will launch in a new window.


## See also ##

- [Installing Gaffer](../InstallingGaffer/index.md)
- [Setting Up the "gaffer" Command](../SettingUpGafferCommand/index.md)
- [Configuring Gaffer for Third-Party Tools](../ConfiguringGafferForThirdPartyTools/index.md)
