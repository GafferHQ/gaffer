##########################################################################
#  
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUI
import GafferImage

QtGui = GafferUI._qtImport( "QtGui" )

class FormatPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :
		self.__selectionMenu = GafferUI.SelectionMenu()
		GafferUI.PlugValueWidget.__init__( self, self.__selectionMenu, plug, **kw )
		
		self.__formatAddedConnection = GafferImage.Format.formatAddedSignal().connect( Gaffer.WeakMethod( self.__formatAdded ) )
		self.__formatRemovedConnection = GafferImage.Format.formatRemovedSignal().connect( Gaffer.WeakMethod( self.__formatRemoved ) )
		
		# Get the script node that holds the default format.
		self.__scriptNode = plug.ancestor( Gaffer.ScriptNode.staticTypeId() )
		
		# Is this the default format plug?
		self.__isDefaultFormatPlug = self.__scriptNode.isSame( plug.node() )
		
		# Populate the widget with the names of the available formats
		formatNames = GafferImage.Format.formatNames()
		
		self.__formatNameAndValues = []
		
		# If this plug is on the script node then do not add any "NULL" (empty) formats.
		for i in range( 0, len( formatNames ) ) :
			name = formatNames[i]
			format = GafferImage.Format.getFormat( name )
			self.__selectionMenu.addItem( name )
			self.__formatNameAndValues.append( ( name, format ) )
			
		# Do not add the "Default Format" option if this is in fact the default format plug!
		if not self.__isDefaultFormatPlug :
			self.__selectionMenu.insertItem( 0, "Default Format" )
			self.__formatNameAndValues.insert( 0, ( "Default Format", GafferImage.Format() ) )
			
		self.__currentChangedConnection = self.__selectionMenu.currentIndexChangedSignal().connect( Gaffer.WeakMethod( self.__currentChanged ) )
		self._updateFromPlug()
	
	def __formatAdded( self, name ) :
		self.__formatNameAndValues.append( ( name, GafferImage.Format.getFormat( name ) ) )
		self.__selectionMenu.insertItem( self.__selectionMenu.getTotal()-1, name )
	
	def __formatRemoved( self, name ) :
		for index, formatNameAndValue in enumerate( self.__formatNameAndValues ) :
			if formatNameAndValue[0] == name:
				self.__selectionMenu.removeIndex( index )
				del self.__formatNameAndValues[index]
				return
	
	def _updateFromPlug( self ) :
		if self.getPlug() is not None:
			with self.getContext() :
			
				# Check to see if the format is the default instance. If so then it means we are tracking
				# the default format and therefore do not need to change the UI.
				if self.getPlug().getValue().getDisplayWindow().isEmpty() and not self.__isDefaultFormatPlug :
					self.__selectionMenu.setCurrentIndex( 0 )
					return
				
				plugValue = self.getPlug().getValue()
				
				matchingIndex = None
				for index, formatNameAndValue in enumerate( self.__formatNameAndValues ) :
					format = formatNameAndValue[1]
					if format == plugValue :
						matchingIndex = index
						break
				if matchingIndex is not None :
					with Gaffer.BlockedConnection( self.__currentChangedConnection ) :
						self.__selectionMenu.setCurrentIndex( matchingIndex )
				else:
					GafferImage.Format.registerFormat( plugValue )
					with Gaffer.BlockedConnection( self.__currentChangedConnection ) :
						self.__selectionMenu.setCurrentIndex( self.__selectionMenu.getTotal()-1 )
		
		self.__selectionMenu.setEnabled( self._editable() )
	
	def __currentChanged( self, selectionMenu ) :
		index = self.__selectionMenu.getCurrentIndex()
		nameAndValue = self.__formatNameAndValues[ index ]
		if self.__isDefaultFormatPlug :
			GafferImage.Format.setDefaultFormat( self.__scriptNode, nameAndValue[1] )
		else :
			self.getPlug().setValue( nameAndValue[1] )
		
		with Gaffer.UndoContext( self.__scriptNode ) :
			self.getPlug().setValue( nameAndValue[1] )
	
	def __getitem__( self, key ) :
		if isinstance( key, int ) :
			return self.__formatNameAndValues[ key ]
		if isinstance( key, str ) :
			for index, formatNameAndValue in enumerate( self.__formatNameAndValues ) :
				if formatNameAndValue[0] == key :
					return formatNameAndValue[1]
		if isinstance( key, GafferImage.Format ) :
			for index, formatNameAndValue in enumerate( self.__formatNameAndValues ) :
				if formatNameAndValue[1] == key :
					return formatNameAndValue[0]
	
	def __len__( self ) :
		return self.__selectionMenu.getTotal()
	
GafferUI.PlugValueWidget.registerType( GafferImage.FormatPlug.staticTypeId(), FormatPlugValueWidget )
