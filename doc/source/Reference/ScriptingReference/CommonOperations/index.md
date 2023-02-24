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

### Get a node or plug name

```
name = node.getName()
```

### Get a node or plug name relative to an ancestor

```
name = node["plugName"].relativeName( root )
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
destinationNode["destinationPlugName"].setInput( sourceNode["sourcePlugName"] )
```

### Break a connection

```
node["plugName"].setInput( None )
```

### Get a plug's input connection

```
input = node["plugName"].getInput()
```

### Get a plug's output connections

```
outputs = node["plugName"].outputs()
```

### Get all child plugs from a node

```
plugs = node.children( Gaffer.Plug )
```

### Get the node from a plug

```
node = plug.node()
```

### Get the parent of a node or plug

```
parent = node.parent()
```

### Get a node's ancestor of type Gaffer.ScriptNode

```
script = node.ancestor( Gaffer.ScriptNode )
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

### Loop over child nodes of type GafferScene.Sphere

```
for node in GafferScene.Sphere.Range( root ) :
	...
```

### Loop over all descendant nodes of type Gaffer.Box

```
for node in Gaffer.Box.RecursiveRange( root ) :
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

### Load a script

```
root["fileName"].setValue( "/path/to/file.gfr" )
root.load()
```

### Export a reference

```
root["boxToExport"].exportForReference( "/path/to/file.grf" )
```

### Load a reference

```
referenceNode = Gaffer.Reference()
root.addChild( referenceNode )
referenceNode.load( "/path/to/file.grf" )
```

### Query a script variable

```
root.context()["project:rootDirectory"]
```

### Get selected nodes

```
root.selection()
```

### Select a node

```
root.selection().clear()
root.selection().add( root["nodeName"] )
```

### Get the frame range

```
start = root["frameRange"]["start"].getValue()
end = root["frameRange"]["end"].getValue()
```

### Set the current frame

```
root.context().setFrame( frame )
```

### Get the playback range

```
GafferUI.Playback.acquire( root.context() ).getFrameRange()
```

### Set the playback range

```
GafferUI.Playback.acquire( root.context() ).setFrameRange( start, end )
```

### Set node as numeric bookmark 1

```
Gaffer.MetadataAlgo.setNumericBookmark( root, 1, root["nodeName"] )
```

### Get the node set as numeric bookmark 1

```
Gaffer.MetadataAlgo.getNumericBookmark( root, 1 )
```

### Set a node as the focus node

```
root.setFocus( root["nodeName"] )
```

### Get the currently focussed node

```
root.getFocus()
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

### Find plugs/nodes with specific metadata

```
Gaffer.Metadata.plugsWithMetadata( root, "name" )
Gaffer.Metadata.nodesWithMetadata( root, "name" )
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

### Get the world space bounding box of a location

```
bound = node["out"].bound( "/path/to/location" ) * node["out"].fullTransform( "/path/to/location" )
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
