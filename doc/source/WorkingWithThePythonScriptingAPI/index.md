# Working with the Python Scripting API #

With its core architecture built from a combination of C++ and Python, Gaffer ships with a convenient Python scripting API. A significant portion of the project uses Python: nodes are exposed to Python in the main application, the node graph file formats are Python scripts, much of the GUI is written in Python, and the various Gaffer applications are configured by Python scripts. Through the main application's built-in Python Editor, you can interactively build and modify the node graph, test expressions, and inspect data. What's more, with a modicum of knowledge in Python and the Gaffer architecture, you can configure and customize each Gaffer application to suit your studio or pipeline needs.

> Important :
> With regards to node graphs, do not confuse the use of the scripting API with expressions inside Expression nodes. The scripting API can be applied in the main application to interactively modify, inspect, test, and debug a node graph. Expressions, on the other hand, are bits of code stored on Expression nodes **inside** a graph, that allow you to dynamically change plug values during the graph's execution.


## Python scripting in graphs ##

In Gaffer, a **script** is a set of serial Python instructions for building a node graph. When Gaffer saves a `.gfr` or `.grf` file, the script serializer traverses the nodes, connections, and plug values, and assembles a series of Python instructions to recreate the graph later. Serialization also comes into play when you copy and paste nodes. If you copy nodes from a graph and paste the clipboard into a text editor, the resulting text will be the recipe for those nodes in Python.

Gaffer node graphs are stored on disk as Python scripts with the `.gfr` file extension. References stored on disk are also Python scripts, but with the `.grf` extension and a slightly different structure.

Do not confuse scripts with active node graphs or expressions: when a node graph is open in Gaffer, or in the middle of executing, its nodes and plugs are stored in memory as C++ objects. All a scripts does is provide a list of instructions Gaffer on how to **build** a graph, which Gaffer can interpret.


## Python scripting API basics ##

- [Tutorial: Node Graph Editing in Python](TutorialNodeGraphEditingInPython/index.md)
- [The Python Editor](ThePythonEditor/index.md)


## Intermediate Python scripting API ##

- [Tutorial: Startup Config 1; Custom Global Context Variables](TutorialStartupConfig1/index.md)
- [Tutorial: Startup Config 2; Custom Global Context Variables](TutorialStartupConfig2/index.md)
- [Tutorial: Startup Config 3; Custom Global Context Variables](TutorialStartupConfig3/index.md)

<!-- TOC -->

```{eval-rst}
.. toctree::
    :titlesonly:
    :hidden:

    ThePythonEditor/index.md
    TutorialNodeGraphEditingInPython/index.md
    TutorialQueryingAScene/index.md
    TutorialStartupConfig1/index.md
    TutorialStartupConfig2/index.md
    TutorialStartupConfig3/index.md
```
