Common Operations
=================

Node Graphs
-----------

### Create a node

```
import GafferScene
node = GafferScene.Sphere()
script.addChild( node )
```

### Rename a node

```
node.setName( "newName" )
```

### Get a plug value

```
value = node["plugName"].getValue()
```

### Set a plug value

```
node["plugName"].setValue( value )
```

### Make a connection

```
destinationNode["destinationPlugName"].setInput( sourceNode["sourceNode"] )
```

### Break a connection

```
node["plugName"].setInput( None )
```

Script nodes
------------

### Get a node by name

```
node = script["nodeName"]
```

### Loop over all nodes

```
for node in script.children( Gaffer.Node ) :
	...
```

### Get the current filename

```
script["fileName"].getValue()
```

### Save a copy

```
script.serialiseToFile( "/path/to/file.gfr" )
```

### Query a script variable

```
script.context()["project:rootDirectory"]
```

### Select a node

```
script.selection().clear()
script.selection().add( script["nodeName"] )
```

### Get the frame range

```
start = script['frameRange']['start'].getValue()
end = script['frameRange']['end'].getValue()
```

### Set the current frame

```
script.context().setFrame( frame )
```

Scenes
------

### Get an option

```
g = node["out"]["globals"].getValue()
o = g["option:render:camera"].value
```

### Get an object at a location

```
o = node["out"].object( "/path/to/location" )
```

### Get the local transform at a location

```
matrix = node["out"].transform( "/path/to/location" )
```

### Get the full (world) transform at a location

```
node["out"].fullTransform( "/path/to/location" )
```

### Get the local bounding box of a location

```
bound = node["out"].bound( "/path/to/location" )
```

### Get the local attributes of a location

```
attributes = node["out"].attributes( "/path/to/location" )
attribute = attributes["name"].value
```

### Get the full (inherited + local) attributes of a location

```
attributes = node["out"].fullAttributes( "/path/to/location" )
attribute = attributes["name"].value
```

### Recurse through the scene hierarchy

```
def visit( scene, path ) :

	for childName in scene.childNames( path ) :
		visit( scene, os.path.join( path, str( childName )  ) )

visit( node["out"], "/" )
```
