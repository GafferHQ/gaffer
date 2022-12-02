# Tutorial: Querying a Scene #

Gaffer has a simple API for querying the scenes that are output from nodes. In this tutorial we'll see how to use this API to traverse a scene hierarchy and examine its state.

Making a scene
--------------

First off, we'll create a simple scene using a network of basic nodes. Cut and paste the following into the Graph Editor to build the network. There's no need to worry about the details of this part - it's just a convenient way to create the network we need for the tutorial. If you do take a look though, you'll see examples of the commands needed to create nodes, set values and make connections.

```
import Gaffer
import GafferScene
import IECore
import imath

__children = {}

__children["Sphere"] = GafferScene.Sphere( "Sphere" )
parent.addChild( __children["Sphere"] )
__children["Sphere"].addChild( Gaffer.V2fPlug( "__uiPosition", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["Sphere"].addChild( Gaffer.V2fPlug( "__uiPosition1", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["Plane"] = GafferScene.Plane( "Plane" )
parent.addChild( __children["Plane"] )
__children["Plane"].addChild( Gaffer.V2fPlug( "__uiPosition", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["Plane"].addChild( Gaffer.V2fPlug( "__uiPosition1", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["Group"] = GafferScene.Group( "Group" )
parent.addChild( __children["Group"] )
__children["Group"]["in"].addChild( GafferScene.ScenePlug( "in1", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["Group"]["in"].addChild( GafferScene.ScenePlug( "in2", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["Group"].addChild( Gaffer.V2fPlug( "__uiPosition", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["Group"].addChild( Gaffer.V2fPlug( "__uiPosition1", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["Camera"] = GafferScene.Camera( "Camera" )
parent.addChild( __children["Camera"] )
__children["Camera"].addChild( Gaffer.V2fPlug( "__uiPosition", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["Camera"].addChild( Gaffer.V2fPlug( "__uiPosition1", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["Group1"] = GafferScene.Group( "Group1" )
parent.addChild( __children["Group1"] )
__children["Group1"]["in"].addChild( GafferScene.ScenePlug( "in1", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["Group1"]["in"].addChild( GafferScene.ScenePlug( "in2", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["Group1"].addChild( Gaffer.V2fPlug( "__uiPosition", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["Group1"].addChild( Gaffer.V2fPlug( "__uiPosition1", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["StandardOptions"] = GafferScene.StandardOptions( "StandardOptions" )
parent.addChild( __children["StandardOptions"] )
__children["StandardOptions"].addChild( Gaffer.V2fPlug( "__uiPosition", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["StandardOptions"].addChild( Gaffer.V2fPlug( "__uiPosition1", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["CustomAttributes"] = GafferScene.CustomAttributes( "CustomAttributes" )
parent.addChild( __children["CustomAttributes"] )
__children["CustomAttributes"]["attributes"].addChild( Gaffer.NameValuePlug( "", Gaffer.StringPlug( "value", defaultValue = '', flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ), True, "member1", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
__children["CustomAttributes"].addChild( Gaffer.V2fPlug( "__uiPosition", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["CustomAttributes"].addChild( Gaffer.V2fPlug( "__uiPosition1", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["PathFilter"] = GafferScene.PathFilter( "PathFilter" )
parent.addChild( __children["PathFilter"] )
__children["PathFilter"].addChild( Gaffer.V2fPlug( "__uiPosition", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["PathFilter"].addChild( Gaffer.V2fPlug( "__uiPosition1", defaultValue = imath.V2f( 0, 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
__children["Sphere"]["transform"]["translate"].setValue( imath.V3f( 0, 1, 0 ) )
__children["Sphere"]["__uiPosition"].setValue( imath.V2f( 8.01966095, 9.80717945 ) )
__children["Plane"]["transform"]["rotate"].setValue( imath.V3f( 90, 0, 0 ) )
__children["Plane"]["dimensions"].setValue( imath.V2f( 10, 10 ) )
__children["Plane"]["divisions"].setValue( imath.V2i( 2, 2 ) )
__children["Plane"]["__uiPosition"].setValue( imath.V2f( -4.33150482, 9.96185112 ) )
__children["Group"]["in"][0].setInput( __children["Plane"]["out"] )
__children["Group"]["in"][1].setInput( __children["Sphere"]["out"] )
__children["Group"]["name"].setValue( 'geometry' )
__children["Group"]["__uiPosition"].setValue( imath.V2f( 2.26130295, -1.60483646 ) )
__children["Camera"]["transform"]["translate"].setValue( imath.V3f( 0, 1.10000002, 5.30000019 ) )
__children["Camera"]["__uiPosition"].setValue( imath.V2f( 20.4540863, 9.92141724 ) )
__children["Group1"]["in"][0].setInput( __children["Group"]["out"] )
__children["Group1"]["in"][1].setInput( __children["Camera"]["out"] )
__children["Group1"]["name"].setValue( 'world' )
__children["Group1"]["__uiPosition"].setValue( imath.V2f( 8.91635609, -12.811451 ) )
__children["StandardOptions"]["in"].setInput( __children["CustomAttributes"]["out"] )
__children["StandardOptions"]["options"]["renderCamera"]["value"].setValue( '/world/camera' )
__children["StandardOptions"]["options"]["renderCamera"]["enabled"].setValue( True )
__children["StandardOptions"]["options"]["renderResolution"]["enabled"].setValue( True )
__children["StandardOptions"]["__uiPosition"].setValue( imath.V2f( 10.4163561, -29.6934471 ) )
__children["CustomAttributes"]["in"].setInput( __children["Group1"]["out"] )
__children["CustomAttributes"]["filter"].setInput( __children["PathFilter"]["out"] )
__children["CustomAttributes"]["attributes"]["member1"]["name"].setValue( 'myString' )
__children["CustomAttributes"]["attributes"]["member1"]["value"].setValue( 'aaa' )
__children["CustomAttributes"]["__uiPosition"].setValue( imath.V2f( 10.4163561, -22.0981121 ) )
__children["PathFilter"]["paths"].setValue( IECore.StringVectorData( [ '/world/geometry/sphere' ] ) )
__children["PathFilter"]["__uiPosition"].setValue( imath.V2f( 21.2740936, -12.715106 ) )

del __children
```

Our first scene queries
-----------------------

Scenes are output from nodes through the out plug found at the bottom of each node. We make queries by calling methods of this plug. To refer to the plug in the Python Editor, we can either type a reference to it in directly, or middle-mouse drag it from the Graph Editor to the Python Editor. To query the output of the StandardOptions node we'll be using the following :

```
root["StandardOptions"]["out"]
```

Note that we're just using Python dictionary syntax to access a node by name and then to access a named plug within it. This plug is the gateway to our queries, so let's make our first query by getting the global settings from within the scene - these are settings created by the various Options nodes.

```
g = root["StandardOptions"]["out"]["globals"].getValue()
print( type( g ) )
print( g.keys() )
print( g["option:render:camera"].value )
print( g["option:render:resolution"].value )
```

There are a couple of things to note here. Firstly, although the out plug appears as a single plug in the Graph Editor, it actually has several child plugs, which allow different aspects of the scene to be queried. We accessed the `globals` plug using dictionary syntax, and then retrieved its value using the `getValue()` method. The result was an `IECore::CompoundObject` which we can pretty much treat like a dictionary, with the minor annoyance that we need to use `.value` to actually retrieve the final value we want.

The `option:render:camera` globals entry tells us that the user wants to render through a camera called `/world/camera`, so let's try to retrieve the object representing the camera. Just as the globals within the scene were represented by a `globals` plug, the objects are represented by an `object` plug. Maybe we can get the camera out using a simple `getValue()` call as before?

```
g = root["StandardOptions"]["out"]["object"].getValue()
Gaffer.ProcessException : line 1 : Group1.out.object : Context has no variable named "scene:path"
```

That didn't work out so well did it? The problem is that whereas the globals are **global**, different objects are potentially available at each point in the scene hierarchy - we need to say which part of the hierarchy we want the object from. We do that as follows :

```
with Gaffer.Context( root.context() ) as context :
	context["scene:path"] = IECore.InternedStringVectorData( [ 'world', 'camera' ] )
	camera = root["StandardOptions"]["out"]["object"].getValue()
	print( camera )
```

The `Context` class is central to the way Gaffer works - a single plug can output entirely different values depending on the [Context](../../WorkingWithTheNodeGraph/Contexts/index.md) in which `getValue()` is called. Here we provided a Context as a path within the scene, but for an image node we'd provide a Context with a tile location and channel name. Contexts allow Gaffer to multithread efficiently - each thread uses it's own Context so each thread can be querying a different part of the scene or a different location in an image. That was a bit wordy though wasn't it? For now let's pretend we didn't even take this detour and let's use a utility method that does the same thing instead :

```
camera = root["StandardOptions"]["out"].object( "/world/camera" )
```

Much better. Let's take a look at what we got :

```
print( camera.parameters().keys() )
print( camera.parameters()["projection"].value )
print( camera.parameters()["focalLength"].value )
print( camera.parameters()["clippingPlanes"].value )
```

Again, the camera looks a lot like a dictionary, so queries aren't too hard.

Further queries
---------------

Having our camera is all well and good, but we don't know where it is located spatially. It might come as no surprise to find that transforms are represented as another child plug alongside `globals` and `object`, and that we can query it in the same way. This time we'll skip that pesky Context stuff entirely, and use another utility method :

```
transform = root["StandardOptions"]["out"].transform( "/world/camera" )
print( transform )
```

That gave us the local transform for the camera in the form of a matrix - we could also use the `fullTransform()` method if we wanted the global transform.

That's about all we want to know about the camera, but what about that sphere? Does it have any properties we might be interested in? We should be able to guess by now that we can get at the object and transform in the same way as we did for the camera :

```
sphereObject = root["StandardOptions"]["out"].object( "/world/geometry/sphere" )
sphereTransform = root["StandardOptions"]["out"].transform( "/world/geometry/sphere" )
```

But what about the CustomAttributes node that was applied to the sphere? How can we query what that did? Not surprisingly, the attributes of the sphere are retrieved via an `attributes` plug, or for the lazy Context dodgers amongst us, an `attributes()` utility method :

```
a = root["StandardOptions"]["out"].attributes( "/world/geometry/sphere" )
print( a.keys() )
print( a["myString"].value )
```

If the sphere had a shader assigned to it, that would appear as `a["shader"]`, but we've deliberately left that out for now to keep this tutorial renderer agnostic.

Traversing the hierarchy
------------------------

One of the key features of the queries above was that they were random access - we could query any location in the scene at any time, without needing to query the parent locations first. That's all well and good, but until now we've been using prior knowledge of the scene structure to decide what to query. In a real situation, our code doesn't know that `/world/geometry/sphere` even exists. We need a means of querying the structure of the scene first, so that we can then query the contents at each location. Oddly enough, the structure is just communicated with another plug alongside the others - this time one called `childNames`. And oddly enough, there's a utility method to help us get its value within the proper Context. Let's start at the root and see what we can find :

```
print( root["StandardOptions"]["out"].childNames( "/" ) )
print( root["StandardOptions"]["out"].childNames( "/world" ) )
```

Rather than continue this manual exploration, let's write a simple recursive function to traverse the scene and print what it finds :

```
def visit( scene, path ) :

	print( path )
	print( "\tTransform : " + str( scene.transform( path ) ) )
	print( "\tObject : " + scene.object( path ).typeName() )
	print( "\tAttributes : " + " ".join( scene.attributes( path ).keys() ) )
	print( "\tBound : " + str( scene.bound( path ) ) + "\n" )
	for childName in scene.childNames( path ) :
		visit( scene, path.rstrip( "/" ) + "/" + str( childName ) )

visit( root["StandardOptions"]["out"], "/" )
```

That's pretty much all there is to it. There's a little more to learn in terms of the APIs for the particular Cortex objects that might be returned by a query, but the above examples hopefully provide a good starting point for exploration.

## See also ##

- [The Python Editor](../ThePythonEditor/index.md)
- [Context](../../WorkingWithTheNodeGraph/Contexts/index.md)
