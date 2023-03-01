<!-- !NO_SCROLLSPY -->

# Launching Gaffer for the First Time #

Once Gaffer has been installed, you will probably want to try it out right away before performing any additional configuration. To launch it, you can run its application file directly from the binary directory.

> Note :
> For these instructions, we will assume you have Gaffer installed to the `/opt/` directory on Linux or macOS and `C:\software\` on Windows. If you have installed it elsewhere, replace `/opt/` or `C:\software\` with the directory you installed it to.

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


## Launching in Windows ##

To launch Gaffer for the first time in Windows:

1. Open the Command Prompt (Start > Windows System > Command Prompt).

2. Navigate to the Gaffer binary directory and run the Gaffer application:
    ```powershell
    C:\Users\user> cd C:\software\gaffer-!GAFFER_VERSION!-windows\bin
    C:\software\gaffer-!GAFFER_VERSION!-windows\bin> gaffer.cmd
    ```

Gaffer will launch in a new window.

> Tip :
> Gaffer can also be launched by browsing to `C:\software\gaffer-!GAFFER_VERSION!-windows\bin` in Windows Explorer and double-clicking on `gaffer.cmd`.

> Note :
> Gaffer requires the [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) to be installed on Windows. If you see errors related to missing `VCRUNTIME` files such as `VCRUNTIME140.dll`, the redestributable will need to be [downloaded](https://aka.ms/vs/17/release/vc_redist.x64.exe) and installed before Gaffer can be launched.

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
