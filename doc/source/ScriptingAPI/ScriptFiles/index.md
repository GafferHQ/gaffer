# Script Files #

Gaffer script files – the projects you load and save – are simply a sequence of Python code that carry all the instructions necessary to reconstruct a node graph. When you save a script in Gaffer, the serializer engine takes the nodes and plugs of the current graph and writes them in sequence to an unbinarized file with a Gaffer extension in UTF-8 encoding.

> Important :
> Scripts loaded into the application and code copy-pasted from or to the _Graph Editor_ use the same syntax. They are safely interchangeable.

You can copy a part or all of a node graph in the _Graph Editor_ (select the nodes, then hit <kbd>Control</kbd> + <kbd>C</kbd>) and paste it into the _Script Editor_ or an external text editor. If you find yourself struggling to find a way of constructing a portion of a graph using script, you can open a sample script in an external text editor and examine how it is constructed.


<!-- TODO: Find a more precise URL -->
<!-- TODO: Make a proper list of places -->
<!-- > Tip : Sample Gaffer scripts can be found in the [source code itself](https://github.com/GafferHQ/gaffer/tree/0.47.0.0). -->


## File Formats ##

Gaffer loads and saves files in the following formats:


### .gfr ###

The “Gaffer” extension. Intended for use as the main project file, or for adding to one. Created when saving a file or exporting a selection of nodes (_File_ > _Export Selection..._).


### .grf ###

The “Gaffer reference” extension. Intended for scripts exported and imported into Box nodes or imported into Reference nodes. Created when exporting a Box node.


## Sample Script File ##

Here are the contents of a sample Gaffer script, followed by a breakdown of the format:

```python
import Gaffer
import GafferScene
import IECore

__children = {}

__children["SceneReader"] = GafferScene.SceneReader( "SceneReader" )
parent.addChild( __children["SceneReader"] )
__children["Group"] = GafferScene.Group( "Group" )
parent.addChild( __children["Group"] )
__children["Group"]["in"].addChild( GafferScene.ScenePlug( "in1" ) )
__children["Group"]["in"].addChild( GafferScene.ScenePlug( "in2" ) )
__children["Camera"] = GafferScene.Camera( "Camera" )
parent.addChild( __children["Camera"] )
__children["Group"]["in"]["in0"].setInput( __children["SceneReader"]["out"] )
__children["Group"]["in"]["in1"].setInput( __children["Camera"]["out"] )

del __children
```


### “import” commands ###

When a script is saved or copied, the serializer automatically detects which [node modules](../NodeModules/index.md) are required to rebuild the node graph, and adds them as `import` commands.


<!-- TODO: ? ### "Metadata" ### -->


### “parent” variable ###

In serialized code, compatibility between different graph environments needs to be preserved, and node scope issues need to be avoided. Therefore, instead of using the `script` variable (as you would in the _Script Editor_), the serializer uses the ["parent" variable](../SpecialVariables/index.md) to guarantee the nodes are added to the containing environment, whether it be the root script or a containing node.


### “__children” variable ###

To avoid issues overwriting the `parent` variable's [dictionary](../DictionarySyntax/index.md) keys, serialized scripts also use the `addChild()` method, in conjunction with a temporary `__children` variable. This way, the serializer can add nodes to the dictionary without accidentally overwriting existing nodes with identical names, while also retaining their handles for later reference.


## See Also ##

- [Dictionary Syntax](../DictionarySyntax/index.md)
- [Using the Script Editor](../../NodeGraphScripting/UsingScriptEditor/index.md)
