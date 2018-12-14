# Tutorial: Startup Configs, Part 3 # 

In this final part of the startup config tutorial, we will demonstrate a startup config that adds a custom entry to the node menu.

![A custom entry in the node menu](images/tutorialNodeMenuCustomEntry.png "A custom entry in the node menu")

The entry will insert a Reference node and load a reference script into it. The sub-graph inside the Reference node consists of an OSLCode node that procedurally generates a texture of a Macbeth chart. This "custom" node should come in handy for lookdev shader development, and, as a bonus, provides a simple demonstration of procedural texture generation in OSL.

Functionally, this node will be like a new node that came from a custom module. However, since the node is basically just an in-graph wrapper made of standard nodes, it will remain portable between Gaffer deployments, meaning that if it is saved inside a script, other users will not need to install additional modules in order to open that script.

We hope that this simple config will be a springboard for adding further entries to the node menu. This solution is very powerful, as it allows you to customize existing nodes or insert References to your Gaffer deployment, without needing to code or compile Gaffer modules.


## Startup Config #3: Custom Node Menu Entry ##

As with the other startup configs, this one will run in the GUI app. Copy this code to a new a `customNodes.py` file in `~/gaffer/startup/gui`:

```eval_rst
.. code-block:: python
    :linenos:

    import Gaffer
    import GafferUI
    import IECore
    import os

    def MacbethTexture( menu ) :

        graphEditor = menu.ancestor( GafferUI.GraphEditor )
        assert( graphEditor is not None )

        script = graphEditor.graphGadget().getRoot()
        node = Gaffer.Reference( "MacbethTexture" )
        script.addChild( node )
        node.load( os.path.expandvars( "$GAFFER_ROOT/resources/references/macbethTexture.grf" ) )

        return node

    nodeMenu = GafferUI.NodeMenu.acquire( application )
    nodeMenu.append( "/Custom/MacbethTexture", MacbethTexture, searchText = "MacbethTexture" )

```

The code only does two things: declare a function to add the node menu, then add it. Let's break it down.


### The node menu function ###

After first `import`ing the necessary modules, the config declares a function for creating the node: 

```eval_rst
.. code-block:: python
    :lineno-start: 6

    def MacbethTexture( menu ) :

```

When the user chooses our custom entry in the node menu, this is the function that the menu object will call. The only parameter for this function should be an implicit `menu` keyword.

> Caution :
> Do not declare any parameters other than `menu` in a node menu function. Otherwise, it will return an error.

Normally, all a node menu function needs to do is instance a node from an existing module, modify its plugs, and return it. The node menu's `append()` method takes care of the rest. 

However, due to a limitation in the current implementation of the way the `append()` method handles Reference nodes, we must parent the Reference node to the graph's root, otherwise it won't load the reference script. So, we need to guarantee that a _Graph Editor_ object exists, and then assign a variable to its graph root:

```eval_rst
.. code-block:: python
    :lineno-start: 8

        graphEditor = menu.ancestor( GafferUI.GraphEditor ) 
        assert( graphEditor is not None ) # Test for a parent graph editor object

        script = graphEditor.graphGadget().getRoot() # Grab the root of the graph
    
```

Next, the remainder of the function. We instance a Reference node, and load a reference script into it:

```eval_rst
.. code-block:: python
    :lineno-start: 12

        node = Gaffer.Reference( "MacbethTexture" )
        script.addChild( node ) # Make sure the node is parented to the graph root
        node.load( os.path.expandvars( "$GAFFER_ROOT/resources/references/macbethTexture.grf" ) )
        
        return node
```

There are two things that you should note here:

First, reference scripts can modify their containing Reference node's UI metadata, but not the node's name. We therefore have to set the Reference node's name ourselves (line 12, `"MacbethTexture"`). Otherwise, the node would appear in the graph with the generic name _Reference_. Any node menu function that requires a custom node name must do the same.

Second, on line 13 we add the node as a child of the graph's root. As mentioned earlier, if this were any other type of node, this step would be unnecessary, as `append()` would cover this for us.

```eval_rst
.. tip::

    You may have noticed on line 14 that we use ``os.path.expandvars`` to expand ``$GAFFER_ROOT``. If you kept the startup config from Part 1 of this tutorial, you could instead use:

    .. code-block:: python
        :lineno-start: 14

        resourcesPath = script["variables"]["projectResources"]["value"].getValue()
        node.load( resourcesPath + "/references/macbethTexture.grf" )

    This way, you can reuse variables added to the script itself, and make your code more portable.
```

In this particular example of a node menu function, we don't modify any of the node's plugs, but we could – such as automatically setting the `mode` plug to 1. Any such additional code would go here. For our function, though, this is the end.


### Adding the function to the node menu ###

At the end of the config, we add our function to the node menu. This part is as simple as grabbing the node menu object and making an `append()` call:

```eval_rst
.. code-block:: python
    :lineno-start: 18

    nodeMenu = GafferUI.NodeMenu.acquire( application ) # Make sure to use the node menu of the current application
    nodeMenu.append( "/Custom/MacbethTexture", MacbethTexture, searchText = "MacbethTexture" )
```

Line 18 merely grabs the node menu from the `application` variable. Recall that we used this variable in Parts 1 and 2 of this tutorial.

The `append()` convenience method is quite useful, as it wraps several other behind-the-scenes utility functions, and makes the node's creation undoable. There are typically only 3 arguments you would want to pass to it:

  1. The path to the node within the node menu's hierarchy. Each position in the hierarchy is separated by a forward slash. If a parent position doesn't exist yet, it will be created.
  2. The function itself. Note that we don't pass any arguments to it.
  3. `searchText`: the node's search keyword, for when the user searches for the node with the keyboard.

You can add more customized nodes to this config with similar ease, as long as each is managed by its own separate function and registered to the node menu with an `append()` call.


## Testing the Node Menu Entry ##

Now you can test the custom node. If you haven't already, save the startup config, then launch a new instance of Gaffer. In the _Graph Editor_, the new entry should appear in the node menu under _Custom_ > _MacbethTexture_, and create a MacbethTexture node when selected.

![The MacbethTexture node in the Graph Editor](images/tutorialMacbethTextureNode.png "The MacbethTexture node in the Graph Editor")


## Demo: Procedural Macbeth Chart ##

![Demo of the Macbeth texture assigned to a plane, to make a Macbeth chart](images/demoMacbethChart.png "Demo of the Macbeth texture assigned to a plane, to make a Macbeth cha")

In this demo, we create a procedurally-generated Macbeth chart by connecting a MacbethTexture node to the _color_ input plug of a surface shader, and then assigning the shader to a plane mesh with a width:height proportion of 3:2.

```eval_rst
    :download:`Download demo <demos/demoMacbethChart.gfr>`
```


## Recap ##

All three parts of this tutorial provided relatively simple examples, but we hope to have demonstrated that with just a bit of Python and a few files, you can easily customize the startup of the various Gaffer apps.


## See Also ##

- [MacbethTexture reference script](../../../../../resources/references/macbethTexture.grf)
- [Tutorial: Startup Configs, Part 1](../CreatingConfigurationFiles/index.md)
- [Tutorial: Startup Configs, Part 2](../CreatingConfigurationFiles2/index.md)
- [Gaffer's default startup configs](https://github.com/GafferHQ/gaffer/tree/!GAFFER_VERSION!/startup)
