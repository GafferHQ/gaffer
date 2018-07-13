
# Special Variables #

The Gaffer API has some special reserved utility variables for use in expressions and code input fields.


## The “script” Variable ##

In Gaffer scripts, the variable used to invoke the root of the script is the `script` variable. When building the node graph of your script, nodes are added using this variable.


## The “parent” Variable ##

The `parent` variable is used to invoke the containing node or the root of the script, depending on the context. This variable is primarily used in serialized code, to avoid scope issues when transferring code between [script files](../ScriptFiles/index.md), Reference and Box nodes <!-- TODO: box and reference article links-->, and the [application's code input fields](../../NodeGraphScripting/ScriptEditor/index.md).

- If serialized code is loaded as the main script file, `parent` will be an alias for `script`.
- If serialized code is pasted into a code input field, `parent` will be an alias for `script`.
- If serialized code is imported or pasted into a Reference or Box node, `parent` will point to the node.


## The “context” Variable ##

```eval_rst
See :ref:`Using the Expression Node<Invoking the Context>`.
```


## See Also ##

- [Using the Script Editor](../../NodeGraphScripting/UsingScriptEditor/index.md)
- [Script Files](../ScriptFiles/index.md)

