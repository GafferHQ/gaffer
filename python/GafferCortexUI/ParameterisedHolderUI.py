##########################################################################
#
#  Copyright (c) 2011-2015, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import re
import pipes
import fnmatch
import imath

import IECore

import Gaffer
import GafferUI
import GafferCortex
import GafferCortexUI

__nodeTypes = (
	GafferCortex.ParameterisedHolderNode,
	GafferCortex.ParameterisedHolderComputeNode,
	GafferCortex.ParameterisedHolderDependencyNode,
	GafferCortex.ParameterisedHolderTaskNode,
)

##########################################################################
# NodeUI
##########################################################################

# Supported userData entries :
#
# ["UI"]["headerVisible"]

class _ParameterisedHolderNodeUI( GafferUI.NodeUI ) :

	def __init__( self, node, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 )

		GafferUI.NodeUI.__init__( self, node, column, **kw )

		headerVisible = True
		parameterised = self.node().getParameterised()[0]
		with IECore.IgnoredExceptions( KeyError ) :
			headerVisible = parameterised.userData()["UI"]["headerVisible"].value

		with column :

			if headerVisible :
				with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal ) :
					GafferUI.Spacer( imath.V2i( 10 ), parenting = { "expand"  : True } )
					toolButton = GafferCortexUI.ToolParameterValueWidget( self.node().parameterHandler() )
					_InfoButton( node )

			with GafferUI.ScrolledContainer( horizontalMode=GafferUI.ScrollMode.Never, borderWidth=4 ) :
				self.__parameterValueWidget = GafferCortexUI.CompoundParameterValueWidget( self.node().parameterHandler(), collapsible = False )

for nodeType in __nodeTypes :
	GafferUI.NodeUI.registerNodeUI( nodeType, _ParameterisedHolderNodeUI )

##########################################################################
# Info button
##########################################################################

## \todo We might want to think about using this for all NodeUIs, since it
# relies only on Metadata which should be available for all node types.
class _InfoButton( GafferUI.Button ) :

	def __init__( self, node ) :

		GafferUI.Button.__init__( self, image="info.png", hasFrame=False )

		self.__node = node
		self.__window = None
		self.clickedSignal().connect( Gaffer.WeakMethod( self.__clicked ), scoped = False )

	def getToolTip( self ) :

		result = GafferUI.Button.getToolTip( self )
		if result :
			return result

		result = IECore.StringUtil.wrap( self.__infoText(), 75 )
		return result

	def __infoText( self ) :

		## \todo: NodeUI should provide setContext()/getContext() methods
		## and we should use those to get the proper context here.
		context = self.__node.scriptNode().context() if self.__node.scriptNode() else Gaffer.Context.current()
		with context :
			result = Gaffer.Metadata.value( self.__node, "description" ) or ""
			summary = Gaffer.Metadata.value( self.__node, "summary" )

		if summary :
			if result :
				result += "\n\n"
			result += summary

		return result

	def __clicked( self, button ) :

		if self.__window is None :
			with GafferUI.Window( "Info", borderWidth=8 ) as self.__window :
				GafferUI.MultiLineTextWidget( editable = False )
			self.ancestor( GafferUI.Window ).addChildWindow( self.__window )

		self.__window.getChild().setText( self.__infoText() )
		self.__window.reveal()

##########################################################################
# Metadata
##########################################################################

def __nodeDescription( node ) :

	parameterised = node.getParameterised()[0]
	if parameterised is None :
		return "Hosts Cortex Parameterised classes"

	return parameterised.description

def __nodeSummary( node ) :

	parameterised = node.getParameterised()[0]
	if not isinstance( parameterised, IECore.Op ) :
		return ""

	node.parameterHandler().setParameterValue()
	parameterValues = IECore.ParameterParser().serialise( parameterised.parameters() )
	# pipes.quote() has a bug in some python versions where it doesn't quote empty strings.
	parameterValues = " ".join( [ pipes.quote( x ) if x else "''" for x in parameterValues ] )

	return "Command line equivalent : \n\ngaffer op %s -version %d -arguments %s" % (
		parameterised.path,
		parameterised.version,
		parameterValues,
	)

## \todo There should really be a method to map from plug to parameter.
# The logic exists in ParameterisedHolder.plugSet() but isn't public.
def __parameter( plug ) :

	parameter = plug.node().parameterHandler().parameter()
	for name in plug.relativeName( plug.node() ).split( "." )[1:] :
		if not isinstance( parameter, IECore.CompoundParameter ) :
			return None
		else :
			parameter = parameter[name]

	return parameter

def __plugDescription( plug ) :

	parameter = __parameter( plug )
	return parameter.description if parameter else None

def __plugPresetNames( plug ) :

	parameter = __parameter( plug )
	if not parameter :
		return None

	presetNames = parameter.presetNames()
	if presetNames and isinstance( plug, (
		Gaffer.StringPlug,
		Gaffer.BoolPlug,
		Gaffer.IntPlug,
		Gaffer.FloatPlug,
		Gaffer.Color3fPlug,
		Gaffer.V3fPlug,
	) ) :
		return IECore.StringVectorData( presetNames )

	return None

def __plugPresetValues( plug ) :

	parameter = __parameter( plug )
	if not parameter :
		return None

	# make sure to get the values in the same
	# order that the names were given.
	values = [ parameter.getPresets()[x] for x in parameter.presetNames() ]
	if isinstance( plug, Gaffer.StringPlug ) :
		return IECore.StringVectorData( [ v.value for v in values ] )
	elif isinstance( plug, Gaffer.BoolPlug ) :
		return IECore.BoolVectorData( [ v.value for v in values ] )
	elif isinstance( plug, Gaffer.IntPlug ) :
		return IECore.IntVectorData( [ v.value for v in values ] )
	elif isinstance( plug, Gaffer.FloatPlug ) :
		return IECore.FloatVectorData( [ v.value for v in values ] )
	elif isinstance( plug, Gaffer.Color3fPlug ) :
		return IECore.Color3fVectorData( [ v.value for v in values ] )
	elif isinstance( plug, Gaffer.V3fPlug ) :
		return IECore.V3fVectorData( [ v.value for v in values ] )

	return None

def __plugWidgetType( plug ) :

	parameter = __parameter( plug )

	if parameter and parameter.presetsOnly and __plugPresetNames( plug ) :
		return "GafferUI.PresetsPlugValueWidget"

	return None

def __plugNoduleType( plug ) :

	return "GafferUI::StandardNodule" if isinstance( plug, Gaffer.ObjectPlug ) else ""

for nodeType in __nodeTypes :

	Gaffer.Metadata.registerNode(

		nodeType,

		"description", __nodeDescription,
		"summary", __nodeSummary,

		plugs = {

			"parameters" : [

				"nodule:type", "GafferUI::CompoundNodule",

			],

			"parameters.*..." : [

				"description", __plugDescription,
				"presetNames", __plugPresetNames,
				"presetValues", __plugPresetValues,
				"plugValueWidget:type", __plugWidgetType,
				"nodule:type", __plugNoduleType,

			],

		},

	)

##########################################################################
# Node menu
##########################################################################

## Appends menu items for the creation of all Parameterised classes found on some searchpaths.
def appendParameterisedHolders( menuDefinition, prefix, searchPathEnvVar, nodeCreator, matchExpression = re.compile( ".*" ) ) :

	if isinstance( matchExpression, str ) :
		matchExpression = re.compile( fnmatch.translate( matchExpression ) )

	menuDefinition.append( prefix, { "subMenu" : IECore.curry( __parameterisedHolderMenu, nodeCreator, searchPathEnvVar, matchExpression ) } )

def __parameterisedHolderCreator( nodeCreator, className, classVersion, searchPathEnvVar ) :

	nodeName = className.rpartition( "/" )[-1]
	node = nodeCreator( nodeName )
	node.setParameterised( className, classVersion, searchPathEnvVar )

	return node

def __parameterisedHolderMenu( nodeCreator, searchPathEnvVar, matchExpression ) :

	c = IECore.ClassLoader.defaultLoader( searchPathEnvVar )
	d = IECore.MenuDefinition()
	for n in c.classNames() :
		if matchExpression.match( n ) :
			nc = "/".join( [ IECore.CamelCase.toSpaced( x ) for x in n.split( "/" ) ] )
			v = c.getDefaultVersion( n )
			d.append( "/" + nc, { "command" : GafferUI.NodeMenu.nodeCreatorWrapper( IECore.curry( __parameterisedHolderCreator, nodeCreator, n, v, searchPathEnvVar ) ) } )

	return d
