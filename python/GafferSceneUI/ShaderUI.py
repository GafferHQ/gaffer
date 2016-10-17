##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import os
import re
import string
import fnmatch

import IECore

import Gaffer
import GafferUI
import GafferScene

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.Shader,

	"description",
	"""
	The base type for all nodes which create shaders. Use the
	ShaderAssignment node to assign them to objects in the scene.
	""",

	"nodeGadget:minWidth", 0.0,

	plugs = {

		"name" : [

			"description",
			"""
			The name of the shader being represented. This should
			be considered read-only. Use the Shader.loadShader()
			method to load a shader.
			""",

			"layout:section", "",
			"nodule:type", "",
			"plugValueWidget:type", "GafferSceneUI.ShaderUI._ShaderNamePlugValueWidget",

		],

		"type" : [

			"description",
			"""
			The type of the shader being represented. This should
			be considered read-only. Use the Shader.loadShader()
			method to load a shader.
			""",

			"layout:section", "",
			"nodule:type", "",
			"plugValueWidget:type", "",

		],

		"parameters" : [

			"description",
			"""
			Where the parameters for the shader are represented.
			""",

			"nodeGadget:nodulePosition", "left",
			"nodule:type", "GafferUI::CompoundNodule",
			"compoundNodule:orientation", "y",
			"compoundNodule:spacing", 0.2,
			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",

		],

		"parameters.*" : [

			# Although the parameters plug is positioned
			# as we want above, we must also register
			# appropriate values for each individual parameter,
			# for the case where they get promoted to a box
			# individually.
			"nodeGadget:nodulePosition", "left",

		],

		"out" : [

			"description",
			"""
			The output from the shader.
			""",

			"nodeGadget:nodulePosition", "right",
			"plugValueWidget:type", "",

		],

	}

)

##########################################################################
# PlugValueWidgets
##########################################################################

class _ShaderNamePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, row, plug, **kw )

		with row :

			self.__label = GafferUI.Label( "" )

			GafferUI.Spacer( IECore.V2i( 1 ), parenting = { "expand" : True } )

			self.__button = GafferUI.Button( "Reload" )
			self.__buttonClickedConnection = self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )

		self._updateFromPlug()

	def hasLabel( self ) :

		return True

	def _updateFromPlug( self ) :

		with self.getContext() :
			shaderName = self.getPlug().getValue()
			self.__label.setText( "<h3>Shader : " + shaderName + "</h3>" )
			## \todo Disable the type check once we've got OpenGLShader implementing reloading properly.
			self.__button.setEnabled( not Gaffer.readOnly( self.getPlug() ) and not isinstance( self.getPlug().node(), GafferScene.OpenGLShader ) )

	def __buttonClicked( self, button ) :

		node = self.getPlug().node()
		if hasattr( node, "shaderLoader" ) :
			node.shaderLoader().clear()

		with Gaffer.UndoContext( node.ancestor( Gaffer.ScriptNode ) ) :
			node.loadShader( node["name"].getValue(), keepExistingValues = True )

##########################################################################
# NodeFinderDialogue mode
##########################################################################

def __shaderNameExtractor( node ) :

	if isinstance( node, GafferScene.Shader ) :
		return node["name"].getValue()
	else :
		return ""

GafferUI.NodeFinderDialogue.registerMode( "Shader Names", __shaderNameExtractor )

##########################################################################
# Shader menu
##########################################################################

## Appends menu items for the creation of all shaders found on some searchpaths.
def appendShaders( menuDefinition, prefix, searchPaths, extensions, nodeCreator, matchExpression = "*", searchTextPrefix = "" ) :

	menuDefinition.append( prefix, { "subMenu" : IECore.curry( __shaderSubMenu, searchPaths, extensions, nodeCreator, matchExpression, searchTextPrefix ) } )

def __nodeName( shaderName ) :

	nodeName = os.path.split( shaderName )[-1]
	nodeName = nodeName.translate( string.maketrans( ".-", "__" ) )
	return nodeName

def __loadFromFile( menu, extensions, nodeCreator ) :

	bookmarks = GafferUI.Bookmarks.acquire( menu, category = "shader" )
	path = Gaffer.FileSystemPath( bookmarks.getDefault( menu ) )
	path.setFilter( Gaffer.FileSystemPath.createStandardFilter( extensions ) )

	dialogue = GafferUI.PathChooserDialogue( path, title="Load Shader", confirmLabel = "Load", valid=True, leaf=True, bookmarks = bookmarks )
	path = dialogue.waitForPath( parentWindow = menu.ancestor( GafferUI.ScriptWindow ) )

	if not path :
		return None

	shaderName = os.path.splitext( str( path ) )[0]

	return nodeCreator( __nodeName( shaderName ), shaderName )

def __shaderSubMenu( searchPaths, extensions, nodeCreator, matchExpression, searchTextPrefix ) :

	if isinstance( matchExpression, str ) :
		matchExpression = re.compile( fnmatch.translate( matchExpression ) )

	shaders = set()
	pathsVisited = set()
	for path in searchPaths :

		if path in pathsVisited :
			continue

		for root, dirs, files in os.walk( path ) :
			for file in files :
				if os.path.splitext( file )[1][1:] in extensions :
					shaderPath = os.path.join( root, file ).partition( path )[-1].lstrip( "/" )
					if shaderPath not in shaders and matchExpression.match( shaderPath ) :
						shaders.add( os.path.splitext( shaderPath )[0] )

		pathsVisited.add( path )

	shaders = sorted( list( shaders ) )
	categorisedShaders = [ x for x in shaders if "/" in x ]
	uncategorisedShaders = [ x for x in shaders if "/" not in x ]

	shadersAndMenuPaths = []
	for shader in categorisedShaders :
		shadersAndMenuPaths.append( ( shader, "/" + shader ) )

	for shader in uncategorisedShaders :
		if not categorisedShaders :
			shadersAndMenuPaths.append( ( shader, "/" + shader ) )
		else :
			shadersAndMenuPaths.append( ( shader, "/Other/" + shader ) )

	result = IECore.MenuDefinition()
	for shader, menuPath in shadersAndMenuPaths :
		menuPath = "/".join( [ IECore.CamelCase.toSpaced( x ) for x in menuPath.split( "/" ) ] )
		result.append(
			menuPath,
			{
				"command" : GafferUI.NodeMenu.nodeCreatorWrapper( IECore.curry( nodeCreator, __nodeName( shader ), shader ) ),
				"searchText" : searchTextPrefix + menuPath.rpartition( "/" )[-1].replace( " ", "" ),
			},
		)

	result.append( "/LoadDivider", { "divider" : True } )
	result.append( "/Load...", { "command" : GafferUI.NodeMenu.nodeCreatorWrapper( lambda menu : __loadFromFile( menu, extensions, nodeCreator ) ) } )

	return result
