Expressions
===========

Time
----

```eval_rst
=================== ============================== ============================
Operation           Python                         OSL
=================== ============================== ============================
Get current time    context.getTime()              time
Get current frame   context.getFrame()             context( "frame" )
Get frame rate      context.getFramesPerSecond()   context( "framesPerSecond" )
=================== ============================== ============================
```

Plugs
-----

```eval_rst
=================== ======================================== ================================
Operation           Python                                   OSL
=================== ======================================== ================================
Get value           value = root["NodeName"]["plugName"]     value = root.NodeName.plugName
Set value           root["NodeName"]["plugName"] = value     root.NodeName.plugName = value
=================== ======================================== ================================
```

Context variables
-----------------

```eval_rst
================================ =========================================== =======================================
Operation                        Python                                      OSL
================================ =========================================== =======================================
Get variable                     context["variableName"]                     context( "variableName" )
Get with default                 context.get( "variableName", default )      context( "variableName", default )
================================ =========================================== =======================================
```
