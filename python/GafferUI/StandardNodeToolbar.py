##########################################################################
#  
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI

class StandardNodeToolbar( GafferUI.NodeToolbar ) :

	def __init__( self, node, **kw ) :
	
		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		
		GafferUI.NodeToolbar.__init__( self, node, self.__row, **kw )
		
		self.__childPlugUIs = {}

		self.__childAddedConnection = node.childAddedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ) )
		self.__childRemovedConnection = node.childRemovedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ) )
		self.__childrenChangedPending = False

		self.__updateChildPlugUIs()

	## \todo This is very similar to code in CompoundPlugValueWidget and
	# StandardNodeUI, and all are vulnerable to plug name changes because of the
	# mapping from plugName->widget. Ideally we'd map from plug->widget directly,
	# but that's problematic because of the Cortex RefCounted object identity problem -
	# two python objects may refer to the same RefCounted object. When this occurs,
	# they're unsuitable for use as dictionary keys because each object will have
	# its own hash (based on the python object id) and therefore appear to be a different
	# key to the other. Perhaps we should look into fixing the underlying object identity
	# problem in Cortex (it's fixed for wrapped classes already), or at the very least
	# see if we can reimplement __hash__ and __eq__ based on the identity of the C++
	# rather than Python object.
	def __updateChildPlugUIs( self ) :
	
		# ditch child uis we don't need any more
		childPlugs = self.node().children( Gaffer.Plug.staticTypeId() )
		childNames = set( self.node().keys() )
		for childName in self.__childPlugUIs.keys() :
			if childName not in childNames :
				del self.__childPlugUIs[childName]

		# make (or reuse existing) uis for each child plug
		orderedChildUIs = []
		for plug in childPlugs :
			
			if plug.getName().startswith( "__" ) :
				continue
			
			if plug.getName() not in self.__childPlugUIs :
				
				widget = GafferUI.PlugValueWidget.create( plug )
				if widget is not None :
							
					if ( isinstance( widget, GafferUI.PlugValueWidget )
						 and not widget.hasLabel()
						 and Gaffer.Metadata.plugValue( plug, "label" ) != ""
					) :
						widget = GafferUI.PlugWidget( widget )
						# undo the annoying fixed size the PlugWidget has applied
						# to the label.
						## \todo Shift all the label size fixing out of PlugWidget and
						# into CompoundPlugValueWidget so we don't have to do this at all.
						QWIDGETSIZE_MAX = 16777215 # qt #define not exposed by PyQt or PySide
						widget.labelPlugValueWidget().label()._qtWidget().setFixedWidth( QWIDGETSIZE_MAX )
				
				self.__childPlugUIs[plug.getName()] = widget
				
			else :
			
				widget = self.__childPlugUIs[plug.getName()]
				
			if widget is not None :
				orderedChildUIs.append( widget )
				if Gaffer.Metadata.plugValue( plug, "divider" ) :
					orderedChildUIs.append( GafferUI.Divider( GafferUI.Divider.Orientation.Vertical ) )
		
		del self.__row[:] # must clear first, to bypass ListContainer's "helpful" remembering of expand statuses
		self.__row[:] = orderedChildUIs
		self.__row.insert( 0, GafferUI.Spacer( IECore.V2i( 1, 1 ) ), expand = True )

	def __childAddedOrRemoved( self, parent, child ) :
	
		assert( parent.isSame( self.node() ) )
	
		if isinstance( child, Gaffer.Plug ) :
			# typically many plugs are added and removed at once. we don't
			# want to be rebuilding the ui for each individual event, so we
			# add an idle callback to do the rebuild once the
			# upheaval is over.
			if not self.__childrenChangedPending :
				GafferUI.EventLoop.addIdleCallback( self.__childrenChanged )
				self.__childrenChangedPending = True

	def __childrenChanged( self ) :
	
		self.__updateChildPlugUIs()
		self.__childrenChangedPending = False
		
		return False # removes the callback
