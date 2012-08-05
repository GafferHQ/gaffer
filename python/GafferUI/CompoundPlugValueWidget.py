##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import IECore

import Gaffer
import GafferUI

class CompoundPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, collapsible=True, label=None, **kw ) :

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 )
		
		self.__collapsible = None
		if collapsible :
			self.__collapsible = GafferUI.Collapsible(
				label if label else IECore.CamelCase.toSpaced( plug.getName() ),
				collapsed = True,
			)
			self.__collapsible.setChild( self.__column )
				
		GafferUI.PlugValueWidget.__init__(
			self,
			self.__collapsible if self.__collapsible is not None else self.__column,
			plug,
			**kw
		)

		self.__plugAddedConnection = plug.childAddedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ) )
		self.__plugRemovedConnection = plug.childRemovedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ) )
		self.__childrenChangedPending = False

		self.__visibilityChangedConnection = self.__column.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__visibilityChanged ) )
		self.__childPlugUIs = {} # mapping from child plug name to PlugWidget

	def hasLabel( self ) :
	
		return True

	def _updateFromPlug( self ) :
	
		pass
	
	## May be overridden by derived classes to return a widget to be placed
	# at the top of the layout.	
	def _headerWidget( self ) :
	
		return None

	## May be overridden by derived classes to customise the creation of widgets
	# to represent the child plugs.	
	def _childPlugWidget( self, childPlug ) :
	
		result = GafferUI.PlugValueWidget.create( childPlug )
		if result is not None and not isinstance( result, CompoundPlugValueWidget ) :
			result = GafferUI.PlugWidget( result )

		return result
	
	## May be overridden by derived classes to return a widget to be placed
	# at the bottom of the layout.	
	def _footerWidget( self ) :
	
		return None
	
	## Returns True if this ui is collapsible
	def _collapsible( self ) :
		
		return self.__collapsible is not None
	
	## May be overridden by derived classes to specify which child plugs
	# are represented and in what order.
	def _childPlugs( self ) :
	
		return self.getPlug().children()
	
	def __updateChildPlugUIs( self ) :
	
		# ditch child uis we don't need any more
		childNames = set( self.getPlug().keys() )
		for childName in self.__childPlugUIs.keys() :
			if childName not in childNames :
				del self.__childPlugUIs[childName]
				
		# make (or reuse existing) uis for each child plug
		orderedChildUIs = []
		for childPlug in self._childPlugs() :
			if childPlug.getName().startswith( "__" ) :
				continue
			if childPlug.getName() not in self.__childPlugUIs :
				self.__childPlugUIs[childPlug.getName()] = self._childPlugWidget( childPlug )
			widget = self.__childPlugUIs[childPlug.getName()]
			if widget is not None :	
				orderedChildUIs.append( widget )
		
		# add header and footer
		headerWidget = self._headerWidget()
		if headerWidget is not None :
			orderedChildUIs.insert( 0, headerWidget )
		footerWidget = self._footerWidget()
		if footerWidget is not None :
			orderedChildUIs.append( footerWidget )
			
		# and update the column to display them
		self.__column[:] = orderedChildUIs
	
	def __visibilityChanged( self, column ) :
	
		assert( column is self.__column )
		
		if self.__column.visible() :
			self.__updateChildPlugUIs()
			self.__visibilityChangedConnection = None # only need to build once
	
	def __childAddedOrRemoved( self, *unusedArgs ) :
	
		# typically many children are added and removed at once. we don't
		# want to be rebuilding the ui for each individual event, so we
		# add an idle callback to do the rebuild once the
		# upheaval is over.
	
		if not self.__childrenChangedPending :
			GafferUI.EventLoop.addIdleCallback( self.__childrenChanged )
			self.__childrenChangedPending = True
			
	def __childrenChanged( self ) :
			
		if not self.__column.visible() :
			return
	
		self.__updateChildPlugUIs()	
		self.__childrenChangedPending = False
		
		return False # removes the callback

GafferUI.PlugValueWidget.registerType( Gaffer.CompoundPlug.staticTypeId(), CompoundPlugValueWidget )
