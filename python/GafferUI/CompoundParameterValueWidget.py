##########################################################################
#  
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI

## Supported parameter userData entries :
#
# ["UI"]["collapsible"]
# ["UI"]["collapsed"]
#
# Supported child userData entries :
#
# ["UI"]["visible"]
class CompoundParameterValueWidget( GafferUI.ParameterValueWidget ) :

	_columnSpacing = 4
	_labelWidth = 110

	## If collapsible is not None then it overrides any ["UI]["collapsible"] userData the parameter might have.
	def __init__( self, parameterHandler, collapsible=None, **kw ) :
		
		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = self._columnSpacing )
		
		if collapsible is None :
			collapsible = True
			with IECore.IgnoredExceptions( KeyError ) :
				collapsible = parameterHandler.parameter().userData()["UI"]["collapsible"].value
		
		self.__collapsible = None
		if collapsible :
			collapsibleLabel = IECore.CamelCase.toSpaced( parameterHandler.plug().getName() )
			self.__collapsible = GafferUI.Collapsible( label = collapsibleLabel, collapsed = True )
			self.__collapsible.setChild( self.__column )
			topLevelWidget = self.__collapsible
		else :
			topLevelWidget = self.__column
			
		GafferUI.ParameterValueWidget.__init__( self, topLevelWidget, parameterHandler, **kw )
		
		self.__plugAddedConnection = parameterHandler.plug().childAddedSignal().connect( self.__childAddedOrRemoved )
		self.__plugRemovedConnection = parameterHandler.plug().childRemovedSignal().connect( self.__childAddedOrRemoved )
		self.__childrenChangedPending = False
		
		if collapsible :
			collapsed = True
			with IECore.IgnoredExceptions( KeyError ) :
				collapsed = parameterHandler.parameter().userData()["UI"]["collapsed"].value
			self.__collapsibleStateChangedConnection = self.__collapsible.stateChangedSignal().connect( Gaffer.WeakMethod( self.__collapsibleStateChanged ) )
			self.__collapsible.setCollapsed( collapsed )
		else :
			self._buildChildParameterUIs( self.__column )

	## May be overridden by derived classes to customise the creation of the UI to represent child parameters.
	# The UI elements created should be placed in the ListContainer passed as column. Note that this may be 
	# called multiple times, as it will be called again when plugs are added or removed. In this case you are
	# responsible for removing any previous ui from column as appropriate.
	def _buildChildParameterUIs( self, column ) :
	
		del column[:]
	
		for childPlug in self.plug().children() :
		
			childParameter = self.parameter()[childPlug.getName()]
			
			with IECore.IgnoredExceptions( KeyError ) :
				if not childParameter.userData()["UI"]["visible"].value :
					continue
			
			valueWidget = GafferUI.ParameterValueWidget.create( self.parameterHandler().childParameterHandler( childParameter ) )
			if not valueWidget :
				continue
				
			if isinstance( valueWidget, CompoundParameterValueWidget ) :
			
				self.__column.append( valueWidget )
				
			else :
			
				row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 8 )
				
				label = GafferUI.Label(
					IECore.CamelCase.toSpaced( childPlug.getName() ),
					horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right
				)
				label.setToolTip( IECore.StringUtil.wrap(
						childPlug.relativeName( childPlug.node() ) + "\n\n" +
						childParameter.description,
						60
					)
				)
				
				## \todo Decide how we allow this sort of tweak using the public
				# interface. Perhaps we should have a SizeableContainer or something?
				label._qtWidget().setMinimumWidth( self._labelWidth )
				label._qtWidget().setMaximumWidth( self._labelWidth )
		
				row.append( label )
				row.append( valueWidget )
				
				self.__column.append( row )

	def __collapsibleStateChanged( self, *unusedArgs ) :
	
		if len( self.__column ) :
			return
			
		self._buildChildParameterUIs( self.__column )

	def __childAddedOrRemoved( self, *unusedArgs ) :
	
		# typically many children are added and removed at once. we don't want to be rebuilding the
		# ui for each individual event, so we add an idle callback to do the rebuild once the
		# upheaval is over.
	
		if not self.__childrenChangedPending :
			GafferUI.EventLoop.addIdleCallback( self.__childrenChanged )
			self.__childrenChangedPending = True
			
	def __childrenChanged( self ) :
	
		if self.__collapsible is not None and not self.__collapsible.getCollapsed() :
			return
	
		try :
			self._buildChildParameterUIs( self.__column )
		except :
			# catching errors because not returning False from this
			# function causes the callback to not be removed, the error
			# to be repeated etc...
			pass
			
		self.__childrenChangedPending = False
		
		return False # removes the callback

GafferUI.ParameterValueWidget.registerType( IECore.CompoundParameter.staticTypeId(), CompoundParameterValueWidget )
