<!-- !NO_SCROLLSPY -->

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
Get value           value = parent["NodeName"]["plugName"]   value = parent.NodeName.plugName
Set value           parent["NodeName"]["plugName"] = value   parent.NodeName.plugName = value
=================== ======================================== ================================
```

Context Variables
-----------------

```eval_rst
================================ =========================================== =======================================
Operation                        Python                                      OSL
================================ =========================================== =======================================
Get variable                     context["variableName"]                     context( "variableName" )
Get with default                 context.get( "variableName", default )      context( "variableName", default )
================================ =========================================== =======================================
```
