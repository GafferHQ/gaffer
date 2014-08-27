##########################################################################
#
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

from __future__ import with_statement

import pipes
import fnmatch

import IECore

import Gaffer
import GafferUI

class ParameterisedHolderNodeUI( GafferUI.NodeUI ) :

	def __init__( self, node, readOnly=False, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 )

		GafferUI.NodeUI.__init__( self, node, column, **kw )

		with column :

			with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal ) :
				GafferUI.Spacer( IECore.V2i( 10 ), parenting = { "expand"  : True } )
				toolButton = GafferUI.ToolParameterValueWidget( self.node().parameterHandler() )
				toolButton.plugValueWidget().setReadOnly( readOnly )
				_InfoButton( node )

			with GafferUI.ScrolledContainer( horizontalMode=GafferUI.ScrolledContainer.ScrollMode.Never, borderWidth=4 ) :
				self.__parameterValueWidget = GafferUI.CompoundParameterValueWidget( self.node().parameterHandler(), collapsible = False )

		self.setReadOnly( readOnly )

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.NodeUI.setReadOnly( self, readOnly )

		self.__parameterValueWidget.plugValueWidget().setReadOnly( readOnly )

GafferUI.NodeUI.registerNodeUI( Gaffer.ParameterisedHolderNode, ParameterisedHolderNodeUI )
GafferUI.NodeUI.registerNodeUI( Gaffer.ParameterisedHolderComputeNode, ParameterisedHolderNodeUI )
GafferUI.NodeUI.registerNodeUI( Gaffer.ParameterisedHolderDependencyNode, ParameterisedHolderNodeUI )

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
		self.__clickedConnection = self.clickedSignal().connect( Gaffer.WeakMethod( self.__clicked ) )

	def getToolTip( self ) :

		result = GafferUI.Button.getToolTip( self )
		if result :
			return result

		result = IECore.StringUtil.wrap( self.__infoText(), 75 )
		return result

	def __infoText( self ) :

		result = Gaffer.Metadata.nodeDescription( self.__node )
		summary = Gaffer.Metadata.nodeValue( self.__node, "summary" )
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
# Nodules
##########################################################################

def __parameterNoduleCreator( plug ) :

	if isinstance( plug, Gaffer.ObjectPlug ) :
		return GafferUI.StandardNodule( plug )
	else :
		return None

GafferUI.Nodule.registerNodule( Gaffer.ParameterisedHolderNode, "parameters", GafferUI.CompoundNodule )
GafferUI.Nodule.registerNodule( Gaffer.ParameterisedHolderComputeNode, "parameters", GafferUI.CompoundNodule )
GafferUI.Nodule.registerNodule( Gaffer.ParameterisedHolderDependencyNode, "parameters", GafferUI.CompoundNodule )

GafferUI.Nodule.registerNodule( Gaffer.ParameterisedHolderNode, fnmatch.translate( "parameters.*" ), __parameterNoduleCreator )
GafferUI.Nodule.registerNodule( Gaffer.ParameterisedHolderComputeNode, fnmatch.translate( "parameters.*" ), __parameterNoduleCreator )
GafferUI.Nodule.registerNodule( Gaffer.ParameterisedHolderDependencyNode, fnmatch.translate( "parameters.*" ), __parameterNoduleCreator )

##########################################################################
# Metadata
##########################################################################

def __nodeDescription( node ) :

	parameterised = node.getParameterised()[0]
	if parameterised is None :
		return ""

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

def __plugDescription( plug ) :

	## \todo There should really be a method to map from plug to parameter.
	# The logic exists in ParameterisedHolder.plugSet() but isn't public.
	parameter = plug.node().parameterHandler().parameter()
	for name in plug.relativeName( plug.node() ).split( "." )[1:] :
		if not isinstance( parameter, IECore.CompoundParameter ) :
			return None
		else :
			parameter = parameter[name]

	return parameter.description

for nodeType in (
	Gaffer.ParameterisedHolderNode,
	Gaffer.ParameterisedHolderComputeNode,
	Gaffer.ParameterisedHolderDependencyNode,
) :

	Gaffer.Metadata.registerNodeDescription( nodeType, __nodeDescription )
	Gaffer.Metadata.registerNodeValue( nodeType, "summary", __nodeSummary )
	Gaffer.Metadata.registerPlugDescription( nodeType, "parameters.*", __plugDescription )
