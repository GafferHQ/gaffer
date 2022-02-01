##########################################################################
#
#  Copyright (c) 2021, Murray Stevenson. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import functools
import imath
import re
import struct

import IECore

import Gaffer
import GafferUI
import GafferImage
import GafferScene
import GafferSceneUI

def _idToManifestKey( value ) :
	# Cryptomatte manifest keys are stored as strings containing the uint32 representation of the hashed name
	# Cryptomatte images store the hash as a float so this converts a float pixel id to a manifest key
	return str( struct.Struct("=I").unpack( struct.Struct("=f").pack( value ) )[0] )

def _findCryptomatteNode( sourcePlug ) :

	def walk( plug ) :

		if isinstance( plug.parent(), GafferScene.Cryptomatte ) :
			return plug.parent()

		for output in plug.outputs() :
			r = walk( output )
			if r is not None :
				return r

		return None

	return walk( sourcePlug )

class _CryptomatteNamesPlugValueWidget( GafferUI.VectorDataPlugValueWidget ) :

	def __init__( self, plug, **kw ) :
		GafferUI.VectorDataPlugValueWidget.__init__( self, plug, **kw )

		addButton = self.vectorDataWidget().addButton()
		removeButton = self.vectorDataWidget().removeButton()

		# Connect at front so we get called before the default handlers
		addButton.dragEnterSignal().connectFront( Gaffer.WeakMethod( self.__convertEvent ), scoped = False )
		removeButton.dragEnterSignal().connectFront( Gaffer.WeakMethod( self.__convertEvent ), scoped = False )
		self.vectorDataWidget().dragEnterSignal().connectFront( Gaffer.WeakMethod( self.__convertEvent ), scoped = False )

	def __getManifest( self ) :

		cryptomatteNode = _findCryptomatteNode( self.getPlug() )
		if cryptomatteNode :
			with self.getContext() :
				with IECore.IgnoredExceptions( Exception ) :
					return cryptomatteNode["__manifest"].getValue()

		return None

	def __dataToManifestValue( self, data ) :

		if isinstance( data, IECore.Color4fData ) :
			manifest = self.__getManifest()
			# we expect the first channel of the event data to contain the value to convert to a manifest key
			manifestValueData = manifest.get( _idToManifestKey( data.value[0] ) )
			if manifestValueData :
				value = [ manifestValueData.value ]
			else :
				value = [ "<{}>".format( data.value[0] ) ]

			return value

		return None

	def __convertEvent( self, widget, event ) :

		# Convert data to a string that will be recognised by VectorDataWidget's native drag handling.
		## \todo This is questionable as `event` is `const` in C++, and the drag may just be transitioning across this
		# widget en-route to another where the conversion is not warranted. Consider VectorDataPlugValueWidget extensions
		# to provide a more legitimate point of conversion, perhaps along the lines of `PlugValueWidget._convertValue()`.

		if isinstance( event.data, IECore.Color4fData ) :
			event.data = IECore.StringVectorData( self.__dataToManifestValue( event.data ) )

		return False

	def _convertValue( self, value ) :

		plugValueType = type( self.getPlug().defaultValue() )
		if isinstance( value, IECore.Color4fData ) and hasattr( value, "value" ) :
			return plugValueType( self.__dataToManifestValue( value ) )
		else :
			return GafferUI.PlugValueWidget._convertValue( self, value )

def __cryptomatteLayerNames( plug ) :

	node = _findCryptomatteNode( plug )
	imagePlug = node["in"]

	imageMetadata = imagePlug["metadata"].getValue()
	cryptomatteNameRegex = re.compile( "^cryptomatte/[0-9a-f]{7}/name$" )
	availableLayers = [ imageMetadata[k].value for k in imageMetadata.keys() if cryptomatteNameRegex.match( k ) ]

	return availableLayers

def __layerPresetNames( plug ) :

	return IECore.StringVectorData( [ "None" ] + __cryptomatteLayerNames( plug ) )

def __layerPresetValues( plug ) :

	return IECore.StringVectorData( [ "" ] + __cryptomatteLayerNames( plug ) )

Gaffer.Metadata.registerNode(

	GafferScene.Cryptomatte,

	"description",
	"""
	Outputs a matte channel generated from IDs selected from Cryptomatte AOVs.
	""",

	"layout:activator:metadataManifest", lambda node : node["manifestSource"].getValue() == GafferScene.Cryptomatte.ManifestSource.Metadata,
	"layout:activator:sidecarManifest", lambda node : node["manifestSource"].getValue() == GafferScene.Cryptomatte.ManifestSource.Sidecar,

	plugs = {

		"in" : [

			"description",
			"""
			The input image containing Cryptomatte image layers and optional metadata.
			""",

		],

		"out" : [

			"description",
			"""
			The resulting image.
			""",

		],

		"layer" : [

			"description",
			"""
			The name of the Cryptomatte layer to use.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"presetNames", __layerPresetNames,
			"presetValues", __layerPresetValues,
			"presetsPlugValueWidget:allowCustom", True,
		],

		"manifestSource" : [

			"description",
			"""
			The source of the Cryptomatte manifest.

			 - None: No manifest will be loaded.
			 - Metadata: From the first of the following image metadata entries that
			 exist for the selected Cryptomatte layer :
			   - `manifest` : The manifest data.
			   - `manif_file` : The name of a JSON manifest file stored in a
			   directory specified on the `manifestDirectory` plug.
			 - Sidecar File: From a JSON file specified on the `sidecarFile` plug.
			""",

			"preset:None", GafferScene.Cryptomatte.ManifestSource.None_,
			"preset:Metadata", GafferScene.Cryptomatte.ManifestSource.Metadata,
			"preset:Sidecar File", GafferScene.Cryptomatte.ManifestSource.Sidecar,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		],

		"manifestDirectory" : [

			"description",
			"""
			A directory of JSON files containing Cryptomatte manifests.

			If a `manif_file` metadata entry exists for the selected Cryptomatte
			layer, it will be appended to this directory. The manifest is read from
			the file at the resulting path.
			""",

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"path:leaf", False,
			"layout:visibilityActivator", "metadataManifest",
		],

		"sidecarFile" : [

			"description",
			"""
			A JSON file containing a Cryptomatte manifest.

			File sequences with arbitrary padding may be specified using the '#' character
			as a placeholder for the frame numbers.
			""",

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"path:leaf", True,
			"fileSystemPath:extensions", "json",
			"fileSystemPath:extensionsLabel", "Show only JSON files",
			"fileSystemPath:includeSequences", True,
			"layout:visibilityActivator", "sidecarManifest",
		],

		"matteNames" : [

			"description",
			"""
			The list of names to be extracted as a matte.

			Names are matched against entries in the Cryptomatte manifest and
			Gaffer's standard wildcard characters can be used to match multiple
			names.

 			 - /robot/*Arm matches /robot/leftArm, /robot/rightArm and
			   /robot/Arm. But does not match /robot/limbs/leftArm or
			   /robot/arm.

			 - /.../house matches /house, /street/house and /city/street/house.

			 - /robot[ABC] matches /robotA, /robotB and /robotC. But does not
			   match /robotD or /robota.

			Cryptomatte manifest entries containing '/' characters will be
			treated as hierarchical paths and a matte will be extracted for any
			entry that is matched or has an ancestor that is matched.

			 - /robot extracts mattes for /robot, /robot/leftArm and
			   /robot/rightArm. But does not extract /robotA or /robotLeftArm.

			ID values can be specified directly by wrapping a float ID value in
			angle brackets.

			 - `<value>`.
			""",

			"plugValueWidget:type", "GafferSceneUI.CryptomatteUI._CryptomatteNamesPlugValueWidget",
		],

		"outputChannel" : [

			"description",
			"""
			The name of the output channel containing the extracted matte.
			""",

		],

	}

)

##########################################################################
# NodeGadget drop handler
##########################################################################

GafferUI.Pointer.registerPointer( "addNames", GafferUI.Pointer( "addObjects.png", imath.V2i( 36, 18 ) ) )
GafferUI.Pointer.registerPointer( "removeNames", GafferUI.Pointer( "removeObjects.png", imath.V2i( 36, 18 ) ) )
GafferUI.Pointer.registerPointer( "replaceNames", GafferUI.Pointer( "replaceObjects.png", imath.V2i( 36, 18 ) ) )

__DropMode = IECore.Enum.create( "None_", "Add", "Remove", "Replace" )

__originalDragPointer = None

def __namesPlug( node ) :
	## \todo Handle matteNames plug with input connection
	return node["matteNames"]

def __dropMode( nodeGadget, event ) :

	if __namesPlug( nodeGadget.node() ) is None :
		return __DropMode.Replace

	if event.modifiers & event.Modifiers.Shift :
		return __DropMode.Add
	elif event.modifiers & event.Modifiers.Control :
		return __DropMode.Remove
	else :
		return __DropMode.Replace

def __dragEnter( nodeGadget, event ) :

	if not (isinstance( event.data, IECore.Color4fData ) or isinstance( event.data, IECore.StringVectorData )):
		return False

	if __dropMode( nodeGadget, event ) == __DropMode.None_ :
		return False

	global __originalDragPointer
	__originalDragPointer = GafferUI.Pointer.getCurrent()

	return True

def __dragLeave( nodeGadget, event ) :

	global __originalDragPointer

	GafferUI.Pointer.setCurrent( __originalDragPointer )
	__originalDragPointer = None

	return True

def __dragMove( nodeGadget, event ) :

	global __originalDragPointer
	if __originalDragPointer is None :
		return False

	GafferUI.Pointer.setCurrent( str( __dropMode( nodeGadget, event ) ).lower() + "Names" )

	return True

def __drop( nodeGadget, event ) :

	global __originalDragPointer
	if __originalDragPointer is None :
		return False

	namesPlug = __namesPlug( nodeGadget.node() )

	dropMode = __dropMode( nodeGadget, event )

	if isinstance( event.data, IECore.Color4fData ) :
		with nodeGadget.node().ancestor( Gaffer.ScriptNode ).context() :
			manifest = nodeGadget.node()["__manifest"].getValue()

		manifestValueData = manifest.get( _idToManifestKey( event.data.value[0] ) )
		if manifestValueData :
			dropValues = [ manifestValueData.value ]
		else :
			dropValues = [ "<{}>".format( event.data.value[0] ) ]

		event.data = IECore.StringVectorData( dropValues )

	if dropMode == __DropMode.Replace :
		names = sorted( event.data )
	elif dropMode == __DropMode.Add :
		names = namesPlug.getValue()
		names.extend( [ x for x in event.data if x not in names ] )
	else :
		names = namesPlug.getValue()
		names = [ x for x in names if x not in event.data ]

	with Gaffer.UndoScope( nodeGadget.node().ancestor( Gaffer.ScriptNode ) ) :
		namesPlug.setValue( IECore.StringVectorData( names ) )

	GafferUI.Pointer.setCurrent( __originalDragPointer )
	__originalDragPointer = None

	return True

def __addNamesDropTarget( nodeGadget ) :

	nodeGadget.dragEnterSignal().connect( __dragEnter, scoped = False )
	nodeGadget.dragLeaveSignal().connect( __dragLeave, scoped = False )
	nodeGadget.dragMoveSignal().connect( __dragMove, scoped = False )
	nodeGadget.dropSignal().connect( __drop, scoped = False )

def __nodeGadget( pathFilter ) :

	nodeGadget = GafferUI.StandardNodeGadget( pathFilter )
	__addNamesDropTarget( nodeGadget )

	return nodeGadget

GafferUI.NodeGadget.registerNodeGadget( GafferScene.Cryptomatte, __nodeGadget )

##########################################################################
# GraphEditor context menu
##########################################################################

def __selectAffected( node, context ) :

	if not isinstance( node, GafferScene.Cryptomatte ) :
		return

	scene = node["__manifestScene"]

	with context :
		pathMatcher = IECore.PathMatcher()
		for path in node["matteNames"].getValue() :
			if path[0] != '<' and path[-1] != '>' :
				pathMatcher.addPath( path )

		pathMatcherResult = IECore.PathMatcher()
		GafferScene.SceneAlgo.matchingPaths( pathMatcher, scene, pathMatcherResult )

	GafferSceneUI.ContextAlgo.setSelectedPaths( context, pathMatcherResult )

def appendNodeContextMenuDefinitions( graphEditor, node, menuDefinition ) :

	if not isinstance( node, GafferScene.Cryptomatte ) :
		return

	menuDefinition.append( "/CryptomatteDivider", { "divider" : True } )
	menuDefinition.append( "/Select Affected Objects", { "command" : functools.partial( __selectAffected, node, graphEditor.getContext() ) } )

##########################################################################
# NodeEditor tool menu
##########################################################################

def appendNodeEditorToolMenuDefinitions( nodeEditor, node, menuDefinition ) :

	if not isinstance( node, GafferScene.Cryptomatte ) :
		return

	menuDefinition.append( "/CryptomatteDivider", { "divider" : True } )
	menuDefinition.append( "/Select Affected Objects", { "command" : functools.partial( __selectAffected, node, nodeEditor.getContext() ) } )
