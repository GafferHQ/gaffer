# Context Variables #


## Global Context Variables ##

Global Context Variables are available to all nodes. Gaffer adds several of them by default, and you can also specify your own.

Global variables values can be edited in the interface's Settings window (_File_ > _Settings..._). Variables related to the script's basic setup are assigned in the window's Settings tab. Other global variables, including user-specified ones, can be added in the Variables tab. These settings can also be accessed from the `ScriptNode` object (for example, from the Python Editor: `root["framRange"]` or `root["variables"]["myVariable"]`).

The default global Context Variables present in the graph root are:

```eval_rst
+-------------------------------+-------------------------------------------------------------------+
| Global Context Variable       | Meaning                                                           |
+===============================+===================================================================+
| :code:`project:name`          | The name of the project the graph belongs to.                     |
+-------------------------------+-------------------------------------------------------------------+
| :code:`project:rootDirectory` | The directory where the current graph's project files are stored. |
+-------------------------------+-------------------------------------------------------------------+
| :code:`frame`                 | The current frame of the graph.                                   |
+-------------------------------+-------------------------------------------------------------------+
| :code:`framesPerSecond`       | The frame rate of the graph.                                      |
+-------------------------------+-------------------------------------------------------------------+
| :code:`frameRange:start`      | The first frame in the frame range.                               |
+-------------------------------+-------------------------------------------------------------------+
| :code:`frameRange:end`        | The last frame in the frame range.                                |
+-------------------------------+-------------------------------------------------------------------+
| :code:`script:name`           | The name of the script.                                           |
+-------------------------------+-------------------------------------------------------------------+
```


## Built-in scene Context Variables ##

Gaffer can create the following built-in Context Variables inside scene Contexts:

```eval_rst
+---------------------------------+--------------------------------------------------------------------------------------------------------------------------+
| Build-in scene Context Variable | Meaning                                                                                                                  |
+=================================+==========================================================================================================================+
| :code:`scene:path`              | Scene location being generated, when computing in service of a bound, transform, attributes, object, or childNames plug. |
+---------------------------------+--------------------------------------------------------------------------------------------------------------------------+
| :code:`scene:setName`           | Name of the set being whose membership is being queried, when computing in service of a set plug.                        |
+---------------------------------+--------------------------------------------------------------------------------------------------------------------------+
| :code:`scene:renderer`          | The active renderer during computation.                                                                                  |
+---------------------------------+--------------------------------------------------------------------------------------------------------------------------+
```


## Built-in image Context Variables ##

Gaffer can create the following built-in Context Variables inside image Contexts:

```eval_rst
+---------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Build-in image Context Variable | Meaning                                                                                                                                                                                                                                                |
+=================================+========================================================================================================================================================================================================================================================+
| :code:`image:tileOrigin`        | Coordinate of bottom-left pixel of tile being generated when computing in service of a channelData plug.                                                                                                                                               |
+---------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| :code:`image:channelName`       | Channel being generated when computing in service of a channelData plug.                                                                                                                                                                               |
+---------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| :code:`image:defaultFormat`     | The fallback format of an image network, if no format has been specified. A `GafferImage.FormatData` object. Use the `value` property to get the `GafferImage.Format <https://github.com/GafferHQ/gaffer/blob/master/include/GafferImage/Format.h>`_.  |
+---------------------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
```


## Node default Context Variables ##

Some nodes add additional Context Variables during execution. As such, these variables are only available upstream of these nodes in the graph. Most of them will have a plug that determines the Context Variable name(s). You can rename them as needed. The following table lists these default names.

> Note : The `prefix:name` format in the default Context Variable names is merely a convention used to avoid clashes between variable names. We recommend you follow the same conventions when naming your own variables, but it is not compulsory.

```eval_rst
+---------------------------+---------------+-------------------------------------------------------------+
| Context Variable          | Source node   | Meaning                                                     |
+===========================+===============+=============================================================+
| :code:`loop:index`        | Loop          | Current iteration of the loop                               |
+---------------------------+---------------+-------------------------------------------------------------+
| :code:`wedge:value`       | Wedge         | Value of the current wedge.                                 |
+---------------------------+---------------+-------------------------------------------------------------+
| :code:`wedge:index`       | Wedge         | Iteration of the current wedge.                             |
+---------------------------+---------------+-------------------------------------------------------------+
| :code:`collect:rootName`  | CollectScenes | Name of the current root location being added to the scene. |
+---------------------------+---------------+-------------------------------------------------------------+
| :code:`collect:layerName` | CollectImages | Name of the current layer being added to the image.         |
+---------------------------+---------------+-------------------------------------------------------------+
```


## Accessing Context Variables ##

For the available methods to access Context Variables with the Python and OSL APIs, see the [Expressions reference](../ScriptingReference/Expressions/index.md).

> Note : To query plug values in the API, you must first instantiate an appropriate Context object. See [Contexts](../../WorkingWithTheNodeGraph/Contexts/index.html#querying-results-with-contexts) and [Common Operations](../ScriptingReference/CommonOperations/index.html#scenes) for more details.


## See also ##

- [Contexts](../../WorkingWithTheNodeGraph/Contexts/index.md)
- [Expressions reference](../ScriptingReference/Expressions/index.md)
