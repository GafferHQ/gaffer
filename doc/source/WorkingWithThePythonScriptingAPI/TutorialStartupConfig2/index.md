# Tutorial: Startup Config 2; Custom Bookmarks ##

In this second startup config of the tutorial, we will add default path bookmarks to Gaffer's file browsers.

![](images/tutorialBookmarks.png "The bookmarks in a Gaffer file browser")

In the file browsers inside the Gaffer application, users have the option of bookmarking file paths. In a studio pipeline, it could be beneficial to provide artists with some centrally-deployed  bookmarks to relevant locations on the file system. Giving every artist a common set – or a project-specific set – of bookmarks could help standardize their workflows. User path bookmarks are maintained separately from default bookmarks, so the artists' personal bookmarks would not be at risk.

With GUI again as our target app, this config will:
- Add a default bookmark, available to all file browsers in Gaffer.
- Add a category-specific default bookmark, available only to image-related file browsers.
- Set the starting directory for image-related file browsers.


## customBookmarks.py ##

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

    bookmarks = GafferUI.Bookmarks.acquire( application, category = "image" )
    picturesPath = os.path.expandvars( "$HOME/Pictures" )
    bookmarks.add( "Pictures", picturesPath )
```

Let's break down what this config does.


### Adding a default bookmark ###

Path bookmarks exist separately in each application instance, so we must first acquire the bookmarks from the the correct Gaffer window. We do this by passing the special `application` variable to the `acquire` method:

```eval_rst
.. code-block:: python
    :lineno-start: 5

    bookmarks = GafferUI.Bookmarks.acquire( application )
```

Then, we simply pass a name for the bookmark and a file system path using the `add()` method.

> Important :
> Bookmarks are stored as plain strings, not typed plugs. Any variable substitutions therein must be formatted like they would be in a terminal, without curly braces (for example, `$variable`).

Since we're targeting the Gaffer installation directory, we use the `$GAFFER_ROOT` variable substitution to stand in for the `GAFFER_ROOT` environment variable, and expand it using a standard Python method:

```eval_rst
.. code-block:: python
    :lineno-start: 6

    resourcesPath = os.path.expandvars( "$GAFFER_ROOT/resources" )
    bookmarks.add( "Resources", resourcesPath )
```

That's all we need to add a default bookmark to Gaffer's file browsers. Try testing the config:

1. If you haven't already, save `customBookmarks.py`, then launch a new instance of Gaffer.
2. Create a SceneReader node (_Scene_ > _File_ > _Reader_).
3. In the Node Editor, click ![](images/pathChooser.png "file browser").
4. In the file browser, click ![](images/bookmarks.png "bookmarks").

If all goes well, _Resources_ should be in the list of bookmarks:

![](images/tutorialDefaultBookmark.png "A custom default bookmark in a file browser")

You may have noticed that we used a global Context Variable for a path in the first startup config of this tutorial, but not here. The reason is simply that global Context Variables are plugs stored per-node graph, whereas path bookmarks are stored in the application.


### Adding a category-specific default bookmark ###

The next section of the code adds another default bookmark, but this time to a specific **category**, which is a string keyword you can associate with various parts of the GUI. If a node has a category that matches a bookmark's category, file browsers for that node will contain that bookmark.

To add a bookmark to a category, we acquire all of the application's the bookmarks like before, only we provide a string as the `category` keyword argument. The category keyword for the default image nodes is simply image`.

```eval_rst
.. code-block:: python
    :lineno-start: 9

    bookmarks = GafferUI.Bookmarks.acquire( application, category = "image" )
    picturesPath = os.path.expandvars( "$HOME/Pictures" )
    bookmarks.add( "Pictures", picturesPath )
```

This should bookmark your `~/Pictures` direcotry for all image node file browsers. Try testing it:

1. Create a Catalogue node.
2. In the Node Editor, In the _Images_ tab, click ![](images/pathChooser.png "file browser").
3. In the file browser, click ![](images/bookmarks.png "bookmark"). _Pictures_ should be in the list of bookmarks.

![](images/tutorialDefaultImageNodeBookmark.png "A custom default bookmark in an image node's file browser")

Since this points to a directory in the user's home folder, this isn't the most realistic example for a bookmark in a studio pipeline, but it should provide an example basis from which to incorporate your own asset and resource locations as bookmarks. Using Python string manipulation, you can compose multi-component strings from several Context Variables or environment variables that point to locations in your file system.


### Setting the file browser default path ###

When you open the file browser for an empty string plug, it begins at a default path. This path is actually another bookmark, which you can also change through the API. Let's try setting the default path for all image nodes.

Since the `bookmarks` variable we declared earlier only contains bookmarks belonging to the `image` category, and we already have the `picturesPath` variable that points to `~/Pictures`,  we can reuse both in combination with the `setDefault()` method.

Add the following to the end of the config:

```eval_rst
.. code-block:: python
    :lineno-start: 12

    bookmarks.setDefault( picturesPath )
```

Now, try testing an image node's default file browser path:

1. Save `customBookmarks.py`, then launch a new instance of Gaffer.
2. Create a Catalogue node.
3. In the Node Editor, in the _Images_ tab, click ![](images/pathChooser.png "file browser").

If all goes well, the file path should default to `~/Pictures`.

![](images/tutorialDefaultImageNodePath.png "A custom default path in an image node's file browser")

> Caution :
> We recommend removing this last line from the config, as it will override the default file browser paths for image nodes with an unrealistic filesystem path that has little utility in a studio environment.


## Quick recap ##

As you can see, the runtime Python objects of an app, in this case the GUI's bookmarks, can be modified easily with startup configs. In the last startup config of this tutorial, we will edit the node menu by adding a custom node to it.


## See also ##

- [Tutorial: Startup Config 3; Custom Node Menu Entries](../TutorialStartupConfig3/index.md)
- [Tutorial: Startup Config 1; Custom Global Context Variables](../TutorialStartupConfig1/index.md)
- [Gaffer's default startup configs](https://github.com/GafferHQ/gaffer/tree/master/startup)

