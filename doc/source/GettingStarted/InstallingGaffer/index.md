<!-- !NO_SCROLLSPY -->

# Installing Gaffer #

The Gaffer package is a self-contained directory, so you will need to manually install it, and later manually configure it, if necessary. Once extracted, the Gaffer directory contains the complete application, ready for use.

> Note :
> In keeping with Linux/macOS best practices, we will demonstrate how to install Gaffer in the `/opt/` directory. However, you could install it to any location on your file system to which you have write and execute access.


## Installing in Linux ##

To install Gaffer in Linux:

1. Download the [latest Linux package of Gaffer](https://github.com/GafferHQ/gaffer/releases/download/!GAFFER_VERSION!/gaffer-!GAFFER_VERSION!-linux.tar.gz).

2. Open a terminal.

3. Extract the archive:

    ```bash
    user@desktop ~ $ cd ~/Downloads
    user@desktop ~/Downloads $ sudo tar -xzf gaffer-!GAFFER_VERSION!-linux.tar.gz -C /opt/
    ```

Gaffer is now installed to `/opt/gaffer-!GAFFER_VERSION!-linux`.


## Installing in macOS ##

To install Gaffer in macOS:

1. Download the [latest macOS package of Gaffer](https://github.com/GafferHQ/gaffer/releases/download/!GAFFER_VERSION!/gaffer-!GAFFER_VERSION!-macos.tar.gz).

2. Open the terminal (Finder > Go > Utilities > Terminal).

3. Extract the archive:

    ```bash
    MacBook:~ user$ cd ~/Downloads
    MacBook:~/Downloads user$ tar -xzf gaffer-!GAFFER_VERSION!-macos.tar.gz -C /opt/
    ```

Gaffer is now installed to `/opt/gaffer-!GAFFER_VERSION!-macos`.


## See also ##

- [Launching Gaffer for the First Time](../LaunchingGafferFirstTime/index.md)
- [Setting Up the "gaffer" Command](../SettingUpGafferCommand/index.md)
- [Configuring Gaffer for Third-Party Tools](../ConfiguringGafferForThirdPartyTools/index.md)
