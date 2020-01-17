# Setting Up the "gaffer" Command #

After you have installed Gaffer, it will remain a collection of files and directories on your file system. Because it is not yet configured as a command, you must navigate to its directory every time. This could become very tedious, so we recommend that you modify your `PATH` environment variable to allow access to the `gaffer` command from anywhere in the terminal.

> Note :
> For these instructions, we will assume you have Gaffer installed to the `/opt/` directory. If you have installed it elsewhere, replace `/opt/` with the directory you installed it to.


### Environment variables ###

An environment variable is simply a value, such as a string, number, boolean, or location that your terminal is aware of. For instance, when you ran the `tar` command to extract the downloaded Gaffer package, the `tar` command was not located in your `~/Downloads` directory, but actually in `/usr/bin/`. Whenever you open your terminal, several folders are added to your terminal's `PATH` environment variable, which provides it with a list of locations in the file system from which it can source commands.

In order for the `gaffer` command to work in your terminal, you will need to add Gaffer's directory to the `PATH` environment variable.


## Setting up the "gaffer" command in Linux ##

The particular terminal on your system depends on your Linux distribution and how it was configured. Most distributions of Linux use bash, but there are other common terminals available, like tcsh. Because we cannot accommodate every available terminal, we will only provide instructions for adding to the `PATH` variable in bash and tcsh.

> Tip : 
> If you are not sure which terminal you have, you can find its name by opening a terminal and inputting `echo $0`, which will return `/bin/bash`, `tcsh`, or some equivalent. If you are not using bash or tcsh, the same principles of environment variables will apply, and your terminal's documentation should provide a comparable way of modifying the `PATH` variable.

To set up the `gaffer` command in Linux:

1. Open your terminal's config file in a text editor.
    
    - bash config: `~/.bash_profile`
    - tcsh config: `~/.tcsh_profile`

2. Add the following line to the end of the file:
    
    - bash: `export PATH=$PATH\:/opt/gaffer-!GAFFER_VERSION!-linux/bin`
    - tcsh: `setenv PATH $PATH\:/opt/gaffer-!GAFFER_VERSION!-linux/bin`

3. Save the file.

4. Open a terminal.

5. Test that the `PATH` variable has been updated:

    ```bash
    user@desktop ~ $ echo $PATH
    # /usr/local/bin:/usr/bin:/bin:/opt/gaffer-!GAFFER_VERSION!-linux/bin
    ```

> Note :
> Depending on your system configuration, the beginning of your `PATH` variable might not appear exactly as above. What's important is whether `/opt/gaffer-!GAFFER_VERSION!-linux/bin` appears at the end of the path.

You can now execute `gaffer` as a command from any directory in the terminal.


## Setting up the "gaffer" command in macOS ##

The default terminal in macOS is bash, so you will need to add to the `PATH` variable in the bash user config.

To set up the `gaffer` command in macOS:

1. Open `~/.bash_profile` in a text editor.

2. Add the line `export PATH=$PATH\:/opt/gaffer-!GAFFER_VERSION!-macos/bin` and save.

3. Open the terminal (Finder > Go > Utilities > Terminal).

4. Test that the `PATH` variable has been updated:

    ```bash
    MacBook:~ user$ echo $PATH
    # /usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/opt/X11/bin:/opt/gaffer-!GAFFER_VERSION!-macos/bin
    ```

> Note :
> Depending on your system configuration, the beginning of your `PATH` variable might not appear exactly as above. What's important is whether `/opt/gaffer-!GAFFER_VERSION!-macos/bin` appears at the end of the path.

You can now execute `gaffer` as a command from any directory in the terminal.


## Using the "gaffer" command ##

Once you have added the Gaffer directory to the `PATH` variable, you can launch Gaffer anywhere in the terminal:

```bash
gaffer
```

You can also use the command to open Gaffer scripts, as outlined in the [Command Line Reference](../../Reference/CommandLineReference/index.md).


## See also ##

- [Installing Gaffer](../InstallingGaffer/index.md)
- [Configuring Gaffer for Third-Party Tools](../ConfiguringGafferForThirdPartyTools/index.md)
