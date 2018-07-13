# Context #

In Gaffer's parallel computing engine, there is no concept of a single “current time.” All threads evaluate with a Context object, which defines a dictionary of context-related values in which a computation is performed. The most basic entry common to all contexts is the frame number. Other context values include the frame rate, current time in the sequence, and any scene, image, text, and global script context variables.

Contexts allow Gaffer to multithread efficiently. Each thread uses its own Context class, so they can each query a different part of the scene or a different location in an image. Because each thread maintains its own stack of contexts, anything can be computed at any frame at any time, and computations can launch upstream computations in other contexts. This is how Gaffer's UI is capable of viewing the scene in different contexts, such as having one _Viewer_ show frame 1 of a sequence and another _Viewer_ show frame 2.

The Context class is central to how Gaffer works: a plug can output entirely different values depending on the context in which it was called.


## context() Function and the “context” Variable ##

A computation's context is accessed by invoking the `context()` function on the script variable, or the context variable (not to be confused with general-purpose context variables <!-- TODO: link to article -->). When invoked, they provide values given that particular context.

Whether to invoke context by the function or the variable depends on the environment:

```eval_rst
* :ref:`In the Script Editor<Invoking Context>`
* :ref:`In an Expression node<Invoking the Context>`
```

<!-- TODO: should be moved to the general-purpose context variable article -->

## Context in String Plugs ##

String plugs can access the value of any context variable through the `${}` [template literal](../../Reference/ScriptingReference/StringSubstitutionSyntax/index.md) with a variable (without quotation marks) into a string plug's value. For example, the `frame` context variable would be referenced with `${frame}`. When the string plug is evaluated by a computation, the parser will replace the literal with the context variable's value.


## See Also ##

- [Scene Context](../SceneContext/index.md)
- [Special Variables](../SpecialVariables/index.md)

<!-- TODO: - [Context Variables](../ContextVariables/index.md) -->
<!-- TODO: - [Context Method Reference](../../Reference/ScriptingReference/ContextMethods/index.md) -->
