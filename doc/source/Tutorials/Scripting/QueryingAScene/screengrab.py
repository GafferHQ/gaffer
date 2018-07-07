# BuildTarget: images/scriptOutputCompoundObject.png

import os
import inspect
import IECore
import imath

import Gaffer
import GafferScene
import GafferUI

# Adjust Script Editor window's height
def __resize( y ) :
	scriptEditorWindow._qtWidget().resize( 690, y )

# Reset output text, add new input text, execute
def __executeText( text ) :
	scriptEditor.outputWidget().setText( "" )
	scriptEditor.inputWidget().setText( inspect.cleandoc( text ) + "\n\n" )
	scriptEditor.execute()

# Open Script Editor window
with GafferUI.Window( "Script Editor" ) as scriptEditorWindow :
	scriptEditor = GafferUI.ScriptEditor( script )
scriptEditorWindow.setVisible( True )

# CompoundObject output in Script Editor
script["fileName"].setValue( os.path.abspath( "scripts/QueryingAScene.gfr" ) )
script.load()
__executeText( '''script["StandardOptions"]["out"]["globals"].getValue()\n\n''' )
__resize( 180 )
GafferUI.WidgetAlgo.grab( widget = scriptEditor.outputWidget(), imagePath = "images/scriptOutputCompoundObject.png" )

# Global settings in Script Editor
__executeText( '''
	globals = script["StandardOptions"]["out"]["globals"].getValue()
	print type( globals )
	print globals.keys()
	print globals["option:render:camera"].value
	print globals["option:render:resolution"].value
	''' )
__resize( 380 )
GafferUI.WidgetAlgo.grab( widget = scriptEditor.outputWidget(), imagePath = "images/scriptOutputGlobals.png" )

# Camera object output in Script Editor
__executeText( '''
	camera = script["StandardOptions"]["out"].object( "/world/camera" )
	print camera
	''' )
__resize( 180 )
GafferUI.WidgetAlgo.grab( widget = scriptEditor.outputWidget(), imagePath = "images/scriptOutputCameraObject.png" )

# Camera object parameters output in Script Editor
__executeText( '''
	print camera.parameters().keys()
	print camera.parameters()["projection"].value
	print camera.parameters()["projection:fov"].value
	print camera.parameters()["clippingPlanes"].value
	''' )
__resize( 380 )
GafferUI.WidgetAlgo.grab( widget = scriptEditor.outputWidget(), imagePath = "images/scriptOutputCameraObjectParameters.png" )

# Camera object transform output in Script Editor
__executeText( 'script["StandardOptions"]["out"].transform( "/world/camera" )' )
__resize( 180 )
GafferUI.WidgetAlgo.grab( widget = scriptEditor.outputWidget(), imagePath = "images/scriptOutputCameraObjectTransform.png" )

# Custom scene attributes in Script Editor
__executeText( '''
	attributes = script["StandardOptions"]["out"].attributes( "/world/geometry/sphere" )
	print attributes.keys()
	print attributes["myString"].value
	''' )
__resize( 380 )
GafferUI.WidgetAlgo.grab( widget = scriptEditor.outputWidget(), imagePath = "images/scriptOutputCustomAttributes.png" )

# Partial scene traversal in Script Editor
__executeText( '''
	print script["StandardOptions"]["out"].childNames( "/" )
	print script["StandardOptions"]["out"].childNames( "/world" )
	''' )
__resize( 180 )
GafferUI.WidgetAlgo.grab( widget = scriptEditor.outputWidget(), imagePath = "images/scriptOutputTraversal.png" )

# Full scene traversal in Script Editor
__executeText( '''
	import os
	   
	def visit( scene, path ) :
	   print path
	   print "   Transform : " + str( scene.transform( path ) )
	   print "   Object : " + scene.object( path ).typeName()
	   print "   Attributes : " + " ".join( scene.attributes( path ).keys() )
	   print "   Bound : " + str( scene.bound( path ) ) + "\\n"
	   for childName in scene.childNames( path ) :
	      visit( scene, os.path.join( path, str( childName )  ) )
	   
	visit( script["StandardOptions"]["out"], "/" )\n
	''' )
scriptEditor.inputWidget().setVisible( False )
__resize( 640 )
GafferUI.WidgetAlgo.grab( widget = scriptEditor.outputWidget(), imagePath = "images/scriptOutputFullTraversal.png" )
