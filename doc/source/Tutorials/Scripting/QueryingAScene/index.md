# Tutorial: Querying a Scene #

Gaffer's scripting flexibility allows you to query the scene's parameters and objects as it flows through the node graph. In this tutorial, we will demonstrate how to use Gaffer's API to reference various scene parameters and traverse the scene hierarchy. We will cover the following:

- The main `out` plug
- Referencing the `globals` scene plug and its values
- Using the utility methods for returning various scene properties:
    - `object()` method, for returning a scene object
    - `parameters()` method, for returning an object's scene parameters
    - `transform()` method, for returning an object's local scene transform
    - `fullTransform()` method, for returning an object's global scene transform
    - `attributes()` method, for returning an object's scene attributes
    - `childNames()` method, for returning the children of a scene location
- Traversing the scene locations

Before continuing, we highly recommend you complete the [Scripting Basics tutorial](../GettingStarted/index.md).

Before you start, load the following script from the Gaffer resources folder: `gaffer-!GAFFER_VERSION!-linux/resources/scripts/queryingScene.gfr`. This simple script contains two grouped geometry primitives and a camera, some global scene options, and some additional scene location properties.


## Scene Queries ##

In this first section, we will demonstrate how to reference scene objects and various global scene options.


### The "out" plug ###

Gaffer's scene nodes pass the scene down through the graph through their primary `out` plug (represented in the _Graph Editor_ as the _out_ plug at the bottom of the node). The `out` plug will be your gateway to all scene queries. Although the _out_ plug appears as a single plug in the _Graph Editor_, it is actually a [compound plug](../CompoundPlugs/index.md) with several child plugs.


### Querying scene global options ###

One of the `out` plug's children is the `globals` plug, which has as its value an IECore.CompoundObject() class, which in turn contains a dictionary. Each key in this dictionary corresponds to a global setting added by an Option node. As with other plugs, you can use the `getValue()` method on the `globals` plug to retrieve this dictionary:

![Global scene options, in the Script Editor's output](images/scriptOutputCompoundObject.png "Global scene options, in the Script Editor's output")

Since this is a dictionary, you will not be able to use `getValue()` to retrieve its key values. Instead, Python dictionary syntax comes into play.

> Tip :
> For plugs with dictionaries, use the `dictionary.keys()` method to retrieve a list of all the keys, and the `dictionary["key"].value` method to retrieve a value.

Try putting all of this into practice for your first query, which will retrieve the scene's global settings:

```python
globals = script["StandardOptions"]["out"]["globals"].getValue()
print type( globals )
print globals.keys()
print globals["option:render:camera"].value
print globals["option:render:resolution"].value
```

![Global settings, in the Script Editor's output](images/scriptOutputGlobals.png "Global settings, in the Script Editor's output")


### Querying an object ###

The `out` plug contains a corresponding `object` child plug for objects. While it would be logical to try and grab an object by its location from it, unfortunately objects cannot easily be referenced using this plug without specifying a [scene context](../SceneContext/index.md). The simple workaround is to ignore the `object` plug and instead use the `object()` method on the `out` plug:

```python
camera = script["StandardOptions"]["out"].object( "/world/camera" )
print camera
```

![Camera's scene object, in the Script Editor's output](images/scriptOutputCameraObject.png "Camera's scene object, in the Script Editor's output")


### Querying an object's parameters ###

An object's scene parameters are also a dictionary, with a key for each parameter. Once again, due to the extra work involved with accessing scene contexts, the best way to handle the dictionary is through a special method, this time the `parameters()` method. As before, its keys and values are accessed with standard Python syntax. Try the following:

```python
print camera.parameters().keys()
print camera.parameters()["projection"].value
print camera.parameters()["projection:fov"].value
print camera.parameters()["clippingPlanes"].value
```

![Camera object parameters, in the Script Editor's output](images/scriptOutputCameraObjectParameters.png "Camera object parameters, in the Script Editor's output")


### Querying an object's transform ###

Referencing the camera object and its parameters is a start, but we don't know where it is located spatially. Scene transforms (not to be confused with the node's transform plugs) are represented as another child plug of `out`. Again, there is a special utility method for retrieving it, in this case the `transform()` method:

```python
transform = script["StandardOptions"]["out"].transform( "/world/camera" )
print transform
```

![Camera object transform, in the Script Editor's output](images/scriptOutputCameraObjectTransform.png "Camera object transform, in the Script Editor's output")

That returned the **local** scene transform for the camera object as a matrix. The `fullTransform()` method is also available, for providing the **global** scene transform.


### Querying custom attributes ###

The CustomAttributes node, as indicated by its name, adds user-defined global attributes to the scene. In keeping with the rest of the `out` plug's children, the scene's attributes are kept as a dictionary in an `attributes` child plug. Yet again, there is a special `attributes()` method for retrieving this dictionary:

```python
attributes = script["StandardOptions"]["out"].attributes( "/world/geometry/sphere" )
print attributes.keys()
print attributes["myString"].value
```

![Custom attributes, in the Script Editor's output](images/scriptOutputCustomAttributes.png "Custom attributes, Script Editor's output")

<!-- TODO: ? If the sphere had a shader assigned to it, that would appear as `a["shader"]`, but we've deliberately left that out for now to keep this tutorial renderer agnostic. -->


## Traversing the Hierarchy ##

An important condition of the previous section's queries to consider was that they were accessed somewhat unrealistically. In the above code samples, we already knew the hierarchy and locations of the scene prior to querying it. In a real-world script, it is unlikely you will have this knowledge, and your code will not know by default, for instance, that the `/world/geometry/sphere` scene location exists. For real-world scripts, you will require a means of first querying the real scene locations prior to querying the scene objects.

### Traversing individual scene locations ###

The full scene hierarchy is kept in the `out` plug's `childNames` child plug. As before, it contains a dictionary, with keys for each location. Also as before, it has a corresponding utility method, `childNames()`, which will return a list of the names of child locations **one level below** the path you provide as input.

Start at the first two levels of the script's scene hierarchy:

```python
print script["StandardOptions"]["out"].childNames( "/" )
print script["StandardOptions"]["out"].childNames( "/world" )
```

![First two levels of scene traversal, output in the Script Editor's output](images/scriptOutputTraversal.png "First two levels of scene traversal, in the Script Editor's output")


### An automatic traversal script ###

Rather than limiting you to manual traversal, use this simple recursive function that traverses the scene for every child location, and outputs some useful scene properties for each location it finds:

```python
import os

def visit( scene, path ) :

	print path
	print "\tTransform : " + str( scene.transform( path ) )
	print "\tObject : " + scene.object( path ).typeName()
	print "\tAttributes : " + " ".join( scene.attributes( path ).keys() )
	print "\tBound : " + str( scene.bound( path ) ) + "\n"
	for childName in scene.childNames( path ) :
		visit( scene, os.path.join( path, str( childName )  ) )

visit( script["StandardOptions"]["out"], "/" )
```

![Full scene traversal, in the Script Editor's output](images/scriptOutputFullTraversal.png "Full scene traversal, in the Script Editor's output")


## Recap ##

You should know have a decent understanding of how Gaffer handles scenes:
- Each scene node outputs the scene through its `out` plug, which has a number of child plugs, corresponding to most of the standard scene properties.
- Each of these child plugs has a dictionary containing its values.
- Gaffer provides a specific utility method to retrieve each of the different dictionaries.

<!-- TODO: ? There's a little more to learn in terms of the APIs for the particular Cortex objects that might be returned by a query,  -->


## See Also ##

- [Using the Script Editor](../ScriptEditor/index.md)
- [Script Files](../ScriptFiles/index.md)
