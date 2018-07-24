# Dictionary Syntax #

Each Gaffer script contains a Python dictionary, which comprises a compendium of keys and values that correspond to the nodes, plugs, values, and connections in memory in C++. Using Python syntax and notation, you can access and manipulate this dictionary to modify the node graph.

In a script's node dictionary, a node is defined by a key and value, with the key as the node's name, and the value as the node's class. A plug is defined in the same way, only it is added as a sub-key of a node's key. As you add to and manipulate the graph (either using the _Graph Editor_ or the [_Script Editor_](../../NodeGraphScripting/ScriptEditor/index.md)), keys, sub-keys, and values are added to and changed in the dictionary.

Consider the following graph:

![A basic sample node graph with a SceneReader, ShaderAssignment, and Group node](images/graphEditorSample.png "A basic sample node graph with a SceneReader, ShaderAssignment, and Group node")

Using the _Script Editor_, you can reveal the dictionary's structure by querying the graph's nodes and plugs:

```python
script["SceneReader"] # GafferScene.SceneReader()
script["SceneReader"]["fileName"] # Gaffer.StringPlug( "fileName", defaultValue = '', )
script["SceneReader"]["tags"] # Gaffer.StringPlug( "tags", defaultValue = '', )

script["ShaderAssignment"] # GafferScene.ShaderAssignment()
script["ShaderAssignment"]["in"].getInput() # GafferScene.ScenePlug( "out", direction = Gaffer.Plug.Direction.Out, )
script["ShaderAssignment"]["in"].getInput().parent() # GafferScene.SceneReader( "SceneReader" )

script["Group"] # Module.NodeType3()
script["Group"]["in"][0].getInput().parent() # GafferScene.ShaderAssignment( "ShaderAssignment" )
```


## Adding Keys to a Node Dictionary ##

In Gaffer, adding keys to the `script` variable will add a corresponding node or plug to the graph.


### addChild() method ###

```python
script.addChild( Gaffer.Node( "newNode" ) )
```

The `addChild()` method is the safe method of adding keys, because it prevents existing nodes or plugs from being overwritten. If a new node or plug name conflicts with an existing name, `addChild()`  will add an iterated numeral to the name. For example, `newNode` would become `newNode1`.

> Tip :
> Use the `addChild()` method to add nodes and plugs to the Python dictionary.


### Using Python syntax ###

```python
script["newNode"] = Gaffer.Node()
```

If you prefer, you can also use the standard Python key assignment syntax, but it is not the best practice in Gaffer.

> Caution :
> Adding nodes and plugs using Python dictionary syntax might overwrite an existing node or plug. Use at your own risk.


## Compound Plugs ##

Compound plugs are referenced just like you would a dictionary sub-key in Python. Assuming you have a default Sphere node, the Transform plug's Translate child plug would be accessed with:

```python
script["Sphere"]["transform"]["translate"]
```


## See Also ##

- [Common Operations Reference](../../Reference/ScriptingReference/CommonOperations/index.md)
- [Script Files](../ScriptFiles/index.md)
- [Tutorial: Scripting Basics](../../../Tutorials/Scripting/GettingStarted/index.md)
