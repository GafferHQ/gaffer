# Using the Expression Node #

The Expression node is intended to be used for retrieving and changing plug values based on script context and context variables.


## Executing the Expression ##

> Tip :
> Use the `print` command in expressions to send output to the terminal that launched Gaffer.

While the Expression node is meant to be evaluated during dispatch, you can also execute its code within Gaffer, just like the _Script Editor_. This can be useful for debugging context variables in the expression node's [context](../../../ScriptingAPI/Context/index.md).

To execute an Expression node's expression:

1. Select the Expression node.

2. In the _Node Editor_, focus on the code input field by tabbing to it or clicking inside it.

3. Hit <kbd>Control</kbd> + <kbd>Enter</kbd>.


## Referencing Plugs ##

For these instructions, we will use a Sphere node and its Radius plug as an example.

Plug references are in dictionary format. For example:

```python
parent["Sphere"]["radius"]
```


### Creating an Expression node from a plug ###

Expression nodes can be created in the _Graph Editor_ and _Script Editor_ using the standard node creation methods. However, since Expression nodes typically access at least one plug of another node, there is a shortcut to create a new Expression node and automatically reference a plug and its value.

To create a new Expression node with an automatic reference to a plug:

1. Select the target node so the _Node Editor_ displays its plugs.

2. In the _Node Editor_, right-click the Radius plug's label or value. The plug's drop-down menu will appear.

3. Select _Create Python Expression..._ or _Create OSL Expression..._. The node will appear in the graph with a green connection to the Sphere node.


### Referencing other plugs ###

> Tip :
> The Expression node's input field does not enter a new line when you reference a plug. If you want the reference to occur at the start of the line, hit <kbd>Enter</kbd> first.

If you need to reference additional plugs or plugs from other nodes, there is a shortcut to do so without typing.

To reference another plug in an Expression Node:

1. Double-click the node you want to reference in the _Graph Editor_. A new _Node Editor_ window for that node.

2. In the _Graph Editor_, select the Expression node.

3. Click and drag the plug label from the reference node's _Node Editor_ window onto the Expression node's input field in the main _Node Editor_.


## Invoking the Context ##

To invoke context in Expression nodes, use the special `context` variable. For example, if you want an Expression node to change a Sphere node's height based on the context's frame, you would retrieve the frame using:

```python
parent["Sphere"]["transform"]["translate"]["y"] = context.getFrame()
```

> Caution :
> Invoking the `context()` function instead of the `context` variable in Expression nodes can cause errors.


### Context variable default values ###

When using the `get()` method on a context variable to drive a plug value, make sure to provide a default value. For example, when retrieving an float variable `myVar`, use:

```python
parent["Sphere"]["transform"]["translate"]["y"] = context.get( "myVar", 0 )
```

This way, the plug you assign the value to will have a value to fall back on. If you do not provide a default value, the node graph will display an error, since the context variable's value is not evaluated until dispatch.

![Node error caused by no default plug value, in Graph Editor](images/graphEditorNodeError.png "Node error caused by no default plug value, in Graph Editor")


## See Also ##

- [Using the Script Editor](../../UsingScriptEditor/index.md)
- [Using the OSLCode Node](../UsingOSLCodeNode/index.md)
