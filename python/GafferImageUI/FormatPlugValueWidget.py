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
		self.__multiSelectionMenu = GafferUI.MultiSelectionMenu( allowMultipleSelection = False, alwaysHaveASelection = True)
		GafferUI.PlugValueWidget.__init__( self, self.__multiSelectionMenu, plug, **kw )

		self.__formatAddedConnection = GafferImage.Format.formatAddedSignal().connect( Gaffer.WeakMethod( self.__formatAdded ) )
		self.__formatRemovedConnection = GafferImage.Format.formatRemovedSignal().connect( Gaffer.WeakMethod( self.__formatRemoved ) )

		# Get the script node that holds the default format.
		self.__scriptNode = plug.ancestor( Gaffer.ScriptNode )

		# Is this the default format plug?
		self.__isDefaultFormatPlug = self.__scriptNode.isSame( plug.node() )

		# Populate the widget with the names of the available formats
		formatNames = GafferImage.Format.formatNames()
		self.__multiSelectionMenu[:] = formatNames

		# Create a mapping of the names to the formats.
		self.__formats = {}.fromkeys( formatNames )
		for name in formatNames :
			self.__formats[name] = GafferImage.Format.getFormat( name )

		# Add the "Default Format" option if this is not the default format plug!
		if not self.__isDefaultFormatPlug :
			self.__multiSelectionMenu.insert( 0, "Default Format" )
			self.__formats["Default Format"] = GafferImage.Format()

		self.__currentChangedConnection = self.__multiSelectionMenu.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__currentChanged ) )
		self._updateFromPlug()

	def __formatAdded( self, name ) :
		self.__formats[name] = GafferImage.Format.getFormat( name )
		self.__multiSelectionMenu.append( name )

	def __formatRemoved( self, name ) :
		self.__multiSelectionMenu.remove( name )
		self.__formats.remove( name )

	def _updateFromPlug( self ) :
		self.__multiSelectionMenu.setEnabled( self._editable() )
		if self.getPlug() is not None:
			with self.getContext() :

				# Check to see if the format is the default instance. If so then it means we are tracking
				# the default format and therefore do not need to change the UI.
				if self.getPlug().getValue().getDisplayWindow().isEmpty() and not self.__isDefaultFormatPlug :
					self.__multiSelectionMenu.setSelection( "Default Format" )
					return

				# Otherwise update the UI from the plug.
				plugValue = self.getPlug().getValue()
				for name in self.__formats.keys() :
					format = self.__formats[name]
					if format == plugValue :
						with Gaffer.BlockedConnection( self.__currentChangedConnection ) :
							self.__multiSelectionMenu.setSelection( name )

						return

				# The format is new so we should add it to our menu...
				GafferImage.Format.registerFormat( plugValue )
				with Gaffer.BlockedConnection( self.__currentChangedConnection ) :
					self.__multiSelectionMenu.setSelection( self.__multiSelectionMenu[-1] )

	def __currentChanged( self, multiSelectionMenu ) :
		selected = self.__multiSelectionMenu.getSelection()
		format = self.__formats[ selected[0] ]

		if self.__isDefaultFormatPlug :
			GafferImage.Format.setDefaultFormat( self.__scriptNode, format )
		else :
			self.getPlug().setValue( format )

		with Gaffer.UndoContext( self.__scriptNode ) :
			self.getPlug().setValue( format )

	def __getitem__( self, key ) :
		if isinstance( key, int ) :
			return ( self.__multiSelectionMenu[key], self.__formats[self.__multiSelectionMenu[key]] )
		if isinstance( key, str ) :
			return self.__formats[key]
		if isinstance( key, GafferImage.Format ) :
			for name in self.__formats.keys() :
				if self.__formats[name] == key :
					return name

	def __len__( self ) :
		return len( self.__multiSelectionMenu )

GafferUI.PlugValueWidget.registerType( GafferImage.FormatPlug, FormatPlugValueWidget )

