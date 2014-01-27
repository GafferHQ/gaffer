##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import fnmatch

import IECore
import Gaffer
import GafferUI

# NodeUI registration
##########################################################################
				
GafferUI.NodeUI.registerNodeUI( Gaffer.Expression.staticTypeId(), lambda node : GafferUI.StandardNodeUI( node, displayMode = GafferUI.StandardNodeUI.DisplayMode.Simplified ) )

# PlugValueWidget popup menu for creating expressions
##########################################################################

def __createExpression( plug ) :

	node = plug.node()
	parentNode = node.ancestor( Gaffer.Node.staticTypeId() )

	with Gaffer.UndoContext( node.scriptNode() ) :
	
		expressionNode = Gaffer.Expression()
		parentNode.addChild( expressionNode )
		
		expression = "parent['"
		expression += plug.relativeName( parentNode ).replace( ".", "']['" )
		expression += "'] = "
		
		if isinstance( plug, Gaffer.StringPlug ) :
			expression += "''"
		elif isinstance( plug, Gaffer.IntPlug ) :
			expression += "1"
		elif isinstance( plug, Gaffer.FloatPlug ) :
			expression += "1.0"
		
		expressionNode["expression"].setValue( expression )
		
	__editExpression( plug )

def __editExpression( plug ) :

	expressionNode = plug.getInput().node()	

	GafferUI.NodeEditor.acquire( expressionNode )

def __popupMenu( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	if not isinstance( plug, ( Gaffer.FloatPlug, Gaffer.IntPlug, Gaffer.StringPlug, Gaffer.BoolPlug ) ) :
		return
		
	node = plug.node()
	if node is None or node.parent() is None :
		return

	input = plug.getInput()
	if input is None and plugValueWidget._editable() :		
		menuDefinition.prepend( "/ExpressionDivider", { "divider" : True } )
		menuDefinition.prepend( "/Create Expression...", { "command" : IECore.curry( __createExpression, plug ) } )
		
__popupMenuConnection = GafferUI.PlugValueWidget.popupMenuSignal().connect( __popupMenu )

# _ExpressionPlugValueWidget
##########################################################################

class _ExpressionPlugValueWidget( GafferUI.MultiLineStringPlugValueWidget ) :

	def __init__( self, plug, **kw ) :
	
		GafferUI.MultiLineStringPlugValueWidget.__init__( self, plug, **kw )
	
		self.__dropTextConnection = self.textWidget().dropTextSignal().connect( Gaffer.WeakMethod( self.__dropText ) )

	def hasLabel( self ) :
	
		# strictly speaking we don't have a label, but i think it's pretty obvious
		# what we are - what else is a giant text input box in an expression ui
		# going to be?
		return True

	def __dropText( self, widget, dragData ) :
	
		if isinstance( dragData, IECore.StringVectorData ) :
			return repr( list( dragData ) )
		elif isinstance( dragData, Gaffer.GraphComponent ) :
			name = dragData.relativeName( self.getPlug().node().parent() )	
			if not name :
				return None
			return "parent" + "".join( [ "['" + n + "']" for n in name.split( "." ) ] )
		elif isinstance( dragData, Gaffer.Set ) :
			if len( dragData ) == 1 :
				return self.__dropText( widget, dragData[0] )
			else :
				return None
		
		return None
		
# PlugValueWidget registrations
##########################################################################

GafferUI.PlugValueWidget.registerCreator(
	Gaffer.Expression.staticTypeId(),
	"engine",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = [
		( IECore.CamelCase.toSpaced( e ), e ) for e in Gaffer.Expression.Engine.registeredEngines() 
	]
)

GafferUI.PlugValueWidget.registerCreator(
	Gaffer.Expression.staticTypeId(),
	"expression",
	_ExpressionPlugValueWidget,
)

GafferUI.PlugValueWidget.registerCreator(
	Gaffer.Expression.staticTypeId(),
	"in",
	None
)

GafferUI.PlugValueWidget.registerCreator(
	Gaffer.Expression.staticTypeId(),
	"out",
	None
)

# Nodule deregistrations
##########################################################################

GafferUI.Nodule.registerNodule( Gaffer.Expression.staticTypeId(), fnmatch.translate( "*" ), lambda plug : None )
