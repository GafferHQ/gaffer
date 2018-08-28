
# Special Variables #

The Gaffer API has some special reserved utility variables for use in expressions and code input fields.


## The “script” Variable ##

In Gaffer scripts, the variable used to invoke the root of the script when using the [_Script Editor_]((../../NodeGraphScripting/ScriptEditor/index.md) is the `script` variable. When building the node graph of your script, nodes are added using this variable.


## The “parent” Variable ##

The `parent` variable is used to invoke the containing node or the root of the script, depending on the context. This variable is primarily used in serialized code, to avoid scope issues when transferring code between [script files](../ScriptFiles/index.md), Reference and Box nodes <!-- TODO: box and reference article links-->, and the [application's code input fields](../../NodeGraphScripting/ScriptEditor/index.md).

- If serialized code is loaded or pasted into the main script, `parent` will refer to the node graph of the root script.
- If serialized code is pasted into a code input field (such as that of an Expression or OSLCode node), `parent` will refer to the node graph of the containing node or the root script.
- If serialized code is imported or pasted into a Reference or Box node, `parent` will refer to the node graph of the containing node.


## The “context” Variable ##

In Expression and OSLCode nodes, `context` is a special variable that will invoke the currently evaluated [context](../Context/index.md).

> Note :
> The `context` variable is different from the `context()` command. They should not be used interchangeably.

```eval_rst
For more information about using this variable, see :ref:`Using the Expression Node<Invoking the Context>`.
```


## See Also ##

- [Using the Script Editor](../../NodeGraphScripting/UsingScriptEditor/index.md)
- [Script Files](../ScriptFiles/index.md)

