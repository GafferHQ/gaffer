# Tutorial: Querying a Scene #

Gaffer has a simple API for querying the scenes that are output from nodes. In this tutorial we'll see how to use this API to traverse a scene hierarchy and examine its state.

Making a scene
--------------

First off, we'll create a simple scene using a network of basic nodes. Cut and paste the following into the Graph Editor to build the network. There's no need to worry about the details of this part - it's just a convenient way to create the network we need for the tutorial. If you do take a look though, you'll see examples of the commands needed to create nodes, set values and make connections.

```
import Gaffer
import GafferScene
import IECore

__children = {}

__children["Sphere"] = GafferScene.Sphere( "Sphere" )
root.addChild( __children["Sphere"] )
__children["Sphere"]["enabled"].setValue( True )
__children["Sphere"]["name"].setValue( 'sphere' )
__children["Sphere"]["transform"]["translate"]["x"].setValue( 0.0 )
__children["Sphere"]["transform"]["translate"]["y"].setValue( 1.0 )
__children["Sphere"]["transform"]["translate"]["z"].setValue( 0.0 )
__children["Sphere"]["transform"]["rotate"]["x"].setValue( 0.0 )
__children["Sphere"]["transform"]["rotate"]["y"].setValue( 0.0 )
__children["Sphere"]["transform"]["rotate"]["z"].setValue( 0.0 )
__children["Sphere"]["transform"]["scale"]["x"].setValue( 1.0 )
__children["Sphere"]["transform"]["scale"]["y"].setValue( 1.0 )
__children["Sphere"]["transform"]["scale"]["z"].setValue( 1.0 )
__children["Sphere"]["type"].setValue( 1 )
__children["Sphere"]["radius"].setValue( 1.0 )
__children["Sphere"]["zMin"].setValue( -1.0 )
__children["Sphere"]["zMax"].setValue( 1.0 )
__children["Sphere"]["thetaMax"].setValue( 360.0 )
__children["Sphere"]["divisions"]["x"].setValue( 20 )
__children["Sphere"]["divisions"]["y"].setValue( 40 )
__children["Sphere"].addChild( Gaffer.V2fPlug( "__uiPosition", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["Sphere"]["__uiPosition"]["x"].setValue( -9.311037063598633 )
__children["Sphere"]["__uiPosition"]["y"].setValue( 13.027215003967285 )
__children["Sphere"].addChild( Gaffer.V2fPlug( "__uiPosition1", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["Sphere"]["__uiPosition1"]["x"].setValue( 0.0 )
__children["Sphere"]["__uiPosition1"]["y"].setValue( 0.0 )
__children["Plane"] = GafferScene.Plane( "Plane" )
root.addChild( __children["Plane"] )
__children["Plane"]["enabled"].setValue( True )
__children["Plane"]["name"].setValue( 'plane' )
__children["Plane"]["transform"]["translate"]["x"].setValue( 0.0 )
__children["Plane"]["transform"]["translate"]["y"].setValue( 0.0 )
__children["Plane"]["transform"]["translate"]["z"].setValue( 0.0 )
__children["Plane"]["transform"]["rotate"]["x"].setValue( 90.0 )
__children["Plane"]["transform"]["rotate"]["y"].setValue( 0.0 )
__children["Plane"]["transform"]["rotate"]["z"].setValue( 0.0 )
__children["Plane"]["transform"]["scale"]["x"].setValue( 1.0 )
__children["Plane"]["transform"]["scale"]["y"].setValue( 1.0 )
__children["Plane"]["transform"]["scale"]["z"].setValue( 1.0 )
__children["Plane"]["dimensions"]["x"].setValue( 10.0 )
__children["Plane"]["dimensions"]["y"].setValue( 10.0 )
__children["Plane"]["divisions"]["x"].setValue( 2 )
__children["Plane"]["divisions"]["y"].setValue( 2 )
__children["Plane"].addChild( Gaffer.V2fPlug( "__uiPosition", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["Plane"]["__uiPosition"]["x"].setValue( -21.662202835083008 )
__children["Plane"]["__uiPosition"]["y"].setValue( 13.181886672973633 )
__children["Plane"].addChild( Gaffer.V2fPlug( "__uiPosition1", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["Plane"]["__uiPosition1"]["x"].setValue( 0.0 )
__children["Plane"]["__uiPosition1"]["y"].setValue( 0.0 )
__children["Group"] = GafferScene.Group( "Group" )
root.addChild( __children["Group"] )
__children["Group"]["enabled"].setValue( True )
__children["Group"]["name"].setValue( 'geometry' )
__children["Group"]["transform"]["translate"]["x"].setValue( 0.0 )
__children["Group"]["transform"]["translate"]["y"].setValue( 0.0 )
__children["Group"]["transform"]["translate"]["z"].setValue( 0.0 )
__children["Group"]["transform"]["rotate"]["x"].setValue( 0.0 )
__children["Group"]["transform"]["rotate"]["y"].setValue( 0.0 )
__children["Group"]["transform"]["rotate"]["z"].setValue( 0.0 )
__children["Group"]["transform"]["scale"]["x"].setValue( 1.0 )
__children["Group"]["transform"]["scale"]["y"].setValue( 1.0 )
__children["Group"]["transform"]["scale"]["z"].setValue( 1.0 )
__children["Group"].addChild( Gaffer.V2fPlug( "__uiPosition", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["Group"]["__uiPosition"]["x"].setValue( -15.069395065307617 )
__children["Group"]["__uiPosition"]["y"].setValue( 1.615199089050293 )
__children["Group"].addChild( Gaffer.V2fPlug( "__uiPosition1", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["Group"]["__uiPosition1"]["x"].setValue( 0.0 )
__children["Group"]["__uiPosition1"]["y"].setValue( 0.0 )
__children["Camera"] = GafferScene.Camera( "Camera" )
root.addChild( __children["Camera"] )
__children["Camera"]["enabled"].setValue( True )
__children["Camera"]["name"].setValue( 'camera' )
__children["Camera"]["transform"]["translate"]["x"].setValue( 0.0 )
__children["Camera"]["transform"]["translate"]["y"].setValue( 1.100000023841858 )
__children["Camera"]["transform"]["translate"]["z"].setValue( 5.300000190734863 )
__children["Camera"]["transform"]["rotate"]["x"].setValue( 0.0 )
__children["Camera"]["transform"]["rotate"]["y"].setValue( 0.0 )
__children["Camera"]["transform"]["rotate"]["z"].setValue( 0.0 )
__children["Camera"]["transform"]["scale"]["x"].setValue( 1.0 )
__children["Camera"]["transform"]["scale"]["y"].setValue( 1.0 )
__children["Camera"]["transform"]["scale"]["z"].setValue( 1.0 )
__children["Camera"]["projection"].setValue( 'perspective' )
__children["Camera"]["fieldOfView"].setValue( 50.0 )
__children["Camera"]["clippingPlanes"]["x"].setValue( 0.009999999776482582 )
__children["Camera"]["clippingPlanes"]["y"].setValue( 100000.0 )
__children["Camera"].addChild( Gaffer.V2fPlug( "__uiPosition", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["Camera"]["__uiPosition"]["x"].setValue( 3.1233882904052734 )
__children["Camera"]["__uiPosition"]["y"].setValue( 13.14145278930664 )
__children["Camera"].addChild( Gaffer.V2fPlug( "__uiPosition1", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["Camera"]["__uiPosition1"]["x"].setValue( 0.0 )
__children["Camera"]["__uiPosition1"]["y"].setValue( 0.0 )
__children["Group1"] = GafferScene.Group( "Group1" )
root.addChild( __children["Group1"] )
__children["Group1"]["enabled"].setValue( True )
__children["Group1"]["name"].setValue( 'world' )
__children["Group1"]["transform"]["translate"]["x"].setValue( 0.0 )
__children["Group1"]["transform"]["translate"]["y"].setValue( 0.0 )
__children["Group1"]["transform"]["translate"]["z"].setValue( 0.0 )
__children["Group1"]["transform"]["rotate"]["x"].setValue( 0.0 )
__children["Group1"]["transform"]["rotate"]["y"].setValue( 0.0 )
__children["Group1"]["transform"]["rotate"]["z"].setValue( 0.0 )
__children["Group1"]["transform"]["scale"]["x"].setValue( 1.0 )
__children["Group1"]["transform"]["scale"]["y"].setValue( 1.0 )
__children["Group1"]["transform"]["scale"]["z"].setValue( 1.0 )
__children["Group1"].addChild( Gaffer.V2fPlug( "__uiPosition", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["Group1"]["__uiPosition"]["x"].setValue( -8.414341926574707 )
__children["Group1"]["__uiPosition"]["y"].setValue( -9.591415405273438 )
__children["Group1"].addChild( Gaffer.V2fPlug( "__uiPosition1", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["Group1"]["__uiPosition1"]["x"].setValue( 0.0 )
__children["Group1"]["__uiPosition1"]["y"].setValue( 0.0 )
__children["StandardOptions"] = GafferScene.StandardOptions( "StandardOptions" )
root.addChild( __children["StandardOptions"] )
__children["StandardOptions"]["enabled"].setValue( True )
__children["StandardOptions"]["options"]["renderCamera"]["name"].setValue( 'render:camera' )
__children["StandardOptions"]["options"]["renderCamera"]["value"].setValue( '/world/camera' )
__children["StandardOptions"]["options"]["renderCamera"]["enabled"].setValue( True )
__children["StandardOptions"]["options"]["renderResolution"]["name"].setValue( 'render:resolution' )
__children["StandardOptions"]["options"]["renderResolution"]["value"]["x"].setValue( 1024 )
__children["StandardOptions"]["options"]["renderResolution"]["value"]["y"].setValue( 778 )
__children["StandardOptions"]["options"]["renderResolution"]["enabled"].setValue( True )
__children["StandardOptions"]["options"]["transformBlur"]["name"].setValue( 'render:transformBlur' )
__children["StandardOptions"]["options"]["transformBlur"]["value"].setValue( False )
__children["StandardOptions"]["options"]["transformBlur"]["enabled"].setValue( False )
__children["StandardOptions"]["options"]["deformationBlur"]["name"].setValue( 'render:deformationBlur' )
__children["StandardOptions"]["options"]["deformationBlur"]["value"].setValue( False )
__children["StandardOptions"]["options"]["deformationBlur"]["enabled"].setValue( False )
__children["StandardOptions"]["options"]["shutter"]["name"].setValue( 'render:shutter' )
__children["StandardOptions"]["options"]["shutter"]["value"]["x"].setValue( -0.25 )
__children["StandardOptions"]["options"]["shutter"]["value"]["y"].setValue( 0.25 )
__children["StandardOptions"]["options"]["shutter"]["enabled"].setValue( False )
__children["StandardOptions"].addChild( Gaffer.V2fPlug( "__uiPosition", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["StandardOptions"]["__uiPosition"]["x"].setValue( -6.914341926574707 )
__children["StandardOptions"]["__uiPosition"]["y"].setValue( -26.473411560058594 )
__children["StandardOptions"].addChild( Gaffer.V2fPlug( "__uiPosition1", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["StandardOptions"]["__uiPosition1"]["x"].setValue( 0.0 )
__children["StandardOptions"]["__uiPosition1"]["y"].setValue( 0.0 )
__children["CustomAttributes"] = GafferScene.CustomAttributes( "CustomAttributes" )
root.addChild( __children["CustomAttributes"] )
__children["CustomAttributes"]["enabled"].setValue( True )
__children["CustomAttributes"]["attributes"].addChild( Gaffer.CompoundDataPlug.MemberPlug( "member1", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["CustomAttributes"]["attributes"]["member1"].addChild( Gaffer.StringPlug( "name", defaultValue = '', flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["CustomAttributes"]["attributes"]["member1"]["name"].setValue( 'myString' )
__children["CustomAttributes"]["attributes"]["member1"].addChild( Gaffer.StringPlug( "value", defaultValue = '', flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["CustomAttributes"]["attributes"]["member1"]["value"].setValue( 'aaa' )
__children["CustomAttributes"]["attributes"]["member1"].addChild( Gaffer.BoolPlug( "enabled", defaultValue = True, flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["CustomAttributes"]["attributes"]["member1"]["enabled"].setValue( True )
__children["CustomAttributes"].addChild( Gaffer.V2fPlug( "__uiPosition", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["CustomAttributes"]["__uiPosition"]["x"].setValue( -6.914341926574707 )
__children["CustomAttributes"]["__uiPosition"]["y"].setValue( -18.878076553344727 )
__children["CustomAttributes"].addChild( Gaffer.V2fPlug( "__uiPosition1", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["CustomAttributes"]["__uiPosition1"]["x"].setValue( 0.0 )
__children["CustomAttributes"]["__uiPosition1"]["y"].setValue( 0.0 )
__children["PathFilter"] = GafferScene.PathFilter( "PathFilter" )
root.addChild( __children["PathFilter"] )
__children["PathFilter"]["paths"].setValue( IECore.StringVectorData( [ "/world/geometry/sphere" ] ) )
__children["PathFilter"].addChild( Gaffer.V2fPlug( "__uiPosition", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["PathFilter"]["__uiPosition"]["x"].setValue( 3.9433956146240234 )
__children["PathFilter"]["__uiPosition"]["y"].setValue( -9.495070457458496 )
__children["PathFilter"].addChild( Gaffer.V2fPlug( "__uiPosition1", flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Serialisable | Gaffer.Plug.Flags.AcceptsInputs | Gaffer.Plug.Flags.PerformsSubstitutions | Gaffer.Plug.Flags.Cacheable, ) )
__children["PathFilter"]["__uiPosition1"]["x"].setValue( 0.0 )
__children["PathFilter"]["__uiPosition1"]["y"].setValue( 0.0 )
__children["Group"]["in"][0].setInput( __children["Plane"]["out"] )
__children["Group"]["in"][1].setInput( __children["Sphere"]["out"] )
__children["Group1"]["in"][0].setInput( __children["Group"]["out"] )
__children["Group1"]["in"][1].setInput( __children["Camera"]["out"] )
__children["StandardOptions"]["in"].setInput( __children["CustomAttributes"]["out"] )
__children["CustomAttributes"]["in"].setInput( __children["Group1"]["out"] )
__children["CustomAttributes"]["filter"].setInput( __children["PathFilter"]["out"] )


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
print type( g )
print g.keys()
print g["option:render:camera"].value
print g["option:render:resolution"].value
```

There are a couple of things to note here. Firstly, although the out plug appears as a single plug in the Graph Editor, it actually has several child plugs, which allow different aspects of the scene to be queried. We accessed the `globals` plug using dictionary syntax, and then retrieved its value using the `getValue()` method. The result was an `IECore::CompoundObject` which we can pretty much treat like a dictionary, with the minor annoyance that we need to use `.value` to actually retrieve the final value we want.

The `option:render:camera` globals entry tells us that the user wants to render through a camera called `/world/camera`, so let's try to retrieve the object representing the camera. Just as the globals within the scene were represented by a `globals` plug, the objects are represented by an `object` plug. Maybe we can get the camera out using a simple `getValue()` call as before?

```
g = root["StandardOptions"]["out"]["object"].getValue()
RuntimeError : line 1 : Exception : Context has no entry named "scene:path"
```

That didn't work out so well did it? The problem is that whereas the globals are **global**, different objects are potentially available at each point in the scene hierarchy - we need to say which part of the hierarchy we want the object from. We do that as follows :

```
with Gaffer.Context( root.context() ) as context :
	context["scene:path"] = IECore.InternedStringVectorData( [ 'world', 'camera' ] )
	camera = root["StandardOptions"]["out"]["object"].getValue()
	print camera
```

The `Context` class is central to the way Gaffer works - a single plug can output entirely different values depending on the [Context](../../WorkingWithTheNodeGraph/Contexts/index.md) in which `getValue()` is called. Here we provided a Context as a path within the scene, but for an image node we'd provide a Context with a tile location and channel name. Contexts allow Gaffer to multithread efficiently - each thread uses it's own Context so each thread can be querying a different part of the scene or a different location in an image. That was a bit wordy though wasn't it? For now let's pretend we didn't even take this detour and let's use a utility method that does the same thing instead :

```
camera = root["StandardOptions"]["out"].object( "/world/camera" )
```

Much better. Let's take a look at what we got :

```
print camera.parameters().keys()
print camera.parameters()["projection"].value
print camera.parameters()["projection:fov"].value
print camera.parameters()["clippingPlanes"].value
```

Again, the camera looks a lot like a dictionary, so queries aren't too hard.

Further queries
---------------

Having our camera is all well and good, but we don't know where it is located spatially. It might come as no surprise to find that transforms are represented as another child plug alongside `globals` and `object`, and that we can query it in the same way. This time we'll skip that pesky Context stuff entirely, and use another utility method :

```
transform = root["StandardOptions"]["out"].transform( "/world/camera" )
print transform
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
print a.keys()
print a["myString"].value
```

If the sphere had a shader assigned to it, that would appear as `a["shader"]`, but we've deliberately left that out for now to keep this tutorial renderer agnostic.

Traversing the hierarchy
------------------------

One of the key features of the queries above was that they were random access - we could query any location in the scene at any time, without needing to query the parent locations first. That's all well and good, but until now we've been using prior knowledge of the scene structure to decide what to query. In a real situation, our code doesn't know that `/world/geometry/sphere` even exists. We need a means of querying the structure of the scene first, so that we can then query the contents at each location. Oddly enough, the structure is just communicated with another plug alongside the others - this time one called `childNames`. And oddly enough, there's a utility method to help us get its value within the proper Context. Let's start at the root and see what we can find :

```
print root["StandardOptions"]["out"].childNames( "/" )
print root["StandardOptions"]["out"].childNames( "/world" )
```

Rather than continue this manual exploration, let's write a simple recursive function to traverse the scene and print what it finds :

```
import os

def visit( scene, path ) :

	print path
	print "\tTransform : " + str( scene.transform( path ) )
	print "\tObject : " + scene.object( path ).typeName()
	print "\tAttributes : " + " ".join( scene.attributes( path ).keys() )
	print "\tBound : " + str( scene.bound( path ) ) + "\n"
	for childName in scene.childNames( path ) :
		visit( scene, os.path.join( path, str( childName )  ) )

visit( root["StandardOptions"]["out"], "/" )
```

That's pretty much all there is to it. There's a little more to learn in terms of the APIs for the particular Cortex objects that might be returned by a query, but the above examples hopefully provide a good starting point for exploration.

## See also ##

- [The Python Editor](../ThePythonEditor/index.md)
- [Context](../../WorkingWithTheNodeGraph/Contexts/index.md)
