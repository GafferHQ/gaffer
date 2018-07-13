# Using the Script Editor #

The input field of the _Script Editor_ functions just like a regular plain text editor, while the output behaves like a debug terminal. Code you execute, and its results, will appear in the output of the _Script Editor_.

> Note :
> Any highlighted portions of the input code will remain in the input field.


## Executing Code ##

To execute code using the _Script Editor_:

1. Enter code into the input field.

2. If any portions of the input code need to be preserved, highlight them.

3. Hit <kbd>Control</kbd> + <kbd>Enter</kbd>.


## Inserting a Node or Plug Reference ##

You can manually create a node or plug reference by entering [dictionary syntax](../../ScriptingAPI/DictionarySyntax/index.md) into the input field of the _Script Editor_. However, this can be tedious and time-consuming. As a shortcut, you can directly reference a node or plug by dragging it into the input field. When inserting multiple nodes from the _Graph Editor_, the resulting reference will be formatted as an array of nodes.

> Tip :
> The _Script Editor_ does not automatically enter a new line when you drag and drop node or plug reference. If you want a reference to occur at the start of a line, hit <kbd>Enter</kbd> first.

To insert a node or plug reference into the _Script Editor_, drag the node or plug from another editor into the input field of the _Script Editor_:

- Plug in _Node Editor:_ Click and drag (![the "plug" icon](images/plug.png "The plug icon")) the plug label 
- Plug value in _Node Editor:_ Middle-click and drag (![the "values" icon](images/values.png "The values icon")) the plug label 
- Node(s) in _Graph Editor_: Middle-click and drag (![the "nodes" icon](images/nodes.png "The nodes icon")) the node(s)


## Inserting a Scene Location Path Reference ##

Similar to referencing nodes and plugs, you can also reference paths to scene locations from the _Hierarchy View_ and the _Viewer_. Regardless of the number of scene objects inserted, the resulting reference will always be formatted as an array.

> Note :
> As when making any scene hierarchy operations, it is important to consider the position in the graph where the reference occurs. The scene location path will vary depending on the selected node. Selecting the wrong node will lead to unintended results.

To insert a reference to a scene location into the _Script Editor:_

1. In the _Graph Editor_, select the node that outputs the scene location(s) you want to use.

2. Retrieve the reference from the _Viewer:_
    1. Select one or more objects and/or bounding boxes.
    2. Click and drag (![the "objects" icon](images/objects.png "The objects icon")) the selection onto the input field of the _Script Editor_.
    
3. Or, retrieve the reference from the _Hierarchy View:_
    1. Select one or more locations and/or objects.
    2. Click and drag (![the "objects" icon](images/objects.png "The objects icon")) the selection onto the input field of the _Script Editor_.


## Invoking Context ##

You can also invoke the [context](../../ScriptingAPI/Context/index.md) of the script in its instantiated state. Examples of context values you might want to query are the main timeline's variables, like the current frame, and global context variables, like the project name.

The `context` variable is not available in the _Script Editor_. Instead, you need to reference the `context()` function in conjunction with the usual `script` variable:

```python
script.context().getFrame()
```


## See Also ##

- [Scripting Reference](../../Reference/ScriptingReference/index.md)
- [The Script Editor](../ScriptEditor/index.md)
- [Controls and Shortcuts](../../Interface/ControlsAndShortcuts/index.md)
