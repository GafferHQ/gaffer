# Context Variables #


## Global Context Variables ##

Global Context Variables are available to all nodes. Gaffer adds several of them by default, and you can also specify your own.

Global variables values can be edited in the interface's Settings window (_File_ > _Settings..._). Variables related to the script's basic setup are assigned in the window's Settings tab. Other global variables, including user-specified ones, can be added in the Variables tab. These settings can also be accessed from the `ScriptNode` object (for example, from the Python Editor: `root["frameRange"]` or `root["variables"]["myVariable"]`).

The default global Context Variables present in the graph root are:

Context Variable        | Meaning
------------------------|--------
`project:name`          | The name of the project the graph belongs to.
`project:rootDirectory` | The directory where the current graph's project files are stored.
`frame`                 | The current frame of the graph.
`framesPerSecond`       | The frame rate of the graph.
`frameRange:start`      | The first frame in the frame range.
`frameRange:end`        | The last frame in the frame range.
`script:name`           | The name of the script.


## Built-in scene Context Variables ##

Gaffer can create the following built-in Context Variables inside scene Contexts:

Context Variable   | Meaning
-------------------|--------
`scene:path`       | Scene location being generated, when computing in service of a bound, transform, attributes, object, or childNames plug.
`scene:setName`    | Name of the set being whose membership is being queried, when computing in service of a set plug.
`scene:renderer`   | The active renderer during computation.


## Built-in image Context Variables ##

Gaffer can create the following built-in Context Variables inside image Contexts:

Context Variable      | Meaning
----------------------|--------
`image:tileOrigin`    | Coordinate of bottom-left pixel of tile being generated when computing in service of a channelData
`image:channelName`   | Channel being generated when computing in service of a channelData
`image:defaultFormat` | The fallback format for image creation nodes, if no format has been specified.

## Node default Context Variables ##

Some nodes add additional Context Variables during execution. As such, these variables are only available upstream of these nodes in the graph. Most of them will have a plug that determines the Context Variable name(s). You can rename them as needed. The following table lists these default names.

> Note : The `prefix:name` format in the default Context Variable names is merely a convention used to avoid clashes between variable names. We recommend you follow the same conventions when naming your own variables, but it is not compulsory.

Context Variable    | Source node   | Meaning
--------------------|---------------|--------
`loop:index`        | Loop          | Current iteration of the loop
`wedge:value`       | Wedge         | Value of the current wedge.
`wedge:index`       | Wedge         | Iteration of the current wedge.
`collect:rootName`  | CollectScenes | Name of the current root location being added to the scene.
`collect:layerName` | CollectImages | Name of the current layer being added to the image.

## Accessing Context Variables ##

For the available methods to access Context Variables with the Python and OSL APIs, see the [Expressions reference](../ScriptingReference/Expressions/index.md).

> Note : To query plug values in the API, you must first instantiate an appropriate Context object. See [Contexts](../../WorkingWithTheNodeGraph/Contexts/index.html#querying-results-with-contexts) and [Common Operations](../ScriptingReference/CommonOperations/index.html#scenes) for more details.


## See also ##

- [Contexts](../../WorkingWithTheNodeGraph/Contexts/index.md)
- [Expressions reference](../ScriptingReference/Expressions/index.md)
