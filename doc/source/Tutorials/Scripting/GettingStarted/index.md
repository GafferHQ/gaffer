# Tutorial: Node Graph Editing in Python #

In Gaffer, you can interactively manipulate node graphs in Python using the _Python Editor_. Gaffer's API is fairly frugal, so learning a few fundamental concepts and tasks will go a long way. In this tutorial, we will give you a quick tour of these fundamentals. Using only Python, you will create a simple graph that consists of a camera and a mauve sphere:

![A preview of the final scene](images/viewerFinalScene.png "A preview of the final scene")

By the end of this tutorial, you should have an understanding of the following topics in Python:

- The _Python Editor_
- Importing modules
- Creating nodes
- Node and plug references
- Setting plug values
- Node connections
- Deleting nodes

> Note :
> For this tutorial, we will assume you are familiar with the Python language.

Before you begin, we highly recommend you complete the [Assembling the Gaffer Bot tutorial](../../../Tutorials/BeginnerTutorial/index.md).


## The Python Editor ##

With the built-in _Python Editor_, you can build and modify the node graph, test API code and syntax, return plug values, and query scenes and images. In the default layout, the editor is in the bottom-right panel, under a tab next to the _Hierarchy View_.

The bottom-half of the _Python Editor_ is the code input field. The top-half is the code output log. Try executing a "Hello, World!" command:

1. Type `print "Hello, World!"` into the input field.
2. Hit <kbd>Control</kbd> + <kbd>Enter</kbd> to execute the code.

![The Python Editor with “Hello, World!”](images/pythonEditorHelloWorld.png "The Python Editor with “Hello, World!”")


## Creating Nodes ##

In the Gaffer API, each node is an instance (in the programming sense) of a class, with each class belonging to a particular Python module. In order to create a node sourced from a module, you will first need to import that module.

> Tip :
> A list of each of Gaffer's default modules can be found in the [Node Reference](../../../Reference/NodeReference/index.html).

Since the scene will require a sphere primitive, import the [GafferScene](../../../Reference/NodeReference/GafferScene/index.md) module, and then create a Sphere node:

```python
import GafferScene
mySphere = GafferScene.Sphere()
root.addChild( mySphere )
```

![A new Sphere node in the main window](images/mainWindowSphereNode.png "A new Sphere node in the main window")

Notice that the node was added with the `addChild()` method to the `root` variable. The `addChild()` method is the core method for adding nodes and plugs to the node graph. The `root` variable references the root of the node graph. All nodes in the graph are ultimately children of the root. If you declared the node variable without adding it to the `root` variable, it would exist in memory (all variables in Python are objects), but it would not yet be part of the graph.

Helpfully, once you import a module, it will remain loaded in that _Python Editor_ (however, if you open a new _Python Editor_, you will need to import it again). The rest of the nodes you will need for this graph also come from the `GafferScene` module, so add them next:

```python
myShader = GafferScene.OpenGLShader()
myAssignment = GafferScene.ShaderAssignment()
myFilter = GafferScene.PathFilter()
myCamera = GafferScene.Camera()
myGroup = GafferScene.Group()
root.addChild( myShader )
root.addChild( myAssignment )
root.addChild( myFilter )
root.addChild( myCamera )
root.addChild( myGroup )
```

![All nodes in the Graph Editor, unconnected](images/graphEditorAllNodes.png "All nodes in the Graph Editor, unconnected")


## Referencing Nodes without Variables ##

Nodes that do not have variables can be referenced by dragging and dropping them in the interface:

1. Middle-click and drag a node from the _Graph Editor_ (the cursor will change to ![the nodes icon](images/nodes.png "The nodes icon")).
2. Release the selection onto the input field of the _Python Editor_.


## Loading Shaders ##

Before we move on to plugs, you should complete the node creation process by loading a shader into the OpenGLShader node. Shader nodes start out blank, so there is one additional step required, which is to load a shader configuration. For this graph, all you need is a simple color. Load a constant shader with the `loadShader()` method:

```python
myShader.loadShader( 'Constant' )
```


## Referencing Plugs ##

Since a node's default plugs are created automatically, they have no assigned variables, so you will need to reference them another way. In the API, plugs in the graph (and also, in fact, the nodes and the `root` variable) can each be treated like a Python dictionary, with key-value pairs. When editing plug values, it is usually necessary to first reference them in dictionary syntax.

For example, you could reference the radius plug of the Sphere node like this:

```python
mySphere['radius']
```

![A plug reference in the Python Editor](images/pythonEditorPlugReference.png "A plug reference in the Python Editor")

> Caution :
> Because Python dictionaries do not have built-in overwrite protection, you can accidentally and irrecoverably replace nodes and plugs with assignments that use existing node names, like `root['Sphere'] = ...`. Use dictionary syntax with care.

Just like with nodes, you can insert a reference to a plug by dragging. Try inserting a reference to radius plug of the Sphere node:
 
1. Select the Sphere node in the _Graph Editor_.
2. Click and drag the **label** of the radius plug from the _Node Editor_ (the cursor will change to ![a plug](images/plug.png "A plug")).
3. Release it onto the input field of the _Python Editor_.

A reference to `root['Sphere']['radius']` will be inserted. This is identical to `mySphere['radius']` from earlier. Notice how when you drag and drop plugs, the reference is formatted in dictionary syntax.

> Important :
> Dragging and dropping plugs is a core technique when using the _Python Editor_. It can speed up your node graph editing and inspecting considerably.


## Retrieving a Plug Value ##

The `getValue()` method retrieves a plug's value. Try it on the `Cs` (colour) plug of the OpenGLShader node:

```python
myShader['parameters']['Cs'].getValue()
```

There is also a shortcut for grabbing a plug value, which involves <kbd>Shift</kbd> + clicking and dragging the plug label from a _Node Editor_ (the cursor will change to ![the values icon](images/values.png "The values icon")) and releasing it onto the input field of the _Python Editor:_

![A plug value reference in the Python Editor](images/pythonEditorPlugValueReference.png "A plug value reference in the Python Editor")

> Tip :
> The above shortcut can also be very handy in regular use. For instance, if you need to know the type and format of a particular plug's value, dragging it into the _Python Editor_ will reveal it.


## Editing a Plug Value ##

The `setValue()` method edits plug values. It functions on plugs with both single and multi-element data types.

<!-- TODO: link to plug type reference, once it is created -->

Editing plugs with one element is simple. All you need to provide is the value. Try increasing the radius of the sphere:

```python
mySphere['radius'].setValue( 4 )
```

![The sphere with increased radius in the Viewer](images/viewerSphereRadius.png "The sphere with increased radius in the Viewer")

When editing a plug with multiple elements, such as a vector, color, matrix, etc., you can either edit all the values at once, or one at a time. Editing all the values at once requires formatting the value in the type's syntax. Most of the multi-element types belong to the `imath` utility module, so before you can edit them, you will first need to import it.


## Editing the Remaining Plugs ##

In this next part, we will step you through the remaining plug edits for your node graph. For each of the following plugs you edit, you will see little to no change, because the nodes are not yet connected. Think of these steps as preparing the plugs.

3-color plugs (colors with no alpha channel) use the `Color3f()` type, so first, import `imath` and set the OpenGLShader node's `Cs` plug:

```python
import imath
myShader['parameters']['Cs'].setValue( imath.Color3f( 0.25, 0.75, 0.25 ) )
```

![The OpenGL node with an adjusted constant plug](images/nodeEditorOpenGLPlug.png "The OpenGL node with an adjusted constant plug")

Next, adjust the camera position, but this time specify only the _z_-axis value of the transform, with dictionary syntax:

```python
myCamera['transform']['translate']['z'].setValue( 8 )
```

![The camera node with an adjusted translate plug](images/viewerCameraPosition.png "The camera node with an adjusted translate plug")

Finally, add a location to the `paths` plug of the PathFilter node:

```python
import IECore
myFilter['paths'].setValue( IECore.StringVectorData( [ '/sphere' ] ) )
```

The above code is more advanced than what we have shown so far, but you will likely need it at some point when editing node graphs. Any time you edit a plug that can take multiple strings, you will need to format the strings as a list, with `IECore.StringVectorData()`. When using this method, remember to first import the `IECore` module.


## Connecting Nodes ##

Nodes do not connect together: their plugs do. The `setInput()` method connects a destination plug to a source plug. 

The input and output plugs on scene nodes that are visible in the _Graph Editor_ follow this naming scheme:
- Output (bottom edge of node): `out`
- Input (top edge of node): `in`
- Filter input (right edge of node): `filter`
- Shader input (left edge of node): `shader`

> Note :
> You are not limited to connecting the default plugs visible in the _Graph Editor_. The `setInput()` method can connect most pairs of plugs.

For example, to connect scene node A to scene node B, an `in` plug of node B is connected to the `out` plug of node A.

Since the ShaderAssignment node has all three types of scene node input plugs, start by connecting it:

```python
myShaderAssignment['in'].setInput( mySphere['out'] ) # Main input/output
myShaderAssignment['shader'].setInput( myShader['out'] ) # Shader input/output
myShaderAssignment['filter'].setInput( myFilter['out'] ) # Filter input/output
```

![The ShaderAssignment node with new connections](images/graphEditorShaderAssignmentConnections.png "The ShaderAssignment node with new connections")

A node that takes multiple input scenes, like the Group node, is slightly different. Its `in` plug is an `ArrayPlug` that consists of multiple children, each a separate scene input accessed via integer index:

```python
myGroup['in'][0].setInput( myAssignment['out'] )
myGroup['in'][1].setInput( myCamera['out'] )
```

![The Group node with new connections](images/graphEditorGroupConnections.png "The Group node with new connections")

> Caution :
> Scene nodes with an `ArrayPlug` input automatically maintain one free child, so that there is always at least one input available. Make sure to connect their child plugs in order: `['in'][0]`, `['in'][1]`, `['in'][2]`, etc. Connecting them out-of-order will return an error.

As you probably noticed, the graph looks tangled up, but that's a consequence of scripting a graph piece-by-piece. Correct this by selecting all the nodes, and then hitting <kbd>Control</kbd> + <kbd>L</kbd>.

![The nodes, rearranged](images/graphEditorRearrangedNodes.png "The nodes, rearranged")

Much better!

> Tip :
> When creating a node graph using Python, if you add the nodes, declare variables for them, connect them, and **then** add them to `root` all at once, they will automatically and evenly lay themselves out. In fact, that is essentially what Gaffer scripts do when loaded.

Here is the final graph:

![The final scene](images/mainWindowFinalScene.png "The final scene")


## Deleting Nodes ##

There's one final common operation you may want to perform on nodes using Python: deletion. Nodes and plugs both have a `removeChild()` method. Try removing the Sphere node: 

```python
root.removeChild( mySphere )
```


## Recap ##

That covers the most common methods and tasks when using Python to edit node graphs. As we have shown, you have the capacity to accomplish almost all interface actions in Python, demonstrating the power and flexibility of the API.


## See Also ##

- [Node Reference](../../../Reference/NodeReference/index.md)
- [_Python Editor_ Shorcuts](../../../Interface/ControlsAndShortcuts/index.html#script-editor)
