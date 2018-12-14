# Tutorial: Startup Configs, Part 2 ##

In this second part of the tutorial, we will demonstrate a startup config that adds default path bookmarks to Gaffer's file browsers.

![The bookmarks in a Gaffer file browser](images/tutorialBookmarks.png "The bookmarks in a Gaffer file browser")

With the file browsers in the Gaffer UI, users have the option to save and load paths as bookmarks. In a studio pipeline, it could be beneficial to provide artists with some centrally-deployed, default path bookmarks to locations on the file system. Giving every artist a common set of bookmarks is a good way to help standardize workflows. User path bookmarks are maintained separately from default bookmarks, so there's no risk to the user's personal bookmarks.

With GUI again as our target app, our config will:
- Add a default bookmark, available to all Gaffer file browsers.
- Add a category-specific default bookmark, available to image node file browsers.
- Set the starting directory for image node file browsers.


## Startup Config #2: customBookmarks.py ##

Copy this code to a new a `customBookmarks.py` file in `~/gaffer/startup/gui`:

```eval_rst
.. code-block:: python
    :linenos:

    import os
    import Gaffer
    import GafferUI

    bookmarks = GafferUI.Bookmarks.acquire( application )
    resourcesPath = os.path.expandvars( "$GAFFER_ROOT/resources" )
    bookmarks.add( "Resources", resourcesPath )

    bookmarks = GafferUI.Bookmarks.acquire( application, category="image" )
    picturesPath = os.path.expandvars( "$HOME/Pictures" )
    bookmarks.add( "Pictures", picturesPath )
```

Let's break down what this config does.


### Adding a default bookmark ###

As with global context variables, path bookmarks exist separately in each app instance, so we must first acquire the bookmarks from the the correct Gaffer window. Like before, we do this by passing the special `application` variable:

```eval_rst
.. code-block:: python
    :lineno-start: 5

    bookmarks = GafferUI.Bookmarks.acquire( application )
```

Then, we simply pass a name for the bookmark and a file system path using the `add()` method. Since we're targeting the Gaffer installation directory, we use the `$GAFFER_ROOT` variable substitution to stand in for the `GAFFER_ROOT` environment variable, and expand it using a standard Python method:

```eval_rst
.. code-block:: python
    :lineno-start: 6

    resourcesPath = os.path.expandvars( "$GAFFER_ROOT/resources" )
    bookmarks.add( "Resources", resourcesPath )
```

> Important :
> The bookmarks object stores plain strings, not plugs. This means that variable substitutions should be formatted like in a terminal (`$variable`), without curly braces.

That's all that's needed for adding a default bookmark to Gaffer's file browsers. Try testing the bookmark:

1. Launch a new instance of Gaffer.
2. Create a SceneReader node (_Scene_ > _File_ > _Reader_).
3. In the _Node Editor_, click ![file browser](images/pathChooser.png "File browser").
4. In the file browser, click ![bookmarks](images/bookmarks.png "Bookmarks"). _Resources_ should be in the list of bookmarks.

![A custom default bookmark in a file browser](images/tutorialDefaultBookmark.png "A custom default bookmark in a file browser")

You may have noticed that we used a global context variable for a path in Part 1 of this tutorial, but not here. This is simply because global context variables are plug stored in the graph, whereas path bookmarks are stored in the application.


### Adding a category-specific default bookmark ###

The next section of the code adds another default bookmark, but this time to a specific **node category**. If a node has a category that matches a bookmark's category, file browsers attached to that node will have that bookmark.

To add a bookmark to a node category, we acquire the bookmarks like before, only we provide a string as the `category` keyword argument. The string for the default image nodes is simply `"image"`.

```eval_rst
.. code-block:: python
    :lineno-start: 9

    bookmarks = GafferUI.Bookmarks.acquire( application, category="image" )
    picturesPath = os.path.expandvars( "$HOME/Pictures" )
    bookmarks.add( "Pictures", picturesPath )
```

Now, all the default image nodes will have a file browser bookmark to `~/Pictures`. Try out the node bookmark:

1. Create a Catalogue node.
2. In the _Node Editor_, In the _Images_ tab, click the ![file browser](images/pathChooser.png "File browser").
3. In the file browser, click ![bookmark](images/bookmarks.png). _Pictures_ should be in the list of bookmarks.

![A custom default bookmark in an image node's file browser](images/tutorialDefaultImageNodeBookmark.png "A custom default bookmark in an image node's file browser")

Since this points to a directory in the user's home folder, this isn't the most realistic example for a bookmark in a studio pipeline, but it should provide an example basis from which to incorporate your own custom asset locations as bookmarks. Using Python string manipulation, you can compose multi-component strings from several environment variables that point to locations in your file system or asset management system.


### Setting the file browser default path ###

When you open a file browser for a blank string plug, it provides a default fallback path to start browsing from. This default path is actually another bookmark, and the API has a method for setting it. In this last section, we'll demonstrate this.

Since `bookmarks` already contains only bookmarks belonging to the `"image"` category, we've reused it. All that's needed is pass a path to the bookmarks using `setDefault()` method.

Add this to the end of the config:

```eval_rst
.. code-block:: python
    :lineno-start: 12

    bookmarks.setDefault( picturesPath )
```

Try it out:

1. Save the startup config.
2. Open a new instance of Gaffer.
3. Create a Catalogue node.
4. In the _Node Editor_, in the _Images_ tab, click ![file browser](images/pathChooser.png "File browser").
5. The file browser should target `~/Pictures` by default.

![A custom default path in an image node's file browser](images/tutorialDefaultImageNodePath.png "A custom default path in an image node's file browser")

> Caution :
> We recommend removing this last line from this config, as it will override the default file browser paths for image nodes with an unrealistic filesystem path that has little utility.


## Quick Recap ##

As you can see, simple UI properties of an app, such as bookmarks, can be modified easily with startup configs. In Part 3 of this tutorial, we will edit a more commonly used UI element, by registering a custom function to it.


## See Also ##

- [Tutorial: Startup Configs, Part 3](../CreatingConfigurationFiles3/index.md)
- [Tutorial: Startup Configs, Part 1](../CreatingConfigurationFiles/index.md)
- [Gaffer's default startup configs](https://github.com/GafferHQ/gaffer/tree/!GAFFER_VERSION!/startup)

