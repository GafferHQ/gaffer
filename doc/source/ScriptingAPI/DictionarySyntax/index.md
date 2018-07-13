# Dictionary Syntax #

Gaffer scripts use Python's dictionary syntax and notation to define the node graph. As you add to and manipulate the node graph, the dictionary builds a compendium of instances of node and plug classes. Each node is a dictionary key, with a node class as its value. Each plug is a sub-key of a node's key, with a plug class as its value. The following pseudocode shows a rough approximation of a node graph's dictionary:

```python
script = {
    ["Node1"]:Module.NodeType1()
    ["Node1"]["Plug1"]:Module.PlugType1()
    ["Node1"]["Plug2"]:Module.PlugType2()

    ["Node2"]:Module.NodeType2()
    ["Node2"]["Plug1"]:Module.PlugType1()
    ["Node2"]["in"]:GafferScene.ScenePlug( ["Node1"]["out"] )
    
    ["Node3"]:Module.NodeType3()
    ["Node3"]["in"]:GafferScene.ScenePlug( ["Node2"]["out"] )
}
```

When the script is evaluated, Gaffer traverses the dictionary, using the _in_ plugs of nodes to build a parent-child hierarchy. This becomes a dependency graph, as represented in the _Graph Editor_. At the start of all Gaffer node graphs is a root ScriptNode object, referenced by the `script` variable.


## Adding Keys to Gaffer Dictionaries ##

In Gaffer, adding nodes to the node graph is synonymous with adding keys to the `script` variable.


### Python syntax ###

```python
script["newNode"] = Gaffer.Node
```

> Caution :
> Adding nodes and plugs using Python dictionary syntax risks overwriting an existing node or plug.

If you are familiar with Python, you probably know the syntax for adding keys to a dictionary. Gaffer's `script` variable is compatible with it, but it is not the best practice.


### addChild() method ###

```python
script.addChild( Gaffer.Node( "newNode" ) )
```

> Tip :
> Use the `addChild()` method to create nodes and plugs.

The `addChild()` method is the safer and preferred method, because it prevents the overwriting of existing nodes or plugs. When a new node or plug name conflicts with an existing name, `addChild()`  adds an iteration numeral to the name. For example, `newNode` would become `newNode1`.


## Compound Plugs ##

Compound plugs are referenced just like you would a dictionary sub-key in Python. Assuming you have a default Sphere node, the Transform plug's Translate child plug would be accessed with:

```python
script["Sphere"]["transform"]["translate"]
```


## See Also ##

- [Common Operations Reference](../../Reference/ScriptingReference/CommonOperations/index.md)
- [Script Files](../ScriptFiles/index.md)
- [Tutorial: Scripting Basics](../../../Tutorials/Scripting/GettingStarted/index.md)
