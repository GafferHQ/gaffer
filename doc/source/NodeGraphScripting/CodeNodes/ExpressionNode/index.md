# Expression Node #

The Expression node is a code node from the [Gaffer module](../../../Reference/NodeReference/Gaffer/index.md) that evaluates Python or OSL code during dispatch. It can be used to:

- Retrieve and modify plug values
- Retrieve and use context variables

It is one of the few nodes that does not appear as a box in the _Graph Editor_. Instead, it appears as a small circle with the label _e_, which cannot be changed.

![An expression node](images/graphEditorExpressionNode.png "An expression node")

You can select either Python or OSL from the node's Language plug in the _Node Editor_.

![Expression node with Hello, World!](images/nodeEditorWindowExpressionCode.png "Expression node with Hello, World!")

> Caution :
> Switching languages will erase the contents of the input field.


## Expression Interpretation ##

The expression in an Expression node is not evaluated natively. Rather, Gaffer uses an interpreter engine to evaluate the code and allow it to interact with the API.


### Referencing the main script ###

When writing code for Expression nodes, use the `parent` variable to refer to the main script rather than the default `script` variable. For example, you would reference a Sphere's Radius plug with:

```python
parent["Sphere"]["radius"]
```


### “print” command ###

Executing the `print` command in the expression will print to the terminal that launched Gaffer.


### Limitations ###

There are certain limitations to expressions. One is that you cannot correctly assign a variable to the main script and then reference the variable's children, as you can in other environments:

<!-- TODO: list more limitations -->

```python
mySphere = parent["Sphere"]
mySphere["transform"]["translate"] # Error
```


## Expression Connections ##

When an Expression node references or modifies another node's plug, a special green connection with an arrow appears between the two nodes in the _Graph Editor_.

When the Expression node merely references the node's plug, the arrow points at the Expression node.

![Connection when referencing](images/graphEditorExpressionNodeReference.png "Connection when referencing")

When the Expression node modifies the plug's value, the arrow points at the referenced node.

![Connection when modifying](images/graphEditorExpressionNodeModify.png "Connection when modifying")


## See Also ##

- [Expression Node Reference](../../../Reference/NodeReference/Gaffer/Expression.md)
- [OSLCode Node](../OSLCodeNode/index.md)
