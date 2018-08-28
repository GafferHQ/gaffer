# Scene Context #

<!-- TODO: convert to "Scene Context Methods" reference, and list the rest of the methods? -->

In the [Querying the Scene tutorial](../../Tutorials/Scripting/QueryingAScene/index.md), we demonstrated querying a scene using the `object()` method. In cases where you would want to query a scene at a particular frame, you would first need to establish a new context.


### "with" keyword ###

The `with` keyword establishes a new context, in which you can access evaluated context variables at a particular moment in time.

Assume you have a script that loads an animated camera and groups it to an asset, and you need to query the camera's height on frame 17. The following code would create a temporary context, set it to frame 17, then check the camera's position on the Y-axis:


```python
with Gaffer.Context( script.context() ) as newContext :
    newContext.setFrame( 17 )
    cameraPos = script["Group"]["out"].transform("/group/camera")
    print cameraPos
```


## See Also ##

- [Context](../Context/index.md)
