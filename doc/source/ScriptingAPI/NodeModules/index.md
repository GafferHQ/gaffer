# Node Modules #

Each node type in Gaffer is a different C++/Python class sourced from a module. Each module declares nodes of a particular category, designed to perform a certain kind of task or process. In order for a Gaffer script to use a node, the node's module first needs to be loaded using the `import` command. For example:

```python
import GafferScene # Scene-related nodes
import GafferOSL # OSL-related nodes
import GafferAppleseed # Appleseed-related nodes
```


## See Also ##

- [Node Module Reference](../../Reference/NodeReference/index.md)
- [The Script Editor](../../NodeGraphScripting/ScriptEditor/index.md)
- [Dictionary Syntax](../DictionarySyntax/index.md)
