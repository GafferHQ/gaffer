#! /bin/bash

set -e

gaffer screengrab -image images/scriptEditor.png -editor ScriptEditor -panel -scriptEditor.execute 'print "Hello World!", script'
gaffer screengrab -image images/scriptEditorGetValue.png -editor ScriptEditor -panel -scriptEditor.execute 'print "Hello World!", script'
gaffer screengrab scripts/node.gfr -selection Node -image images/nodeEditor.png -editor NodeEditor
gaffer screengrab scripts/sphere.gfr -selection Sphere -image images/scriptEditorGetValue.png -editor ScriptEditor -panel -scriptEditor.execute 'script["Sphere"]["radius"].getValue()'
gaffer screengrab scripts/meshToPoints.gfr -selection MeshToPoints -image images/meshToPointsViewer.png -editor Viewer
gaffer screengrab scripts/meshToPoints.gfr -selection MeshToPoints -image images/meshToPointsNodeGraph.png -editor NodeGraph
gaffer screengrab scripts/group.gfr -selection Group -image images/group.png -editor NodeGraph
