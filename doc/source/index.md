Introduction
============

Gaffer is a node based application for use in CG and VFX production, with a particular focus on lighting and look development. Scenes are generated procedurally via networks of nodes for loading caches, joining and partitioning, adding lights, assigning shaders and attributes and so on. Gaffer is not tied to any particular renderer, and currently provides out-of-the-box support for [3delight](http://www.3delight.com), [Arnold](https://www.solidangle.com/arnold) and [Appleseed](http://appleseedhq.net).

Gaffer also provides basic 2D compositing functionality, suitable for use in lighting slapcomps and automated pipeline processes. Processing on a renderfarm is defined using graphs of tasks within Gaffer's node editor, with dispatch currently supported via [Tractor](https://renderman.pixar.com/view/pixars-tractor) or a built in local dispatcher.

In addition to itself being highly extensible, Gaffer's underlying frameworks are designed to enable the rapid development of standalone custom tools, both command line and GUI.

- [Installation](Installation/index.md)
- [Tutorials](Tutorials/index.md)
- [Reference](Reference/index.md)
- [Release Notes](ReleaseNotes/index.md)
- [Appendices](Appendices/index.md)
