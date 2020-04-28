##########################################################################
#
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

import os
import re
import shutil

import IECore
import IECoreScene

import Gaffer
import GafferUI
import GafferCortex
import GafferCortexUI

class PresetDialogue( GafferUI.Dialogue ) :

	def __init__( self, title, parameterHandler ) :

		GafferUI.Dialogue.__init__( self, title )

		self._parameterHandler = parameterHandler
		self.__locationMenu = None
		self.__presetListing = None

	def _locationMenu( self, owned=False, writable=False, **kw ) :

		if self.__locationMenu is None :
			self.__locationMenu = GafferUI.SelectionMenu( **kw )
			for searchPath in self.__searchPaths( owned, writable ) :
				self.__locationMenu.addItem( searchPath )

		return self.__locationMenu

	def _presetListing( self, allowMultipleSelection=False, **kw ) :

		if self.__presetListing is None :
			self.__presetListing = GafferUI.PathListingWidget(
				Gaffer.DictPath( {}, "/" ),
				columns = [ GafferUI.PathListingWidget.defaultNameColumn ],
				displayMode = GafferUI.PathListingWidget.DisplayMode.Tree,
				allowMultipleSelection = allowMultipleSelection,
			)
			self.__locationMenuChangedConnection = self._locationMenu().currentIndexChangedSignal().connect( Gaffer.WeakMethod( self.__locationChanged ) )
			self._updatePresetListing()

		return self.__presetListing

	def _updatePresetListing( self ) :

		location = self.__locationMenu.getCurrentItem()
		presetLoader = IECore.ClassLoader( IECore.SearchPath( location ) )
		parameterised = self._parameterHandler.plug().node().getParameterised()[0]

		d = {}
		for presetName in presetLoader.classNames() :
			preset = presetLoader.load( presetName )()
			if preset.applicableTo( parameterised, self._parameterHandler.parameter() ) :
				d[preset.metadata()["title"]] = preset

		self.__presetListing.setPath( Gaffer.DictPath( d, "/" ) )
		self.__presetListing.selectionChangedSignal()( self.__presetListing )

	def _selectedPresets( self ) :

		selection = self.__presetListing.getSelectedPaths()
		return [ p.info()["dict:value"] for p in selection ]

	def __searchPaths( self, owned, writable ) :

		searchPathEnvVar = _searchPathEnvVar( self._parameterHandler.plug().node() )
		paths = os.environ[searchPathEnvVar].split( ":" )

		existingPaths = []
		for path in paths :
			if not os.path.isdir( path ) :
				with IECore.IgnoredExceptions( Exception ) :
					os.makedirs( path )
			if os.path.isdir( path ) :
				if owned and os.stat( path ).st_uid != os.getuid() :
					continue
				if writable and not os.access( path, os.W_OK ) :
					continue
				existingPaths.append( path )

		return existingPaths

	def __locationChanged( self, locationMenu ) :

		self._updatePresetListing()

class SavePresetDialogue( PresetDialogue ) :

	__defaultName = "Enter a name!"

	def __init__( self, parameterHandler ) :

		PresetDialogue.__init__( self, "Save Preset", parameterHandler )

		with GafferUI.ListContainer( spacing = 8 ) as column :
			with GafferUI.GridContainer( spacing = 6 ) :

				GafferUI.Label(
					"<h3>Location</h3>",
					parenting = {
						"index" : ( 0, 0 ),
						"alignment" : (
							GafferUI.Label.HorizontalAlignment.Right,
							GafferUI.Label.VerticalAlignment.None,
						),
					}
				)
				self._locationMenu( writable=True, parenting = { "index" : ( slice( 1, 3 ), 0 ) } )

				GafferUI.Label(
					"<h3>Name</h3>",
					parenting = {
						"index" : ( 0, 1 ),
						"alignment" : (
							GafferUI.Label.HorizontalAlignment.Right,
							GafferUI.Label.VerticalAlignment.None,
						),
					}
				)
				self.__presetNameWidget = GafferUI.TextWidget( self.__defaultName, parenting = { "index" : ( 1, 1 ) } )
				self.__presetNameWidget.setSelection( None, None ) # select all
				self.__presetNameChangedConnection = self.__presetNameWidget.textChangedSignal().connect( Gaffer.WeakMethod( self.__presetNameChanged ) )

				self.__loadAutomaticallyWidget = GafferUI.BoolWidget( "Load automatically", parenting = { "index" : ( 2, 1 ) } )
				self.__loadAutomaticallyChangedConnection = self.__loadAutomaticallyWidget.stateChangedSignal().connect( Gaffer.WeakMethod( self.__loadAutomaticallyChanged ) )

				GafferUI.Label(
					"<h3>Description</h3>",
					parenting = {
						"index" : ( 0, 2 ),
						"alignment" : (
							GafferUI.Label.HorizontalAlignment.Right,
							GafferUI.Label.VerticalAlignment.Top,
						),
					}
				)

				self.__presetDescriptionWidget = GafferUI.MultiLineTextWidget( parenting = { "index" : ( slice( 1, 3 ), 2 ) } )
				self.__presetDescriptionChangedConnection = self.__presetDescriptionWidget.textChangedSignal().connect( Gaffer.WeakMethod( self.__updateSaveButton ) )

			with GafferUI.Collapsible( "Parameters To Save", collapsed=True ) as cl :

				# forcing CompoundVectorParameter to act as a leaf, because allowing the selection of some children but not others
				# makes no sense (because they must all have the same length).
				parameterPath = GafferCortex.ParameterPath( parameterHandler.parameter(), "/", forcedLeafTypes = ( IECore.CompoundVectorParameter, ) )
				self.__parameterListing = GafferUI.PathListingWidget(
					parameterPath,
					columns = [ GafferUI.PathListingWidget.defaultNameColumn ],
					allowMultipleSelection = True,
					displayMode = GafferUI.PathListingWidget.DisplayMode.Tree
				)
				self.__parameterListing.setSelectedPaths( self.__allPaths( parameterPath ) )
				self.__haveSelectedParameters = True
				self.__selectionChangedConnection = self.__parameterListing.selectionChangedSignal().connect(
					Gaffer.WeakMethod( self.__selectionChanged )
				)

		self._setWidget( column )

		self._addButton( "Cancel" )
		self.__saveButton = self._addButton( "Save" )
		self.__saveButton.setEnabled( False )

	def waitForSave( self, **kw ) :

		self.__presetNameWidget.grabFocus()

		while 1 :

			button = self.waitForButton( **kw )
			if button is self.__saveButton :
				if self.__save() :
					return True
			else :
				return False

	def __save( self ) :

		self._parameterHandler.setParameterValue()
		parameterised = self._parameterHandler.plug().node().getParameterised()[0]
		preset = IECore.BasicPreset(
			parameterised,
			self._parameterHandler.parameter(),
			self.__selectedParameters()
		)

		presetLocation = self._locationMenu().getCurrentItem()
		# append the name of the class to the location, so that presets with
		# identical names (but for different classes) don't overwrite each
		# other.
		presetLocation = presetLocation + "/" + parameterised.typeName()

		presetName = self.__presetNameWidget.getText()
		# make a filename by sanitising the preset name.
		fileName = presetName.replace( " ", "_" )
		fileName = re.sub( '[^a-zA-Z0-9_]*', "", fileName )
		# We have to also make sure that the name doesn't begin with a number,
		# as it wouldn't be a legal class name in the resulting py stub.
		fileName = re.sub( '^[0-9]+', "", fileName )

		if os.path.exists( presetLocation + "/" + fileName ) :
			dialogue = GafferUI.ConfirmationDialogue(
				"Preset already exists!",
				"A preset named \"%s\" already exists.\nReplace it?" % presetName,
				confirmLabel = "Replace"
			)
			if not dialogue.waitForConfirmation( parentWindow = self ) :
				return False

		presetDescription = self.__presetDescriptionWidget.getText()

		preset.save( presetLocation, fileName, presetName, presetDescription )

		return True

	def __allPaths( self, path ) :

		result = [ path ]
		if not path.isLeaf() :
			for childPath in path.children() :
				result.extend( self.__allPaths( childPath ) )

		return result

	def __updateSaveButton( self, *unused ) :

		enabled = True

		presetName = self.__presetNameWidget.getText()
		if not presetName or presetName == "Enter a name!" :
			enabled = False

		if not self.__presetDescriptionWidget.getText() :
			enabled = False

		if not self.__haveSelectedParameters :
			enabled = False

		self.__saveButton.setEnabled( enabled )

	def __selectedParameters( self ) :

		result = []
		selectedPaths = self.__parameterListing.getSelectedPaths()
		for path in selectedPaths :
			if path.isLeaf() :
				result.append( path.info()["parameter:parameter"] )

		return result

	def __selectionChanged( self, pathListing ) :

		self.__haveSelectedParameters = bool( self.__selectedParameters() )
		self.__updateSaveButton()

	def __presetNameChanged( self, nameWidget ) :

		if nameWidget.getText() == _autoLoadName :
			self.__loadAutomaticallyWidget.setState( True )

		self.__updateSaveButton()

		return True

	def __loadAutomaticallyChanged( self, boolWidget ) :

		if boolWidget.getState() :
			self.__presetDescriptionWidget.setText( _autoLoadDescription )
			self.__presetNameWidget.setText( _autoLoadName )
		else :
			self.__presetDescriptionWidget.setText( "" )
			self.__presetNameWidget.setText( self.__defaultName )
			self.__presetNameWidget.setSelection( None, None ) # select all
			self.__presetNameWidget.grabFocus()

		self.__presetNameWidget.setEnabled( not boolWidget.getState() )
		self.__presetDescriptionWidget.setEnabled( not boolWidget.getState() )

		return True

class LoadPresetDialogue( PresetDialogue ) :

	def __init__( self, parameterHandler ) :

		PresetDialogue.__init__( self, "Load Preset", parameterHandler )

		with GafferUI.SplitContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal ) as row :

			with GafferUI.ListContainer( spacing=4 ) :

				with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

					GafferUI.Label(
						"<h3>Location</h3>",
						horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right
					)
					self._locationMenu()

				presetListing = self._presetListing()
				self.__selectionChangedConnection = presetListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ) )

			with GafferUI.ListContainer( spacing=4 ) :
				self.__presetDetailsLabel = GafferUI.Label( "<h3>Description</h3>" )
				self.__presetDetailsWidget = GafferUI.MultiLineTextWidget( editable = False )

		self._setWidget( row )

		self._addButton( "Cancel" )
		self.__loadButton = self._addButton( "Load" )
		self.__loadButton.setEnabled( False )

		row.setSizes( [ 0.5, 0.5 ] )

	def waitForLoad( self, **kw ) :

		button = self.waitForButton( **kw )
		if button is self.__loadButton :
			self.__load()
			return True

		return False

	def __load( self ) :

		preset = self._selectedPresets()[0]

		node = self._parameterHandler.plug().node()
		parameterised = node.getParameterised()[0]
		with node.parameterModificationContext() :
			preset( parameterised, self._parameterHandler.parameter() )

	def __selectionChanged( self, *unused ) :

		presets = self._selectedPresets()
		if not presets :
			loadEnabled = False
			text = "No preset selected"
		else :
			loadEnabled = True
			text = presets[0].metadata()["description"]
			if not text.strip() :
				text = "No description provided"

		self.__presetDetailsWidget.setText( text )
		self.__loadButton.setEnabled( loadEnabled )

class DeletePresetsDialogue( PresetDialogue ) :

	def __init__( self, parameterHandler ) :

		PresetDialogue.__init__( self, "Delete Preset", parameterHandler )

		with GafferUI.ListContainer( spacing=4 ) as column :

			with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				GafferUI.Label(
					"<h3>Location</h3>",
					horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right
				)
				self._locationMenu( owned=True )

			presetListing = self._presetListing( allowMultipleSelection=True )
			self.__selectionChangedConnection = presetListing.selectionChangedSignal().connect( Gaffer.WeakMethod( self.__selectionChanged ) )

		self._setWidget( column )

		self._addButton( "Close" )
		self.__deleteButton = self._addButton( "Delete" )
		self.__deleteButton.setEnabled( False )
		self.__deleteButtonPressedConnection = self.__deleteButton.clickedSignal().connect( Gaffer.WeakMethod( self.__delete ) )

	def waitForClose( self, **kw ) :

		self.waitForButton( **kw )

	def __selectionChanged( self, *unused ) :

		self.__deleteButton.setEnabled( len( self._selectedPresets() ) > 0 )

	def __delete( self, button ) :

		assert( button is self.__deleteButton )

		location = self._locationMenu().getCurrentItem()
		for preset in self._selectedPresets() :
			shutil.rmtree( location + "/" + preset.path )

		self._updatePresetListing()

## Applies the default "Load Automatically" preset to the specified ParameterisedHolder node.
def autoLoad( parameterisedHolder ) :

	searchPaths = os.environ.get( _searchPathEnvVar( parameterisedHolder ), "" )
	searchPaths = IECore.SearchPath( searchPaths )
	presetLoader = IECore.ClassLoader( searchPaths )

	parameterised = parameterisedHolder.getParameterised()[0]
	presetName = parameterised.typeName() + "/" + _autoLoadName

	if presetName not in presetLoader.classNames() :
		return

	preset = presetLoader.load( presetName )()
	with parameterisedHolder.parameterModificationContext() :
		preset( parameterised, parameterised.parameters() )

##########################################################################
# Private utility methods.
##########################################################################

_autoLoadName = "uiAutoLoad"
_autoLoadDescription = """This preset is loaded automatically - it can be used to set up the default user interface with the most commonly used settings."""

def _searchPathEnvVar( parameterisedHolder ) :

	parameterised = parameterisedHolder.getParameterised()

	searchPathEnvVar = parameterised[3]
	if not searchPathEnvVar :
		# we need to guess based on type
		if isinstance( parameterised[0], IECore.Op ) :
			searchPathEnvVar = "IECORE_OP_PATHS"
		else :
			raise Exception( "Unable to determine search paths for presets" )

	searchPathEnvVar = searchPathEnvVar.replace( "_PATHS", "_PRESET_PATHS" )

	return searchPathEnvVar

##########################################################################
# Plumbing to make the dialogues available from parameter menus.
##########################################################################

def __loadPreset( parameterHandler ) :

	dialogue = LoadPresetDialogue( parameterHandler )
	dialogue.waitForLoad()

def __savePreset( parameterHandler ) :

	dialogue = SavePresetDialogue( parameterHandler )
	dialogue.waitForSave()
	# \todo We should be giving the window a parent, but we can't
	# because GafferUI.Menu won't pass the menu argument to commands
	# which are curried functions.

def __deletePresets( parameterHandler ) :

	dialogue = DeletePresetsDialogue( parameterHandler )
	dialogue.waitForClose()

def __parameterPopupMenu( menuDefinition, parameterValueWidget ) :

	parameterHandler = parameterValueWidget.parameterHandler()
	if not parameterHandler.isSame( parameterHandler.plug().node().parameterHandler() ) :
		# only apply ourselves to the top level parameter for now
		return

	editable = parameterValueWidget.plugValueWidget()._editable()

	menuDefinition.append( "/PresetsDivider", { "divider" : True } )
	menuDefinition.append( "/Save Preset...", { "command" : IECore.curry( __savePreset, parameterHandler ) } )
	menuDefinition.append( "/Load Preset...", { "command" : IECore.curry( __loadPreset, parameterHandler ), "active" : editable } )
	menuDefinition.append( "/Delete Presets...", { "command" : IECore.curry( __deletePresets, parameterHandler ) } )

GafferCortexUI.ParameterValueWidget.popupMenuSignal().connect( __parameterPopupMenu, scoped = False )
