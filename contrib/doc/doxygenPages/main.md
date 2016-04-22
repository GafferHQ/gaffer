Welcome to the Gaffer Frameworks              {#mainpage}
=========================================================

The C++ libraries and Python modules documented here form the basis of the [Gaffer application](http://imageengine.github.io/gaffer/). They may be used to write extension modules for Gaffer itself, as libraries for use in other packages, or to write entirely new applications.

Gaffer
------

This library provides the basis for creating node graphs using the Gaffer::Node and Gaffer::Plug classes. It provides a few concrete node types, such as Gaffer::Expression and Gaffer::Random - but most nodes are implemented in libraries with a specific area of focus.

GafferImage
-----------

This library implements a simple image processing framework on top of the main Gaffer library. Images are passed between nodes using GafferImage::ImagePlug, and image processing nodes derive from GafferImage::ImageProcessor.

GafferScene
-----------

This library implements a framework for processing 3d scenegraphs. Scenes are passed between nodes using GafferScene::ScenePlug, and scene processing nodes derive from GafferScene::SceneProcessor. The GafferScene::ObjectSource base class provides a simple way of adding new primitive types to Gaffer, and the GafferScene::SceneElementProcessor base class provides a basis for manipulating the transforms, objects and attributes that make up a scene.

GafferUI
--------

This library provides a framework for building user interfaces for the node graphs created using the libraries above.