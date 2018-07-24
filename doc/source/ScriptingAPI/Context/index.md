# Context #

In Gaffer, there is no concept of a single “current time.” In Gaffer's parallel computation engine, all computation threads have a current Context object, which determines the specific parts of the scene or image at a particular moment in the sequence that need computing. Contexts allow Gaffer to multithread efficiently. Because each thread maintains its own stack of contexts, anything can be computed at any frame at any time, and computations can launch upstream computations in other contexts. This is how Gaffer's UI is capable of displaying a scene in several different contexts at once, such as having one _Viewer_ show frame 1 of a sequence and another _Viewer_ show frame 2.

<!-- TODO: split off into separate context variable article -->

Each Context object defines a dictionary of context-related variables in which the computation is performed. The most basic context variable is `frame`, for the frame number. Scene- and image-specific context variables also exist, such as which part of a scene (`scene:path`) or region of an image (`image:tileOrigin`) will compute. Gaffer uses many other context variables for threading and computation, however not all of them are useful to artists or a VFX pipeline.


## context() Function and the “context” Variable ##

Within a Gaffer script, a computation's context is accessed by invoking the `context()` function on the `script` variable, or by using the `context` variable (not to be confused with general-purpose context variables <!-- TODO: link to article -->) itself. When invoked, they provide values given that particular context.

Whether to invoke context by the function or the variable depends on the environment:

```eval_rst
* In the :ref:`Script Editor<Invoking Context>`, use the ``context()`` function
* In an :ref:`Expression node<Invoking the Context>`, use the ``context`` variable
```

<!-- TODO: should be moved to the general-purpose context variable article -->

## Context in String Plugs ##

String plugs can access the value of any context variable through the `${}` [template literal](../../Reference/ScriptingReference/StringSubstitutionSyntax/index.md). For example, the `frame` context variable would be referenced with `${frame}`. When the string plug is evaluated, the parser will replace the literal with the context variable's value.


## See Also ##

- [Scene Context](../SceneContext/index.md)
- [Special Variables](../SpecialVariables/index.md)
- [Expressions Reference](../../Reference/Expressions/index.md)

<!-- TODO: - [Context Variables](../ContextVariables/index.md) -->
<!-- TODO: - [Context Method Reference](../../Reference/ScriptingReference/ContextMethods/index.md) -->
