# Scene Context #

In the [Querying the Scene tutorial](../../Tutorials/Scripting/QueryingAScene/index.md), we demonstrated querying a scene using the `object()` method.

Certain scene properties cannot be queried using the _Scene Inspector_ or the `object()` method. This is especially irksome, because the `object()` method was very convenient in that it bypassed the need to provide a [context](../Context/index.md). However, sometimes there is no way around this, and you will need to specify a context in which to query a scene property.


### "with" keyword ###

To set a context and query the scene, use the `with` Python keyword. `with` establishes a new context, in which you can access context variables and values as they would exist in a thread.

In the tutorial, there was a Camera node connected to a Group node, giving a location of `/world/camera`. For the next example, we will use the same scene hierarchy. In the following code, the `object` child plug, which normally returns an error when `getValue()` is used on it, properly returns the camera's scene path:


```python
with Gaffer.Context( script.context() ) as newContext :
    newContext["scene:path"] = IECore.InternedStringVectorData( [ 'world', 'camera' ] )
    camera = script["StandardOptions"]["out"]["object"].getValue()
    print camera
```


## See Also ##

- [Context](../Context/index.md)
