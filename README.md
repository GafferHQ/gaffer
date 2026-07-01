![Gaffer Logo](resources/GafferLogo.svg)

# Gaffer #

Gaffer is a VFX application that enables look developers, lighters, and compositors to easily build, tweak, iterate, and render scenes. Gaffer supports in-application scripting in Python and [OSL](https://github.com/AcademySoftwareFoundation/OpenShadingLanguage), so VFX artists and technical directors can design shaders, automate processes, and build production workflows.

An open-source project, Gaffer also provides an application framework for studios to design and create their own VFX production pipeline tools. Built using the [Cortex](https://github.com/ImageEngine/cortex) libraries, Gaffer ships with a multi-threaded, deferred evaluation engine and a flexible user interface framework.

More information about Gaffer and its use in studios can be found at [GafferHQ](https://gafferhq.org).

Users can learn how to use Gaffer through the [documentation](https://gafferhq.org/documentation).

Developer notes are available on the [Gaffer developer wiki](https://github.com/GafferHQ/gaffer/wiki).

Participating in the Gaffer community requires abiding by the project's [Code of Conduct](CODE_OF_CONDUCT.md).


## Download ##

Compiled binary releases are available for download from the [releases page](https://github.com/GafferHQ/gaffer/releases).

Gaffer is officially supported and tested on **Linux** (RHEL/Rocky/AlmaLinux 9) and **Windows** (Windows 10/11).


## Building ##

[![CI](https://github.com/GafferHQ/gaffer/workflows/CI/badge.svg)](https://github.com/GafferHQ/gaffer/actions?query=workflow%3ACI)

Gaffer targets the [VFX Reference Platform](https://vfxplatform.com). We are currently on **CY2024**. Aside from general platform development packages, we specifically require the following tools that may not be installed by default on your system. Without these, you will not be able to build Gaffer.

> **Note:** From time to time, this list may change. For a complete, accurate, and up-to-date method of installing the prerequisites on Linux, refer to the [Podman setup](https://github.com/GafferHQ/build/blob/main/Containerfile) we use for building automatic releases.

### Build requirements ###


> **Note:** Specific package names may differ depending on your Linux distribution and repository.

#### Main build requirements ####


Package Name | Version
------------ |:--------------:
[`gcc`](https://gcc.gnu.org/index.html) | 11.2.1
[`scons`](http://www.scons.org) |
[`inkscape`](http://inkscape.org) |


#### Documentation build requirements ####

> **Note:** Building the documentation is optional.

Package Name | Minimum Version
------------ |:--------------:
[`sphinx`](http://www.sphinx-doc.org/) | 4.3.1

Python Module | Required version
------------- |:---------------:
`sphinx_rtd_theme` | 1.0.0
`myst-parser` | 0.15.2
`docutils` | 0.17.1


### Build process ###

```bash
git clone https://github.com/GafferHQ/gaffer.git
cd gaffer
```

Gaffer depends on a number of 3rd-party libraries. We recommend using the pre-built dependencies from the [Gaffer dependencies project](https://github.com/GafferHQ/dependencies/releases). These are used in our automated test builds and so are guaranteed to be up-to-date with Gaffer's requirements.

The dependencies distribution forms the basis of a Gaffer build and the root of the expanded archive becomes the `BUILD_DIRECTORY` we pass to `scons`.

The easiest way to get the right dependencies version is to use the `config/installDependencies.sh` script included in the Gaffer source tree. This downloads the correct version for the version of Gaffer you are building and unpacks them to a directory of your choice.

In this example we're going to build gaffer to a `gaffer-build` directory next to our checkout.


```bash
./config/installDependencies.sh ../gaffer-build
```

You can then build Gaffer itself:

```bash
scons build BUILD_DIR=../gaffer-build
```

> **Note:** If `scons` has any issues finding dependencies or tools, see `SConstruct` for the various options that can be set to specify their location.

With any luck, you now have a functioning version of Gaffer.

```bash
../gaffer-build/bin/gaffer
```

### Build process on Windows 11###

#### 1- Use Git Bash

```bash
# Must be executed inside Git Bash to interpret the .sh file
./config/installDependencies.sh ../gaffer-build
```
Once the dependencies finish unpacking into your gaffer-build directory, close Git Bash.

#### 2- Install Scons

```powershell
:: 1. Navigate to your local clone directory
cd path\to\your\gaffer

:: 2. Install SCons into your python environment if you haven't already
pip install scons
```

#### 3- Add existing 7-Zip to your System PATH
- Typically, it is located at C:\Program Files\7-Zip. Check if 7z.exe is sitting inside that folder.
- In your Windows Search bar, type "environment variables" and select Edit the system environment variables.
- Click the Environment Variables... button at the bottom right.
- In the System variables list (the bottom section), find Path and click Edit....
- Click New and paste the path: C:\Program Files\7-Zip
- Click OK on all windows to save.
- Restart your terminal and run the script again.

#### 4- Force Python to use UTF-8 encoding in this PowerShell window

```powershell
[System.Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "User")
```

#### 5- Scons tips for laters

Before you can build you need to setup a few things because of the difference between linux and windows. Windows requires a little bit more hand holding. Make sure you do these steps below for a successful and fluid build.

***1. Inkscape Errors:*** Gaffer utilizes Inkscape purely during the compilation phase to automatically convert all of the UI icon assets (.svg vector files) into .png raster graphics for the application layouts. But the problem is that even though Inkscape might be in the environment path scons will not find it. So we have to force it in the command line. The line to add at the end of the build command is `INKSCAPE="C:\Program Files\Inkscape\bin\inkscape.exe" --config=force`

***2. Scons cannot see installed git:*** Same issue with Inkscape we'll need to create a symbolic link to the real git for scons to see. Open power shell in elviated privilages
```powershell
# Create a link from your real git executable straight into the gaffer-build folder
New-Item -ItemType SymbolicLink -Path "C:\src\gaffer-build\bin\git.exe" -Target "C:\Program Files\Git\bin\git.exe"
```

***3. GLEW.lib:*** The linker will blow up looking for GLEW.lib, the fix is to find the real file, and create a mirror copy named exactly what the linker wants.
Open a normal PowerShell window and search for the actual GLEW library file inside your dependencies directory:
```powershell
Get-ChildItem -Path "C:\src\gaffer-build\lib\" -Filter "*glew*"
```
*(You will likely see `glew32.lib` or `glew32s.lib` print out in the list).*

Now, Open **PowerShell as an Administrator**, and create a hard link pointing from their expected name to the file that *actually* exists.
**If the file found was `glew32.lib`, run:**
```powershell
New-Item -ItemType HardLink -Path "C:\src\gaffer-build\lib\GLEW.lib" -Value "C:\src\gaffer-build\lib\glew32.lib"
```

***4. Build Time:*** By default, SCons acts conservatively and compiles everything on a single CPU thread. You need to explicitly tell it to spin up parallel workers using the -j (jobs) flag. ***Note: switching to multi core build will error out when reaching the Inkscape stage. Because you split the build into multiple parallel threads using `-j 8`, Gaffer launched 8 separate instances of Inkscape simultaneously, all trying to access the exact same SVG file at once. Inkscape on Windows often handles parallel thread calling very poorly, resulting in memory overflows and crashes. Since you only need to build these icons once (and they don't change when you tweak your RenderMan C++ node code), you can bypass this multi-threaded bug easily.Because SCons tracks file generation states, it will not recompile any of your C++ code. All your RenderMan and Gaffer UI objects are already safely compiled as .obj and .dll binaries from your last run. So make sure to run the build again with `-j 1` when the build errors out on the icons

#### 5- Building on windows
Once all the tips in step #5 are completed open a fresh powershell and run the following command to build for various render engines

1. Default build with cycles: `scons build -j 16 BUILD_DIR=../gaffer-build NKSCAPE="C:\Program Files\Inkscape\bin\inkscape.exe"`
2. Build with RenderMan: `scons build -j 16 RENDERMAN_ROOT="C:\Program Files\Pixar\RenderManProServer-27.3" build BUILD_DIR=../gaffer-build NKSCAPE="C:\Program Files\Inkscape\bin\inkscape.exe"`
3. Build with Arnold: `scons build -j 16 ARNOLD_ROOT="C:\src\Arnold-7.5.2.0" build BUILD_DIR=../gaffer-build NKSCAPE="C:\Program Files\Inkscape\bin\inkscape.exe"`
4. Build with 3Delight: `scons build -j 16 DELIGHT_ROOT="C:\Program Files\3Delight" build BUILD_DIR=../gaffer-build NKSCAPE="C:\Program Files\Inkscape\bin\inkscape.exe"`

If you want to build for all engines just add reach location one after the other as following:
```powershell
scons build -j 16 RENDERMAN_ROOT="C:\Program Files\Pixar\RenderManProServer-27.3" ARNOLD_ROOT="C:\src\Arnold-7.5.2.0" DELIGHT_ROOT="C:\Program Files\3Delight" BUILD_DIR=..\gaffer-build INKSCAPE="C:\Program Files\Inkscape\bin\inkscape.exe"
```

***Once you hit the Inkscape error, redo the above command with***
```powershell
scons build -j 1 RENDERMAN_ROOT="C:\Program Files\Pixar\RenderManProServer-27.3" ARNOLD_ROOT="C:\src\Arnold-7.5.2.0" DELIGHT_ROOT="C:\Program Files\3Delight" BUILD_DIR=..\gaffer-build INKSCAPE="C:\Program Files\Inkscape\bin\inkscape.exe"
```

### Building with third-party renderer support

Gaffer dependencies ships with Cycles, but to build the modules for one of the other supported third-party renderers, you will need to set appropriate `scons` options pointing to your installation. The options are:

- Arnold: `ARNOLD_ROOT`
- 3Delight: `DELIGHT_ROOT`

For example, the following command builds Gaffer with Arnold support:

```bash
scons build ARNOLD_ROOT=/path/to/arnold BUILD_DIR=...
````

## Questions and troubleshooting ##

If you have any questions about using Gaffer, or encounter problems setting it up, feel free to ask on the [Gaffer community group](https://groups.google.com/g/gaffer-dev). Our users and contributors are happy to help.


## Requesting features ##

If there is a feature you would like to see in Gaffer, request it on the [Gaffer community group](https://groups.google.com/g/gaffer-dev). Do not create an Issue for it on GitHub.


## Contributions and bugs reports ##

Please see the project's [contribution guidelines](CONTRIBUTING.md).


## Copyright and license ##

© 2011–2025 John Haddon. All rights reserved.

© 2011–2025 Image Engine Design Inc. All rights reserved.

© 2011–2025 Cinesite VFX Ltd. All rights reserved.

Distributed under the [BSD license](LICENSE).
