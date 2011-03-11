##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

from PySide import QtGui

import IECore

import Gaffer
import GafferUI

## This class forms a useful base for creating node uis for use in the NodeEditor
# and elsewhere. It provides simple methods for building a ui structured using tabs
# and collapsible elements, and allows customisation of the widget types used for
# each Plug.
class NodeUI( GafferUI.Widget ) :

	def __init__( self, node ) :
	
		GafferUI.Widget.__init__( self, QtGui.QWidget() )
	
		self._qtWidget().setLayout( QtGui.QGridLayout() )
		self.__currentColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=2 )
		self._qtWidget().layout().addWidget( self.__currentColumn._qtWidget(), 0, 0 )
		
		self.__node = node
		
		self._build()

		# to fill any additional space
		self.__currentColumn.append( GafferUI.Spacer( IECore.V2i( 0 ) ), expand=True )
		
	## Returns the node the ui is being created for.
	def _node( self ) :
	
		return self.__node

	def _tab( self, label ) :
	
		raise NotImplementedError
		
	def _collapsible( self, label ) :
	
		class CollapsibleContext() :
		
			def __init__( self, nodeUI ) :
			
				self.__nodeUI = nodeUI
				self.__label = label
		
			def __enter__( self ) :
			
				cl = GafferUI.Collapsible( self.__label, collapsed=True )
				co = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=2 )
				cl.setChild( co )
				
				self.__prevColumn = self.__nodeUI._NodeUI__currentColumn
				
				self.__nodeUI._NodeUI__currentColumn.append( cl )
				self.__nodeUI._NodeUI__currentColumn = co
				
			def __exit__( self, type, value, traceBack ) :
			
				self.__nodeUI._NodeUI__currentColumn.append( GafferUI.Spacer( IECore.V2i( 0 ) ), expand=True )
				self.__nodeUI._NodeUI__currentColumn = self.__prevColumn
				
		return CollapsibleContext( self )
		
	def _addWidget( self, widget ) :
		
		self.__currentColumn.append( widget )
		
	def _addPlugWidget( self, plugOrPlugPath ) :
	
		if isinstance( plugOrPlugPath, basestring ) :
			plug = self._node().getChild( plugOrPlugPath )
		else :
			plug = plugOrPlugPath
		
		vw = GafferUI.PlugValueWidget.create( plug )
		if vw :	
			w = GafferUI.PlugWidget( vw )
			self._addWidget( w )

	## This method is called from the constructor to build the ui. It is
	# intended to be overriden in derived classes.
	def _build( self ) :
		
		self.__buildWalk( self._node() )

	def __buildWalk( self, parent ) :
	
		plugs = [ x for x in parent.children() if x.isInstanceOf( Gaffer.Plug.staticTypeId() ) ]
		plugs = [ x for x in plugs if x.direction()==Gaffer.Plug.Direction.In and not x.getName().startswith( "__" ) ]
		for plug in plugs :

			if plug.typeId()==Gaffer.CompoundPlug.staticTypeId() :
			
				with self._collapsible( IECore.CamelCase.toSpaced( plug.getName() ) ) :
					self.__buildWalk( plug )
				
			else :
			
				self._addPlugWidget( plug )

	@staticmethod
	def _registerPlugWidget( self, nodeTypeId, plugPath, widgetType, **kw ) :
	
		raise NotImplementedError
		
GafferUI.NodeEditor.registerNodeUI( Gaffer.Node.staticTypeId(), NodeUI )
