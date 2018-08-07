# Tutorial: Scripting Basics #

In this tutorial, we will give you a first taste of Python scripting in Gaffer. Gaffer's Python scripting API is fairly frugal, so learning a few fundamental concepts will go a long way. Here we'll take a quick tour through these fundamentals using the [_Script Editor_](../../../Reference/UIReference/ScriptEditor/index.md) in the main Gaffer application. We will cover the following topics:

- Using the _Script Editor_
- Dragging and dropping references and values into the _Script Editor_
- Creating nodes and plugs in script
- Referencing nodes in script
- Editing node values and connections in script

> Note :
> For this tutorial, we will assume you are familiar with scripting in Python.


## "Hello, World!" and the _Script Editor_ ##

Gaffer's _Script Editor_ lets you build and modify the node graph, edit and adjust the underlying code of your script (your project file), test expressions, and display results. By default, you can find the _Script Editor_ in the bottom-right panel, in a tab next to the _Scene Hierarchy_.

![The Script Editor](images/scriptEditorEmpty.png "The Script Editor")

The text field in the bottom-half is for inputting code, and behaves like a typical text editor: type, copy-paste, and enter new lines as you normally would. The top-half is a readout that displays the code you execute and any resulting output.

Try executing a "Hello, World!" command:

1. Type `print "Hello, World!"` into the input field.

2. Hit <kbd>Control</kbd> + <kbd>Enter</kbd> to execute the code.

![The Script Editor with “Hello, World!”](images/scriptEditorHello.png "The Script Editor with “Hello, World!”")

<!-- > Tip :-->
<!-- > When you execute code, the contents of the input field will be erased. However, if you first highlight the code prior to executing it, the code you entered will remain in the field. -->


## Scripting Basics with a Generic Node ##

In this first section, we will cover the most basic operations for scripting nodes and plugs in Python, using a generic node as an example.


### Creating a node ###

Each node in the scripting API is a Python class.

First, try creating a node of the generic node class:

```python
script.addChild( Gaffer.Node() )
```

![Generic node in the Graph Editor](images/graphEditorGenericNode.png "Generic node in the Graph Editor")

Notice that you added the node to the generic `script` variable.

> Important :
> The `script` variable references the root of the node graph. All nodes are added to it.


### Referencing nodes ###

Since the above code did not assign a variable to your node, you do not yet have a convenient handle for referring to it. There is a simple way to retrieve the script reference to any existing node – dragging and dropping from the _Graph Editor:_

1. Middle-click and drag the node from the _Graph Editor_. Your cursor will change to ![the node icon](images/nodeMiddleClick.png "The node icon").

2. Drop the selection onto the input field of the _Script Editor_. The reference will be `script["Node"]`.

3. Add a variable declaration to the beginning of the line: `myNode = script["Node"]`.

4. Execute the code.

The `myNode` variable will now reference your generic node.


### Changing a node value ###

Like any Python class, nodes have methods.

Try using your variable in conjunction with the `setName()` method to changes its name:

```python
myNode.setName( "MyVeryFirstNode" )
```

![Renamed generic node in the Graph Editor](images/graphEditorGenericNodeRenamed.png "Renamed generic node in the Graph Editor")

There are several other methods for manipulating nodes. A complete list can be found in the [Node Operations reference](../../../Reference/ScriptingReference/CommonOperations/index.md).


### Adding a plug ###

Plugs are also Python classes, and are added to nodes themselves using the same `addChild()` method.

Try adding an integer plug and a floating point plug to your generic node:

```python
myNode.addChild( Gaffer.IntPlug() )
myNode.addChild( Gaffer.FloatPlug() )
```

In the _Graph Editor_, your node will now have two dots on top of its box, indicating it has two plugs.

![MyVeryFirstNode with two plugs in the Graph Editor](images/graphEditorGenericNodeTwoPlugs.png "MyVeryFirstNode with two plugs in the Graph Editor")

<!-- TODO: link to generic plug types reference, once it is created -->


### Modifying the _Graph Editor_ selection ###

Gaffer's API allows access, modification, and creation of its interface's objects and methods. One interface-related object that can be manipulated is the selection in the _Graph Editor_, referred to by the `script.selection()` object.

Try selecting your generic node:

```python
script.selection().clear()
script.selection().add( myNode )
```

The node is now selected, and you can see it in the _Node Editor_.

![MyVeryFirstNode in the Node Editor](images/nodeEditorGenericNode.png "MyVeryFirstNode in the Node Editor")

<!-- TODO: link to interface classes and methods reference (once the article is created) -->


### Referencing plugs ###

Like nodes, a reference to a plug can also be inserted into the _Script Editor_ by dragging and dropping.

Try inserting a reference to your generic node's integer plug, and give it a variable:

1. If your node is not selected, select it.

2. Click and drag the _Int Plug's_ **label** (not its value field) from the _Node Editor_. Your cursor will change to ![a plug](images/plug.png "A plug").

3. Drop the selection onto the input field of the _Script Editor_. The reference will be `script["Node"]["IntPlug"]`.

4. Add a variable declaration to the beginning of the line: `myPlug = script["Node"]["IntPlug"]`.

5. Execute the code.

You will now be able to reference the integer plug with the `myPlug` variable.


### Deleting nodes and plugs ###

As with their method for creation, nodes and plugs have a complementary `removeChild()` method for deletion.

Remove the integer plug from your generic node and delete its variable (just to be safe):

```python
myNode.removeChild( myPlug )
del myPlug
```

The plug will disappear from the _Node Editor_, and there will be only one visible plug in the _Graph Editor_.

![MyVeryFirstNode with one plug in the Graph Editor](images/graphEditorGenericNodeOnePlug.png "MyVeryFirstNode with one plug in the Graph Editor")

Unfortunately, your generic node will not be of much use for the rest of the tutorial. Before continuing, delete it too:

```python
script.removeChild( myNode )
del myNode
```

That covers the most basic scripting tasks in Gaffer. Hopefully, you will be beginning to develop a sense of Gaffer's power and flexibility from the ability to accomplish all that you can in the interface through the scripting API.


## Brief Aside: On References and Dictionary Notation##

Before continuing, there's an important distinction that needs to be made with regards to referencing nodes. The previous code examples used mixed references, by using a variable to refer to nodes and Python dictionary notation to refer to plugs. They are effectively the same, but the mixed syntax might cause a great deal of confusion at first.

Consider the previous section's node `MyVeryFirstNode` (and the `myNode` variable) with its plug `IntPlug` (and the `myPlug` variable). Referring to the node's variable and dictionary entry are one and the same:

```python
script["MyVeryFirstNode"] # Gaffer.Node( "MyVeryFirstNode" )
myNode                    # Gaffer.Node( "MyVeryFirstNode" )
```

This can become confusing when we mix them together, such as when we refer to the node's variable while using the plug's dictionary entry:

```python
script["MyVeryFirstNode"]["IntPlug"] # Gaffer.IntPlug( "IntPlug", defaultValue = 0, )
myNode["IntPlug"]                    # Gaffer.IntPlug( "IntPlug", defaultValue = 0, )
myPlug                               # Gaffer.IntPlug( "IntPlug", defaultValue = 0, )
```

In the next section of this tutorial, you will see several instances of mixed syntax, so bear in mind the distinction.


## Scripting a Point Sphere Scene ##

Next, we will demonstrate how to create nodes from imported modules, and connect them in script to build a very basic scene comprised of a point sphere.


### Adding nodes from a module ##

In the previous section we used a generic node which had no particular use. Useful nodes are sourced from one of Gaffer's [node modules](../../../Reference/NodeReference/index.md). When creating a node from a module in script, you will first need to `import` the module. Our new scene will contain a Sphere node, which requires the GafferScene module. 

Start by importing the GafferScene module and creating a Sphere node:

```python
import GafferScene
mySphere = GafferScene.Sphere()
script.addChild( mySphere )
```

![The Sphere node in the Viewer](images/viewerSphere.png "The Sphere node in the Viewer")

> Tip :
> When using the _Script Editor_, modules only need to be imported once per session.


### Changing plug values ###

A plug's value can be returned with the `getValue()` method and modified with the `setValue()` method.

Use the output of the _Script Editor_ to test the Sphere node's current Radius plug value:

```python
mySphere["radius"].getValue() # 1.0
```

Next, set the values of the sphere's Name, Radius, and Theta Max plugs:

```python
mySphere["name"].setValue( "mySphere" )
mySphere["radius"].setValue( 3 )
mySphere["thetaMax"].setValue( 180 )
```

![The Sphere node with adjusted plugs in the Node Editor](images/nodeEditorSphere.png "The Sphere node with adjusted plugs in the Node Editor")

![The Sphere node with adjusted plugs in the Viewer](images/viewerSpherePlugs.png "The Sphere node with adjusted plugs in the Viewer")

> Note :
> A scene node's Name plug determines the name of the object as it will appear in the scene hierarchy.


### Setting compound plug values ###

When a plug has its own child plugs, it is called a **compound plug**. An example would be the sphere's Transform plug, which has Translate, Rotate, and Scale child plugs. Plugs with multiple values are also compound plugs: they contain one child plug for each value. The Rotate plug, for instance, contains 3 child plugs, each with a float value for a different axis. You can either `setValue()` each child plug value individually, or all at once using the `V3f` type.

> Note :
> The `V3f` type requires the `imath` module.

First, increase the sphere's mesh division child plugs individually:

```python
# Editing a list one element at a time
mySphere["divisions"]["x"].setValue( 80 )
mySphere["divisions"]["y"].setValue( 160 )
```

![The Sphere node with double the divisions in the Viewer](images/viewerSphereDivisions.png "The Sphere node with double the divisions in the Viewer")

Then, move the sphere closer to the camera by adjusting all of the Translate plug's children using a `V3f` type:

```python
# Editing a list all at once
import imath
mySphere["transform"]["translate"].setValue( imath.V3f( 2, 0, 2 ) )
```

![The Sphere node with a transform in the Viewer](images/viewerSphereTransform.png "The Sphere node with a transform in the Viewer")

As you can see, assigning the Translate plug's value using the `V3f` type declares each of its values at once, which spares you from having to type out each child plug.

<!-- TODO: link to imath type reference, when it's made -->


### Referencing plug types ###

The Translate plug does not indicate that is uses the `V3f` type (other than its having 3 numerical fields), so how could you have known? Drag and drop again comes to the rescue, with a very easy and convenient way to discover the built-in type and syntax for a plug's value(s): 

> Tip : 
> To see the current plug's value in its native type, <kbd>Shift</kbd> + click and drag the plug label from the _Node Editor_ and drop it onto the _Script Editor_ input field.


### Connecting nodes ###

In Gaffer, nodes themselves are not connected together. Rather, a node's _in_ plug is connected to another node's _out_ plug using the `setInput()` method. The receiving node's _in_ plug does not take a value, but rather a node's _out_ plug itself.

Create a MeshToPoints node and connect it to the Sphere node, and set its point type:

```python
myMeshToPoints = GafferScene.MeshToPoints()
script.addChild( myMeshToPoints )
myMeshToPoints["in"].setInput( mySphere["out"] )
myMeshToPoints["type"].setValue( "sphere" )
```

![MeshToPoints node in the Viewer](images/viewerMeshToPoints.png "MeshToPoints node in the Graph Editor")

![MeshToPoints node in the Graph Editor](images/graphEditorMeshToPoints.png "MeshToPoints node in the Graph Editor")


### Connecting nodes with multiple inputs ###

Until now, you've been accessing plugs and nodes by name. Flexible, multi-input nodes like the Group node can have any number of inputs. To account for this, their _in_ plug behaves like an array, and its children are accessed using array indexing. The first child is accessed with `["in"][0]`, its second child with `["in"][1]`, and so on.

Create a Camera node, a Group node, and group the whole scene together:

```python
myCamera = GafferScene.Camera()
script.addChild( myCamera )
myGroup = GafferScene.Group()
script.addChild( myGroup )

myGroup["in"][0].setInput( myMeshToPoints["out"] )
myGroup["in"][1].setInput( myCamera["out"] )
```

![MeshToPoints and Camera grouped](images/graphEditorGroup.png "MeshToPoints and Camera grouped")

You now have the beginnings of a scene, built entirely in script.


## Recap ##

You should now have a good fundamental understanding of scripting in Gaffer. We have shown how Gaffer's node graphs can be constructed using a minimal collection of scripting commands, and that the _Script Editor_ makes experimenting with these commands easy by allowing node and plug references and values to be dropped directly into the _Script Editor_.


## See Also ##

- [Node Reference](../../../Reference/NodeReference/index.md)
- [_Script Editor_ Shorcuts](../../../Interface/ControlsAndShortcuts/index.html#script-editor)
