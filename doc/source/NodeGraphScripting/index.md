# Node Graph Scripting #

Since much of Gaffer's framework is built and wrapped in Python, Gaffer supports building and modifying the node graph in Python, as well as directly executing code to manipulate data during script dispatch.

The following articles cover topics related to the scripting in the node graph, such as using the built-in script and code editor interfaces, and using the built-in code nodes.


## Script Editor ##

Gaffer's interface has a built-in _Script Editor_ for interactively building and modifying the node graph in Python, as well as for testing and querying the Gaffer [Scripting API](../ScriptingAPI/index.md).

- [The Script Editor](ScriptEditor/index.md)
- [Using the Script Editor](UsingScriptEditor/index.md)


## Code Nodes ##

Some of Gaffer's default modules contain special nodes for evaluating code during script dispatch.

- [The Code Nodes](CodeNodes/index.md)


<!-- TOC -->

```eval_rst
.. toctree::
    :hidden:
    :titlesonly:
    :maxdepth: 1

    ScriptEditor/index.md
    UsingScriptEditor/index.md
    CodeNodes/index.md
```
