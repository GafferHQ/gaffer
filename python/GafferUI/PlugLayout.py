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

import Gaffer
import GafferUI

## A class for laying out widgets to represent all the plugs held on a particular parent.
class PlugLayout( GafferUI.Widget ) :

	def __init__( self, parent, orientation = GafferUI.ListContainer.Orientation.Vertical, **kw ) :

		assert( isinstance( parent, ( Gaffer.Node, Gaffer.CompoundPlug ) ) )

		self.__mainContainer = GafferUI.ListContainer( orientation, spacing = 4 )
		
		GafferUI.Widget.__init__( self, self.__mainContainer, **kw )
		
		self.__parent = parent
		
		# we need to connect to the childAdded/childRemoved signals on
		# the parent so we can update the ui when plugs are added and removed.
		self.__childAddedConnection = parent.childAddedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ) )
 		self.__childRemovedConnection = parent.childRemovedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ) )
 		self.__childrenChangedPending = False
		
		# building plug uis can be very expensive, and often we're initially hidden in a non-current tab
		# or a collapsed section. so we defer our building until we become visible to avoid unnecessary overhead.
		self.__visibilityChangedConnection = self.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__visibilityChanged ) )
				
		self.__plugsToWidgets = {} # mapping from child plug to widget

	## Returns a PlugValueWidget representing the specified child plug.
	# Because the layout is built lazily on demand, this might return None due
	# to the user not having opened up the ui - in this case lazy=False may
	# be passed to force the creation of the ui.
	def plugValueWidget( self, childPlug, lazy=True ) :

		if not lazy and len( self.__plugsToWidgets ) == 0 :
			self.__update()

		w = self.__plugsToWidgets.get( childPlug, None )
		if w is None :
			return w
		elif isinstance( w, GafferUI.PlugValueWidget ) :
			return w
		else :
			return w.plugValueWidget()
		
	def __update( self ) :
	
		# get the plugs we want to represent
		plugs = self.__parent.children( Gaffer.Plug.staticTypeId() )
		plugs = [ plug for plug in plugs if not plug.getName().startswith( "__" ) ]
				
		# ditch widgets we don't need any more
		plugsSet = set( plugs )
		self.__plugsToWidgets = dict(
			( plug, widget ) for plug, widget in self.__plugsToWidgets.items() if plug in plugsSet
		)
					
		# make (or reuse existing) uis for each plug
		orderedWidgets = []
		for plug in plugs :
			if plug not in self.__plugsToWidgets :
				widget = self.__createPlugWidget( plug )
				self.__plugsToWidgets[plug] = widget
			else :
				widget = self.__plugsToWidgets[plug]
			
			if widget is not None :	
				orderedWidgets.append( widget )
				if Gaffer.Metadata.plugValue( plug, "divider" ) :
					orderedWidgets.append( GafferUI.Divider(
						GafferUI.Divider.Orientation.Horizontal if self.__mainContainer.orientation() == GafferUI.ListContainer.Orientation.Vertical else GafferUI.Divider.Orientation.Vertical
					) )
					
		# and update the column to display them in the right order
		self.__mainContainer[:] = orderedWidgets

 	def __createPlugWidget( self, plug ) :
 	
 		result = GafferUI.PlugValueWidget.create( plug )
 		if result is None :
 			return result
 			
 		if not result.hasLabel() and Gaffer.Metadata.plugValue( plug, "label" ) != "" :
 			result = GafferUI.PlugWidget( result )
			if self.__mainContainer.orientation() == GafferUI.ListContainer.Orientation.Horizontal :
				# undo the annoying fixed size the PlugWidget has applied
				# to the label.
				## \todo Shift all the label size fixing out of PlugWidget and just fix the
				# widget here if we're in a vertical orientation.
				QWIDGETSIZE_MAX = 16777215 # qt #define not exposed by PyQt or PySide
				result.labelPlugValueWidget().label()._qtWidget().setFixedWidth( QWIDGETSIZE_MAX )
							
 		return result
	
	def __visibilityChanged( self, widget ) :
	
		assert( widget is self )
		if self.visible() :
			self.__update()
			del self.__visibilityChangedConnection # only need to build once
	
	def __childAddedOrRemoved( self, *unusedArgs ) :
	
		# typically many children are added and removed at once. we don't
		# want to be rebuilding the ui for each individual event, so we
		# add an idle callback to do the rebuild once the
		# upheaval is over.
	
		if not self.__childrenChangedPending :
			GafferUI.EventLoop.addIdleCallback( self.__childrenChanged )
			self.__childrenChangedPending = True
			
	def __childrenChanged( self ) :
		
		if not self.visible() :
			return
	
		self.__update()	
		self.__childrenChangedPending = False
		
		return False # removes the callback
