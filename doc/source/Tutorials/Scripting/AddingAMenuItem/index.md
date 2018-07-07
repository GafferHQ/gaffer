# Tutorial: Adding a Menu Item #

This tutorial addresses how to add menu items. It will cover:

- Adding an item to the main menu
- Referencing the main application window
- Using the undo context

Before you begin, we recommend you complete the [Creating a Configuration File](../CreatingConfigurationFiles/index.md) tutorial.

> Tip :
> This tutorial focuses on the main menu, but you can find examples for adding menu items to the _Graph Editor_, _Node Editor_, and more in [Gaffer's default configuration files](https://github.com/GafferHQ/gaffer/tree/!GAFFER_VERSION!/startup/gui).


## Creating the Script ##

Through Gaffer's startup environment variable, you can create your own startup scripts in `~/gaffer/startup/gui/`. Before you begin, create a new file `insertCows.py` in that directory.


## Writing the script ##

Through this section, we will build the script piece by piece.

First, the startup script needs an `__insertCows` function. Since Gaffer can have multiple scripts (files) open at once, you will first need to specify which script to access before the function can modify it. This can be easily determined based on which window the menu was invoked from using the `ancestor()` method:

```python
    def __insertCows( menu ) :
    	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
    	script = scriptWindow.scriptNode()
```

> Note :
> Later, when the function is added to a menu, the `menu` variable that it implicitly takes as input will be passed by the parent menu.

Ideally, any function that modifies the scene should be undoable. To make the function's commands undoable, they should be wrapped in an `UndoContext()`:

```python
with Gaffer.UndoContext( script ) :
	...
```

Now we can create a _SceneReader_ node to load the cow's geometry, and a _Duplicate_ node to copy and rotate it.

```python
	reader = GafferScene.SceneReader( "Cow" )
	reader["fileName"].setValue( "${GAFFER_ROOT}/resources/cow/cow.scc" )
	script.addChild( reader )
	duplicate = GafferScene.Duplicate( "Herd" )
	duplicate["target"].setValue( "/cow" )
	duplicate["copies"].setValue( 7 )
	duplicate["transform"]["translate"]["x"].setValue( 16 )
	duplicate["transform"]["rotate"]["y"].setValue( 45 )
	duplicate["in"].setInput( reader["out"] )
	script.addChild( duplicate )
```

Finally, the function should select the newly created scene, to signal to the user that their insert succeeded. The selection does not need to be undoable, so it will escape the scope of the `undoContext()`:

```python
script.selection().clear()
script.selection().add( duplicate )
```

### Creating the menu item ###

Now the function needs to be added to a menu. For simplicity, the startup script will add the new menu item to the application's main menu, which is hosted in the main script window:

```python
GafferUI.ScriptWindow.menuDefinition( application ).append( "/Help/Insert Cows", { "command" : __insertCows } )
```

Most user interfaces in Gaffer can be referenced and extended with similar ease. In this case, the code simply specified the `GafferUI.ScriptWindow` object, and called the `append()` method to add a path to a new menu item, with the result of executing the `__insertCows` function.

Save the startup script, and launch Gaffer. The menu item will now produce this result in any script:

![Circle of cows, in the Viewer](images/viewerCows.png "Circle of cows, in the Viewer")


## The Final File ##

Here is the final result of `~/gaffer/startup/gui/insertCows.py`:

```python
import Gaffer
import GafferUI
import GafferScene

def __insertCows( menu ) :
	scriptWindow = menu.ancestor( GafferUI.ScriptWindow )
	script = scriptWindow.scriptNode()

	with Gaffer.UndoContext( script ) :
		reader = GafferScene.SceneReader( "Cow" )
		reader["fileName"].setValue( "${GAFFER_ROOT}/resources/cow/cow.scc" )
		script.addChild( reader )
		duplicate = GafferScene.Duplicate( "Herd" )
		duplicate["target"].setValue( "/cow" )
		duplicate["copies"].setValue( 7 )
		duplicate["transform"]["translate"]["x"].setValue( 16 )
		duplicate["transform"]["rotate"]["y"].setValue( 45 )
		duplicate["in"].setInput( reader["out"] )
		script.addChild( duplicate )

	script.selection().clear()
	script.selection().add( duplicate )

GafferUI.ScriptWindow.menuDefinition(application).append( "/Help/Insert Cows", { "command" : __insertCows } )
```


## See Also ##

- [Tutorial: Creating a Configuration File](../CreatingConfigurationFiles/index.md)

<!-- - [Using the Script Editor](../UsingTheScriptEditor/index.md) -->
