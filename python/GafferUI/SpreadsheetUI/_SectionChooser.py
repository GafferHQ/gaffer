##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

import functools
import re
import sys

import IECore

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtWidgets

class _SectionChooser( GafferUI.Widget ) :

	def __init__( self, rowsPlug, **kw ) :

		tabBar = QtWidgets.QTabBar()
		GafferUI.Widget.__init__( self, tabBar, **kw )

		self.__rowsPlug = rowsPlug
		self.__currentSectionChangedSignal = Gaffer.Signals.Signal1()

		tabBar.setDrawBase( False )
		tabBar.setMovable( True )
		tabBar.setExpanding( False )
		tabBar.setUsesScrollButtons( True )

		tabBar.setContextMenuPolicy( QtCore.Qt.CustomContextMenu )
		tabBar.customContextMenuRequested.connect( Gaffer.WeakMethod( self.__contextMenuRequested ) )

		tabBar.currentChanged.connect( Gaffer.WeakMethod( self.__currentChanged ) )
		self.__ignoreCurrentChanged = False
		tabBar.tabMoved.connect( Gaffer.WeakMethod( self.__tabMoved ) )
		self.__plugMetadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal( self.__rowsPlug.node() ).connect(
			Gaffer.WeakMethod( self.__plugMetadataChanged )
		)
		self.__rowsPlug.defaultRow()["cells"].childAddedSignal().connect( Gaffer.WeakMethod( self.__columnAdded ) )
		self.__rowsPlug.defaultRow()["cells"].childRemovedSignal().connect( Gaffer.WeakMethod( self.__columnRemoved ) )

		self.__updateTabs()

	def currentSection( self ) :

		if not self._qtWidget().count() :
			return None

		return self._qtWidget().tabText( self._qtWidget().currentIndex() )

	def currentSectionChangedSignal( self ) :

		return self.__currentSectionChangedSignal

	@classmethod
	def sectionNames( cls, rowsPlug ) :

		names = set()
		for cellPlug in rowsPlug.defaultRow()["cells"] :
			names.add( cls.getSection( cellPlug ) )

		if names == { "Other" } :
			# "Other" is a special section that we put columns into
			# automatically if they don't have any section metadata.
			# This helps us be robust to columns that are added directly
			# through the API by code unaware of sectioning. When _everything_
			# is in "Other", we automatically disable sectioning.
			return []

		namesAndIndices = []
		for name in sorted( list( names ) ) :
			index = len( namesAndIndices ) if name != "Other" else sys.maxsize
			metadataIndex = Gaffer.Metadata.value( rowsPlug, "spreadsheet:section:{}:index".format( name ) )
			index = metadataIndex if metadataIndex is not None else index
			namesAndIndices.append( ( name, index ) )

		namesAndIndices.sort( key = lambda x : x[1] )
		return [ x[0] for x in namesAndIndices ]

	@classmethod
	def setSection( cls, cellPlug, sectionName ) :

		rowsPlug = cellPlug.ancestor( Gaffer.Spreadsheet.RowsPlug )
		oldSectionNames = cls.sectionNames( rowsPlug )

		cls.__registerSectionMetadata( cellPlug, sectionName )

		# We may have made a new section and/or destroyed
		# an old one (by removing its last item). Reassign order
		# to put new sections where we want them, and to remove
		# gaps and old metadata.
		newSectionNames = cls.sectionNames( rowsPlug )
		if sectionName not in oldSectionNames :
			# New section created. Make sure it goes at the end, unless "Other"
			# is at the end, in which case put it in front of that.
			newSectionNames.remove( sectionName )
			if len( newSectionNames ) and newSectionNames[-1] == "Other" :
				newSectionNames.insert( -1, sectionName )
			else :
				newSectionNames.append( sectionName )

		cls.__assignSectionOrder( rowsPlug, newSectionNames )

	@classmethod
	def getSection( cls, cellPlug ) :

		return Gaffer.Metadata.value( cellPlug, "spreadsheet:section" ) or "Other"

	@classmethod
	def __registerSectionMetadata( cls, cellPlug, sectionName ) :

		if sectionName == "Other" :
			Gaffer.Metadata.deregisterValue( cellPlug, "spreadsheet:section" )
		else :
			Gaffer.Metadata.registerValue( cellPlug, "spreadsheet:section", sectionName )

	@classmethod
	def __assignSectionOrder( cls, rowsPlug, sectionNames ) :

		# Remove metadata for sections that no longer exist

		registeredValues = Gaffer.Metadata.registeredValues( rowsPlug, Gaffer.Metadata.RegistrationTypes.Instance )
		for key in registeredValues :
			m = re.match( "spreadsheet:section:(.+):index", key )
			if m and m.group( 1 ) not in sectionNames :
				Gaffer.Metadata.deregisterValue( rowsPlug, key )

		# Register indices for existing sections

		for i, sectionName in enumerate( sectionNames ) :
			Gaffer.Metadata.registerValue(
				rowsPlug,
				"spreadsheet:section:{}:index".format( sectionName ),
				i
			)

	def __plugMetadataChanged( self, plug, key, reason ) :

		if key == "spreadsheet:section" and self.__rowsPlug.isAncestorOf( plug ) :
			self.__updateTabs()
		elif re.match( "spreadsheet:section:.+:(index|description)", key ) and plug == self.__rowsPlug :
			self.__updateTabs()

	def __updateTabs( self ) :

		oldSectionNames = [ self._qtWidget().tabText( i ) for i in range( 0, self._qtWidget().count() ) ]
		newSectionNames = self.sectionNames( self.__rowsPlug )

		oldSectionToolTips = [ self._qtWidget().tabToolTip( i ) for i in range( 0, self._qtWidget().count() ) ]
		newSectionToolTips = [
			GafferUI.DocumentationAlgo.markdownToHTML(
				Gaffer.Metadata.value( self.__rowsPlug, "spreadsheet:section:{}:description".format( sectionName ) ) or ""
			)
			for sectionName in newSectionNames
		]

		if oldSectionNames == newSectionNames and oldSectionToolTips == newSectionToolTips :
			return

		currentSectionName = self._qtWidget().tabText( self._qtWidget().currentIndex() )

		self.__ignoreCurrentChanged = True
		try :
			while self._qtWidget().count() :
				self._qtWidget().removeTab( 0 )
			for index, sectionName in enumerate( newSectionNames ) :
				self._qtWidget().addTab( sectionName )
				self._qtWidget().setTabToolTip(
					index, newSectionToolTips[index]
				)
			if currentSectionName in newSectionNames :
				self.__setCurrent( newSectionNames.index( currentSectionName ) )
			else :
				self.currentSectionChangedSignal()( self )
		finally :
			self.__ignoreCurrentChanged = False

	def __setCurrent( self, index ) :

		self._qtWidget().setCurrentIndex( index )

	def __currentChanged( self, index ) :

		if not self.__ignoreCurrentChanged :
			self.currentSectionChangedSignal()( self )

	def __tabMoved( self, fromIndex, toIndex ) :

		with Gaffer.Signals.BlockedConnection( self.__plugMetadataChangedConnection ) :
			with Gaffer.UndoScope( self.__rowsPlug.ancestor( Gaffer.ScriptNode ) ) :
				for i in range( 0, self._qtWidget().count() ) :
					sectionName = self._qtWidget().tabText( i )
					Gaffer.Metadata.registerValue( self.__rowsPlug, "spreadsheet:section:{}:index".format( sectionName ), i )

	def __columnAdded( self, cellsPlug, cellPlug ) :

		self.__updateTabs()

	def __columnRemoved( self, cellsPlug, cellPlug ) :

		self.__updateTabs()

	def __renameSection( self, sectionName ) :

		sectionNames = self.sectionNames( self.__rowsPlug )
		assert( sectionName in sectionNames )
		sectionIsCurrent = self._qtWidget().tabText( self._qtWidget().currentIndex() ) == sectionName

		newSectionName = GafferUI.TextInputDialogue(
			title = "Rename section",
			initialText = sectionName,
			confirmLabel = "Rename",
		).waitForText( parentWindow = self.ancestor( GafferUI.Window ) )

		if not newSectionName or newSectionName == sectionName :
			return

		if newSectionName in sectionNames :
			for suffix in range( 1, len( sectionNames ) + 2 ) :
				suffixedSectionName = newSectionName + str( suffix )
				if suffixedSectionName not in sectionNames :
					newSectionName = suffixedSectionName
					break

		with Gaffer.UndoScope( self.__rowsPlug.ancestor( Gaffer.ScriptNode ) ) :

			# Move appropriate columns to renamed section
			for cellPlug in self.__rowsPlug.defaultRow()["cells"] :
				if self.getSection( cellPlug ) == sectionName :
					# Using `__registerSectionMetadata()` rather than `setSection()`
					# because we call `__assignSectionOrder()` ourselves.
					self.__registerSectionMetadata( cellPlug, newSectionName )

			# Reapply section order for renamed section.
			self.__assignSectionOrder(
				self.__rowsPlug,
				[ newSectionName if n == sectionName else n for n in sectionNames ]
			)

			# And choose the renamed tab if necessary.
			if sectionIsCurrent :
				self.__setCurrent( sectionNames.index( sectionName ) )

	def __setSectionDescription( self, sectionName ) :

		metadataKey = "spreadsheet:section:{}:description".format( sectionName )

		description = GafferUI.TextInputDialogue(
			title = "Set Description",
			initialText = Gaffer.Metadata.value( self.__rowsPlug, metadataKey ),
			confirmLabel = "Set",
			multiLine = True,
		).waitForText( parentWindow = self.ancestor( GafferUI.Window ) )

		if description is not None :
			with Gaffer.UndoScope( self.__rowsPlug.ancestor( Gaffer.ScriptNode ) ) :
				Gaffer.Metadata.registerValue( self.__rowsPlug, metadataKey, description )

	def __deleteSection( self, sectionName ) :

		sectionNames = self.sectionNames( self.__rowsPlug )

		with Gaffer.UndoScope( self.__rowsPlug.ancestor( Gaffer.ScriptNode ) ) :
			# Iterate in reverse to avoid invalidating column indices we're
			# about to visit.
			for columnIndex, cellPlug in reversed( list( enumerate( self.__rowsPlug.defaultRow()["cells"] ) ) ) :
				if self.getSection( cellPlug ) == sectionName :
					self.__rowsPlug.removeColumn( columnIndex )
			# Reassign section indices to remove gap.
			self.__assignSectionOrder(
				self.__rowsPlug,
				[ n for n in sectionNames if n != sectionName ]
			)

	def __moveSection( self, fromSectionName, toSectionName ) :

		sectionNames = self.sectionNames( self.__rowsPlug )
		sectionIsCurrent = self._qtWidget().tabText( self._qtWidget().currentIndex() ) == fromSectionName

		with Gaffer.UndoScope( self.__rowsPlug.ancestor( Gaffer.ScriptNode ) ) :

			# Move columns
			for cellPlug in self.__rowsPlug.defaultRow()["cells"] :
				if self.getSection( cellPlug ) == fromSectionName :
					# Using `__registerSectionMetadata()` rather than `setSection()`
					# because we call `__assignSectionOrder()` ourselves.
					self.__registerSectionMetadata( cellPlug, toSectionName )

			# Reapply section order to remove gaps.
			newSectionNames = [ n for n in sectionNames if n != fromSectionName ]
			self.__assignSectionOrder( self.__rowsPlug, newSectionNames )

			if sectionIsCurrent :
				self.__setCurrent( newSectionNames.index( toSectionName ) )

	def __removeSectioning( self ) :

		with Gaffer.UndoScope( self.__rowsPlug.ancestor( Gaffer.ScriptNode ) ) :

			for cellPlug in self.__rowsPlug.defaultRow()["cells"] :
				# Using `__registerSectionMetadata()` rather than `setSection()`
				# because we call `__assignSectionOrder()` ourselves.
				self.__registerSectionMetadata( cellPlug, "Other" )

			self.__assignSectionOrder( self.__rowsPlug, [] )

	def __contextMenuRequested( self, pos ) :

		m = IECore.MenuDefinition()
		sectionName = self._qtWidget().tabText( self._qtWidget().tabAt( pos ) )

		for index, name in enumerate( self.sectionNames( self.__rowsPlug ) ) :
			m.append(
				"/Switch to/%s" % name,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setCurrent ), index )
				}
			)

		m.append( "/__EditDivider__", { "divider" : True } )

		readOnly = Gaffer.MetadataAlgo.readOnly( self.__rowsPlug )

		m.append(
			"/Rename...",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__renameSection ), sectionName ),
				"active" : not readOnly,
			}
		)

		m.append(
			"/Set Description...",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__setSectionDescription ), sectionName ),
				"active" : not readOnly,
			}
		)

		sectionNames = self.sectionNames( self.__rowsPlug )
		for toSectionName in sectionNames :
			m.append(
				"/Move Columns To/{}".format( toSectionName ),
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__moveSection ), sectionName, toSectionName ),
					"active" : toSectionName != sectionName and not readOnly,
				}
			)

		m.append( "/__DeleteDivider__", { "divider" : True } )

		m.append(
			"/Delete",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__deleteSection ), sectionName ),
				"active" : not readOnly,
			}
		)

		m.append( "/__RemoveDivider__", { "divider" : True } )

		m.append(
			"/Remove Sectioning",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__removeSectioning ) ),
				"active" : not readOnly,
			}
		)

		self.__contextMenu = GafferUI.Menu( m )
		self.__contextMenu.popup( parent = self )
