# Configuring Gaffer for Third-Party Tools #

Gaffer is compatible with the following commercial and open-source third-party tools:

- [Appleseed](http://appleseedhq.net/)
- [Arnold](https://www.solidangle.com/arnold/)
- [3Delight](http://www.3delight.com/)
- [Tractor](https://renderman.pixar.com/tractor)

Gaffer comes with Appleseed, so it will require no additional configuration. For the rest of the tools in this list, you will need to set some additional environment variables.

> Tip :
> If you do not use Appleseed in production, you can hide its nodes and presets from the UI by setting the `GAFFERAPPLESEED_HIDE_UI` environment variable to `1`. Even when set, Appleseed will still be available for OSL shader previews and example scenes.

> Note :
> For the following Linux instructions, we will assume you are using the bash shell and are familiar with terminal commands. Other shells will have comparable methods for setting environment variables.


## Configuring Gaffer for Arnold ##

For Gaffer to load the GafferArnold module, an `ARNOLD_ROOT` environment variable must point to the Arnold installation directory. Before you begin, make sure that Arnold is correctly installed and configured, and close any open instances of Gaffer.


### Arnold in Linux ###

> Note :
> For this instruction, we will assume you have Arnold !ARNOLD_VERSION! installed to `!ARNOLD_PATH_LINUX!`.

To create the `ARNOLD_ROOT` environment variable in Linux:

1. Open `~/.bash_profile` with a text editor.

2. Add the line `export ARNOLD_ROOT=!ARNOLD_PATH_LINUX!` and save.

3. In a terminal, test that the variable is set:

    ```bash
    user@desktop ~ $ echo $ARNOLD_ROOT
    # !ARNOLD_PATH_LINUX!
    ```


### Arnold in Windows ###

> Note :
> For this instruction, we will assume you have Arnold !ARNOLD_VERSION! installed to `!ARNOLD_PATH_WINDOWS!`.

To create the `ARNOLD_ROOT` environment variable in Windows:

1. Open the Command Prompt (Start > Windows System > Command Prompt).

2. Run the command `setx ARNOLD_ROOT "!ARNOLD_PATH_WINDOWS!"`.

3. In a new Command Prompt window, test that the variable is set:

    ```powershell
    C:\Users\user> echo %ARNOLD_ROOT%
    # !ARNOLD_PATH_WINDOWS!
    ```


### Arnold in macOS ###

> Note :
> For this instruction, we will assume you have Arnold !ARNOLD_VERSION! installed to `!ARNOLD_PATH_OSX!`.

To create the `ARNOLD_ROOT` environment variable in macOS:

1. Open `~/.bash_profile` with a text editor.

2. Add the line `export ARNOLD_ROOT=!ARNOLD_PATH_OSX!` and save.

3. Open a terminal (Finder > Go > Utilities > Terminal).

4. Test that the variable is set:

    ```bash
    MacBook:~ user$ echo $ARNOLD_ROOT
    # !ARNOLD_PATH_OSX!
    ```


### Verifying Arnold is loaded ###

The next time you start Gaffer, the Arnold nodes will be available from the node creation menu (right-click inside the Graph Editor).

<!-- TODO: ![](images/arnoldNodes.png "Arnold node menu") -->


## Configuring Gaffer for 3Delight ##

For Gaffer to load the GafferDelight module, a `DELIGHT` environment variable must point to the 3Delight installation directory. Before you begin, make sure that 3Delight is correctly installed and configured, and close any open instances of Gaffer.


### 3Delight in Linux ###

> Note :
> For this instruction, we will assume you have 3Delight !DELIGHT_VERSION! installed to `!DELIGHT_PATH_LINUX!`.

To create the `DELIGHT` environment variable in Linux:

1. Open `~/.bash_profile` with a text editor.

2. Add the line `export DELIGHT=!DELIGHT_PATH_LINUX!` and save.

3. In a terminal, test that the variable is set:

    ```shell
    user@desktop ~ $ echo $DELIGHT
    # !DELIGHT_PATH_LINUX!
    ```


### 3Delight in Windows ###

> Important :
> Gaffer currently requires __3Delight for Maya__ to be included as part of the 3Delight install for access to lights and shaders.

> Tip :
> The 3Delight installer typically configures the `DELIGHT` environment variable on Windows. So the steps below may not be required.

> Note :
> For this instruction, we will assume you have 3Delight !DELIGHT_VERSION! installed to `!DELIGHT_PATH_WINDOWS!`.

To create the `DELIGHT` environment variable in Windows:

1. Open the Command Prompt (Start > Windows System > Command Prompt).

2. Run the command `setx DELIGHT "!DELIGHT_PATH_WINDOWS!"`.

3. In a new Command Prompt window, test that the variable is set:

    ```powershell
    C:\Users\user> echo %DELIGHT%
    # !DELIGHT_PATH_WINDOWS!
    ```


### 3Delight in macOS ###

> Note :
> For this instruction, we will assume you have 3Delight !DELIGHT_VERSION! installed to `!DELIGHT_PATH_OSX!`.

To create the `DELIGHT` environment variable in macOS:

1. Open `~/.bash_profile` with a text editor.

2. Add the line `export DELIGHT=!DELIGHT_PATH_OSX!` and save.

3. Open a terminal (Finder > Go > Utilities > Terminal).

4. Test that the variable is set:

    ```bash
    MacBook:~ user$ echo $DELIGHT
    # !DELIGHT_PATH_OSX!
    ```


### Verifying 3Delight is loaded ###

The next time you start Gaffer, the 3Delight nodes will be available from the node creation menu (right-click inside the Graph Editor).

<!-- TODO: ![](images/delightNodes.png "Delight node menu") -->


## Configuring Gaffer for Tractor ##

For Gaffer to interface with Tractor, the `PYTHONPATH` environment variable must contain the path to the Tractor python module. Before you begin, make sure that Tractor is correctly installed and configured, and close any open instances of Gaffer.


### Tractor in Linux ###

> Note :
> For this instruction, we will assume you have Tractor !TRACTOR_VERSION! installed to `!TRACTOR_PATH_LINUX!`.

To add the Tractor python module to the `PYTHONPATH` environment variable in Linux:

1. Open `~/.bash_profile` with a text editor.

2. Add the line `export PYTHONPATH=$PYTHONPATH\:!TRACTOR_PATH_LINUX!/lib/python2.7/site-packages` and save.

3. In a terminal, test that the variable is set:

    ```shell
    user@desktop ~ $ echo $PYTHONPATH
    # /usr/bin/python2.7:/usr/lib/python2.7:!TRACTOR_PATH_LINUX!/lib/python2.7/site-packages
    ```

> Note :
> Depending on your system's configuration, your `PYTHONPATH` variable might not appear exactly as above. What's important is whether `:!TRACTOR_PATH_LINUX!/lib/python2.7/site-packages` appears in the path.


### Tractor in macOS ###

> Note :
> For this instruction, we will assume you have Tractor !TRACTOR_VERSION! installed to `!TRACTOR_PATH_OSX!`.

To add the Tractor python module to the `PYTHONPATH` environment variable in macOS:

1. Open `~/.bash_profile` with a text editor.

2. Add the line `export PYTHONPATH=$PYTHONPATH\:!TRACTOR_PATH_OSX!/lib/python2.7/site-packages` and save.

3. Open a terminal (Finder > Go > Utilities > Terminal).

4. Test that the variable is set:

    ```shell
    MacBook:~ user$ echo $PYTHONPATH
    # /Library/Frameworks/Python.framework/Versions/2.7/bin:!TRACTOR_PATH_OSX!/lib/python2.7/site-packages
    ```

> Note :
> Depending on your system's configuration, your `PYTHONPATH` variable might not appear exactly as above. What's important is whether `:!TRACTOR_PATH_OSX!/lib/python2.7/site-packages` appears in the path.


### Verifying Tractor is loaded ###

Once the tractor folder has been added to your `PYTHONPATH`, you can then verify that Tractor is loading correctly:

1. Launch Gaffer.

2. Create and select a SystemCommand node (_Dispatch_ > _SystemCommand_).

3. In the Node Editor, click _Execute_. The _Dispatcher_ window will open.

4. _Tractor_ will be available in the _Dispatcher_ drop-down menu.

<!-- TODO: ![](images/tractorDispatch.png "Tractor dispatch") -->


## See also ##

- [Setting Up the "gaffer" Command](../SettingUpGafferCommand/index.md)
- [Installing Gaffer](../InstallingGaffer/index.md)
