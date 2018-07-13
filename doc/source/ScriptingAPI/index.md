# Scripting API #

Gaffer's framework is built from a combination of C++ and Python. A significant portion of the core architecture has hooks in Python: much of the GUI is written in Python, nodes are wrapped in Python, and the Gaffer file formats are simple Python scripts.

There is a direct one-to-one correspondence between Gaffer's C++ and Python APIs, so if you start out using one language, you can easily transfer your work to the other. It is relatively straightforward to prototype in Python, and later convert to C++ if performance becomes an issue. Or, alternatively, you can spend most of your time coding in C++, and switch to Python when greater ease and flexibility are needed.

The following articles specify Gaffer's scripting API, covering topics related to the node graph, UI, and file formats.


<!-- ## Tutorials ## -->
<!-- Before diving in to the scripting API, we recommend completing the [Scripting Basics tutorial](../Tutorials/ScriptingBasics/index.md). The following tutorials cover more advanced and specialized topics. -->
<!-- - [Tutorial: Querying a Scene](Tutorials/QueryingAScene/index.md) -->
<!-- - [Tutorial: Creating a Configuration File](Tutorials/CreatingConfigurationFile/index.md) -->
<!-- - [Tutorial: Adding a Menu Item](Tutorials/AddingMenuItem/index.md) -->


## Script Syntax ##

- [Dictionary Syntax](DictionarySyntax/index.md)
- [Special Variables](SpecialVariables/index.md)
- [Node Modules](NodeModules/index.md)


## Script Files ##

- [Script Files](ScriptFiles/index.md)
- [Configuration Files](ConfigurationFiles/index.md)


## Context ##

- [Context](Context/index.md)
- [Scene Context](SceneContext/index.md)


<!-- TOC -->

```eval_rst
.. toctree::
    :hidden:
    :titlesonly:
    :maxdepth: 1

    DictionarySyntax/index.md
    SpecialVariables/index.md
    NodeModules/index.md
    ScriptFiles/index.md
    ConfigurationFiles/index.md
    Context/index.md
    SceneContext/index.md
```
