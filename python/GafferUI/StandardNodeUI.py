##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

import re
import fnmatch

import IECore

import Gaffer
import GafferUI

## A standard UI which should do the job fairly well for most node types. It supports the
# placement of plugs in different sections of the UI based on a "nodeUI:section" Metadata value
# associated with the plug. A value of "header" places the plug above the tabs, and all
# other values place the plug in a tab with the section name.
class StandardNodeUI( GafferUI.NodeUI ) :

	DisplayMode = IECore.Enum.create( "Tabbed", "Simplified" )

	def __init__( self, node, displayMode = None, **kw ) :

		self.__mainColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )

		GafferUI.NodeUI.__init__( self, node, self.__mainColumn, **kw )

		self.__displayMode = displayMode if displayMode is not None else self.DisplayMode.Tabbed

		self.__sectionColumns = {}
		if self.__displayMode == self.DisplayMode.Tabbed :

			headerColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
			self.__sectionColumns["header"] = headerColumn
			self.__mainColumn.append( headerColumn )

			self.__tabbedContainer = GafferUI.TabbedContainer()
			self.__mainColumn.append( self.__tabbedContainer )

		self.__buildPlugWidgets()

		# ScriptNode has an execute method but that is for something else.
		## \todo We need to base this on the new Executable class.
		if hasattr( node, "execute" ) and not isinstance( node, Gaffer.ScriptNode ) :
			settingsColumn = self.__sectionColumn( "Settings" )
			settingsColumn.append( GafferUI.ExecuteUI.ExecuteButton( self.node() ) )
			settingsColumn.append( GafferUI.Spacer( IECore.V2i( 1 ) ), expand = True )

		if self.__displayMode == self.DisplayMode.Tabbed :
			self.__tabbedContainer.setCurrent( self.__tabbedContainer[0] )

	## The top level layout for the standard node ui is a tabbed container. Derived
	# classes may access it using this function in order to add their own tabs
	def _tabbedContainer( self ) :

		return self.__tabbedContainer

	def __sectionColumn( self, sectionName ) :

		if self.__displayMode == self.DisplayMode.Simplified and sectionName != "Settings" :
			return None

		sectionColumn = self.__sectionColumns.get( sectionName, None )
		if sectionColumn is None :

			scrolledContainer = GafferUI.ScrolledContainer( horizontalMode=GafferUI.ScrolledContainer.ScrollMode.Never, borderWidth=8 )
			sectionColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing=4 )
			scrolledContainer.setChild( sectionColumn )

			if self.__displayMode == self.DisplayMode.Tabbed :
				self.__tabbedContainer.insert( 0, scrolledContainer, label = sectionName )
			else :
				self.__mainColumn.append( scrolledContainer, expand = True )

			self.__sectionColumns[sectionName] = sectionColumn

		return sectionColumn

	def __buildPlugWidgets( self ) :

		for plug in self.node().children( Gaffer.Plug.staticTypeId() ) :

			if plug.getName().startswith( "__" ) :
				continue
			widget = GafferUI.PlugValueWidget.create( plug )
			if widget is None :
				continue

			if isinstance( widget, GafferUI.PlugValueWidget ) and not widget.hasLabel() :
				widget = GafferUI.PlugWidget( widget )

			sectionName = GafferUI.Metadata.plugValue( plug, "nodeUI:section" ) or "Settings"
			sectionColumn = self.__sectionColumn( sectionName )
			if sectionColumn is not None :
				sectionColumn.append( widget )

GafferUI.NodeUI.registerNodeUI( Gaffer.Node.staticTypeId(), StandardNodeUI )
