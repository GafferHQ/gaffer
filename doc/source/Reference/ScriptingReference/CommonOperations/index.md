Common Operations
=================

Node Graphs
-----------

### Create a node

```
import GafferScene
node = GafferScene.Sphere()
root.addChild( node )
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

### Get a node by name

```
node = root["nodeName"]
```

### Loop over all nodes

```
for node in root.children( Gaffer.Node ) :
	...
```

### Get the current filename

```
root["fileName"].getValue()
```

### Serialize the node graph to file

```
root.serialiseToFile( "/path/to/file.gfr" )
```

### Query a script variable

```
root.context()["project:rootDirectory"]
```

### Select a node

```
root.selection().clear()
root.selection().add( root["nodeName"] )
```

### Get the frame range

```
start = root['frameRange']['start'].getValue()
end = root['frameRange']['end'].getValue()
```

### Set the current frame

```
root.context().setFrame( frame )
```

Metadata
--------

### Register a value for a plug/node

```
Gaffer.Metadata.registerValue( plug, "name", value )
Gaffer.Metadata.registerValue( node, "name", value )
```

### Query a value for a plug/node

```
Gaffer.Metadata.value( plug, "name" )
Gaffer.Metadata.value( node, "name" )
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
		visit( scene, path.rstrip( "/" ) + "/" + str( childName ) )

visit( node["out"], "/" )
```
