Scripting
=========

All of Gaffer’s core functionality is available to be scripted using Python - in fact much of the GUI application itself is written in Python, Gaffer plugins are just Python modules, and the file format itself is simply a Python script with a .gfr extension.

There is a direct one to one correspondence between the C++ and Python APIs for Gaffer, so if you start out using one, you can easily transfer to the other. This makes it relatively straightforward to prototype in Python, but convert to C++ if performance becomes an issue, or to spend most of your time hacking away in C++ but still be comfortable writing some GUI code in Python.

<!-- TOC -->

```eval_rst
.. toctree::
    :titlesonly:

    GettingStarted/index.md
    CreatingConfigurationFiles/index.md
    AddingAMenuItem/index.md
    QueryingAScene/index.md
    UsingTheOSLCodeNode/index.md
```
