# The Script Editor #

Gaffer's _Script Editor_ lets you build and modify the node graph through its underlying code, test expressions, and display results. In the default UI layout, it resides in the bottom-right panel, in the tab next to the _Hierarchy View_.

![The Script Editor](images/scriptEditorBlank.png "The Script Editor")

The _Script Editor_ is split into two areas. The bottom-half is the code input field. The top-half is the code output, which displays your executed code, its output results, and any errors. Errors will appear in red.

![Errors in the output field](images/scriptEditorError.png "Errors in the output field")

The _Script Editor_ functions like a debug terminal. In the input field, you can type, select, cut, copy, and paste code. Once your code is ready, you can execute it. The output field displays a history of your executed code, as well as any returns or outputs.

Just like with [Gaffer's script files](../../ScriptingAPI/ScriptFiles/index.md), when creating a new node using the _Script Editor_, you will first need to `import` the node's module.

> Note :
> When using the _Script Editor_, you do not need to `import` the Gaffer or IECore modules. They are loaded by default.


## See Also ##

- [Using the Script Editor](../UsingScriptEditor/index.md)
