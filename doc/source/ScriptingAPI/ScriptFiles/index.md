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

The “Gaffer” extension. Intended for scripts used as the main project file.


### .grf ###

The “Gaffer reference” extension. Intended for scripts exported and imported from Reference and Box nodes.

> Note :
> The Reference and Box nodes will only import scripts with the .grf extension. To import a .gfr script into a Reference or Box node, change its extension to .grf. No additional conversion is necessary.


## Sample Script File ##

Below are the contents of a sample Gaffer file containing a SceneReader and Camera node connected to a Group node:

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

Here is a breakdown of the format:

### “import” commands ###

When a script is saved or copied, the serializer automatically detects which [node modules](../NodeModules/index.md) are required to rebuild the node graph, and adds them as `import` commands at the beginning of the serialized code.


<!-- TODO: ? ### "Metadata" ### -->


### “parent” variable ###

Normally, nodes are added to the `script` variable. In serialized code, however, compatibility between different environments needs to be preserved, and node scope issues need to be avoided. Therefore, the ["parent" variable](../SpecialVariables/index.md) is used instead, to guarantee the nodes are added to the root script.


### “__children” variable ###

To avoid issues overwriting the `parent` variable's [dictionary](../DictionarySyntax/index.md) keys, serialized scripts also use the `addChild()` method, in conjunction with a temporary `__children` variable. This way, the serializer can add nodes to the dictionary without accidentally overwriting them, while also retaining their handles for later reference.


## See Also ##

- [Dictionary Syntax](../DictionarySyntax/index.md)
- [Using the Script Editor](../../NodeGraphScripting/UsingScriptEditor/index.md)
