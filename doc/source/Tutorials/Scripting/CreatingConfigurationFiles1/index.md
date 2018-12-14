# Tutorial: Startup Configs, Part 1 #

Gaffer actually consists of multiple applications split between its major tasks, such as GUI (the main application interface), Dispatch, Execute, and Stats. These applications are easily extensible and customizable. On startup, each will load any number of arbitrary Python scripts, called **startup configs**, from default or custom startup paths. Startup configs can make calls to API hooks for extending or adding functionality to each app.

In this multi-part tutorial, we will walk through 3 example startup configs for the GUI app:

- <a href="#startup-config-1-customvariables-py">Startup config #1</a>: A config that adds a global context variable to all node graphs.
- [Startup config #2](../CreatingConfigurationFiles2/index.md): A config that adds file path bookmarks to the file browser inside Gaffer.
- [Startup config #3](../CreatingConfigurationFiles3/index.md): A config that adds a custom entry to the node menu.

This first config will be for the GUI app, and will add a path component as a global context variable called `${project:resources}`. The path will be to `/resources` in the Gaffer installation directory. Since we're adding it this context variable using a startup config, it will be automatically added to every node graph Gaffer opens or creates.

![A global context variable in a string plug](images/tutorialVariableSubstitutionInStringPlug.png "A global context variable in a string plug")


## Global Context Variables ##

Before we begin, a quick aside. **Global** context variables are context variables assigned to the node graph's root, and available to every node and plug at every point in the graph. They appear in the graph's settings (_File_ > _Settings_), under the _Variables_ tab.

There are also **default** global context variables. These are received from startup configs, and are added to all graphs. All graphs automatically receive the `project:name` and `project:rootDirectory` string context variables, which provide information to the graph for where to output renders and caches by default.

Assigning file path components to global context variables is an effective way to integrate the structure of your file system into graphs. If you have a network or asset management system, you can concatenate the components into paths that point to your scene caches, textures, reference scripts, etc. For example, consider this path built out of global context variables:

```
"/${showPath}/${sequencePath}/${shotPath}/${assetPath}"
```

If each global context variable were assigned to a path component, during a render, the evaluation engine could interpret it to something like:

```
"/SHOW_001/SEQ_001/SHOT_001/gafferBot"
```

Of course, the exact structure and naming convention would depend on your file system or asset management system.

With all that out of the way, onto the startup config.


## Startup Config #1: customVariables.py ## 

Copy this code to a new a `customVariables.py` file in `~/gaffer/startup/gui`:

```eval_rst
.. code-block:: python
    :linenos:

    import IECore
    import Gaffer

    def __scriptAdded( container, script ) :

        variables = script["variables"]

        if "projectResources" not in variables :
            projectResources = variables.addMember(
                "project:resources",
                IECore.StringData( "${GAFFER_ROOT}/resources/" ),
                "projectResources"
                )

        Gaffer.MetadataAlgo.setReadOnly( variables["projectResources"]["name"], True )

    application.root()["scripts"].childAddedSignal().connect( __scriptAdded, scoped = False )
```

Let's break down what's going on.

After `import`ing the necessary modules, we declare a function for adding a global context variable:

```eval_rst
.. code-block:: python
    :lineno-start: 4

    def __scriptAdded( container, script ) :
```

Both the arguments we pass are implicit, and specific to the method that will call this function.

Next, we grab the `variables` plug from the graph, which contains all the current global context variables. Then, we add an entry for the resources directory to it using the `addMember()` method.

```eval_rst
.. code-block:: python
    :lineno-start: 6

        variables = script["variables"] # All the global context variables in the graph

        if "projectResources" not in variables :
            projectResources = variables.addMember(
                "project:resources",
                IECore.StringData( "${GAFFER_ROOT}/resources/" ),
                "projectResources"
                )" )
```

The `addMember()` method takes three arguments:
1. Plug name: The string for the variable that is accessible in the graph. Can be used in variable substitutions. The colon we use in `project:resources` has no significance to the interpreter. Colons are used merely by convention and for readability.
2. Plug value: The default value. You can use any standard plug types, such as floats, integers, `V3f`, `V2i`, etc. If the type comes from a special module (such as `imath`), make sure to `import` it first.
3. Variable name: The key name for the variable, only used in the API.

> Note :
> In the _Python Editor_, unlike regular plugs, you cannot retrieve values from `root["variables"]` with the `getValue()` method.

Notice that in the plug value we provided, we used the `${GAFFER_ROOT}` variable substitution as a path component, since it already points to the installation directory.

We then finish the function by setting the new variable's name as read-only, to protect it from accidental deletion by users and nodes:

```eval_rst
.. code-block:: python
    :lineno-start: 15

        Gaffer.MetadataAlgo.setReadOnly( variables["projectResources"]["name"], True )
```

Finally, we complete the config by adding the function to the event signal for opening and creating node graphs:

```eval_rst
.. code-block:: python
    :lineno-start: 17

    application.root()["scripts"].childAddedSignal().connect( __scriptAdded, scoped = False )
```

Notice the use of the `application` variable. This is a special variable, available in all startup configs, that refers to the current Gaffer instance. Since multiple Gaffer graphs can be open at once, it's necessary to ensure that we're modifying the current graph.


## Testing the Global Context Variable ##

Now we can test the effect of the startup config. If you haven't already, save `customVariables.py`, then launch a new instance of Gaffer. In the empty graph, take a look at the global context variables found in the _Variables_ tab of the graph's settings (_File_ > _Settings_). You should see the new `project:resources` variable with the correct value.

![The custom global context variable in the Settings window](images/tutorialSettingsWindowCustomContextVariable.png "The custom global context variable in the Settings window")

Every subsequent node graph you open or create will have the `project:resources` global context variable added to it. Try using it to load Gaffy's scene cache:

1. Create a SceneReader node.
2. In the _Node Editor_, set the _File Name_ plug to `${project:resources}/gafferBot/caches/gafferBot.scc`.

If all went well, Gaffy's geometry cache should have loaded in the graph.

![Successfully reading Gaffy using variable substitution in a string](images/tutorialVariableSubstitutionTest.png "Successfully reading Gaffy using variable substitution in a string")

As mentioned earlier, if you wanted to make the path more modular, you could further divide the path by sub-directory, and assign a global context variable to each.


## Environment Variables and Context Variables ##

Before concluding Part 1 of this tutorial, we should clarify one point about variable substitutions and path components.

In string plugs, both environment variables and context variables use the same variable substitution syntax: `${variable}`. They are not, however, the same. Context variables can be modified during the node graph's execution, while environment variables are set outside of Gaffer's scope.

In a live Gaffer window, you can test whether a string will substitute for an environment variable in the _Python Editor:_

```python
import os

"GAFFER_ROOT" in os.environ  # True
"projectResources" in os.environ  # False
```

If your studio uses environments variables to define file system directories or path components, it would be a better choice to use them, rather than global context variables, in your file paths inside Gaffer.


## Quick Recap ##

Adding custom global context variables to your node graphs is a fairly simple affair. With them, you can build implicit file paths, making your graph's content sources modular.

In the next part of this tutorial, we will demonstrate some UI modification, with a startup config that adds path bookmarks to the file browser.


## See Also ##

- [Tutorial: Startup Configs, Part 2](../CreatingConfigurationFiles2/index.md)
- [Tutorial: Startup Configs, Part 3](../CreatingConfigurationFiles3/index.md)
- [Gaffer's default startup configs](https://github.com/GafferHQ/gaffer/tree/!GAFFER_VERSION!/startup)
