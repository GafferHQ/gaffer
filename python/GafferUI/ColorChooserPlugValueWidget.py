##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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
import imath

import IECore

import Gaffer
import GafferUI
from GafferUI.PlugValueWidget import sole

class ColorChooserPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__colorChooser = GafferUI.ColorChooser()

		GafferUI.PlugValueWidget.__init__( self, self.__colorChooser, plugs, **kw )

		self.__colorChooser.setSwatchesVisible( False )

		visibleComponents = self.__colorChooserOption( "visibleComponents" )
		if visibleComponents is not None :
			self.__colorChooser.setVisibleComponents( visibleComponents )

		staticComponent = self.__colorChooserOption( "staticComponent" )
		if staticComponent is not None :
			self.__colorChooser.setColorFieldStaticComponent( staticComponent )

		colorFieldVisible = self.__colorChooserOption( "colorFieldVisible" )
		if colorFieldVisible is not None :
			self.__colorChooser.setColorFieldVisible( colorFieldVisible )

		self.__colorChangedConnection = self.__colorChooser.colorChangedSignal().connect(
			Gaffer.WeakMethod( self.__colorChanged ), scoped = False
		)

		self.__colorChooser.visibleComponentsChangedSignal().connect(
			functools.partial( Gaffer.WeakMethod( self.__colorChooserVisibleComponentsChanged ) ),
			scoped = False
		)
		self.__colorChooser.staticComponentChangedSignal().connect(
			functools.partial( Gaffer.WeakMethod( self.__colorChooserStaticComponentChanged ) ),
			scoped = False
		)
		self.__colorChooser.colorFieldVisibleChangedSignal().connect(
			functools.partial( Gaffer.WeakMethod( self.__colorChooserColorFieldVisibleChanged ) ),
			scoped = False
		)
		self.__colorChooser.optionsMenuSignal().connect(
			functools.partial( Gaffer.WeakMethod( self.__colorChooserOptionsMenu ) ),
			scoped = False
		)

		self.__lastChangedReason = None
		self.__mergeGroupId = 0

	def _updateFromValues( self, values, exception ) :

		# ColorChooser only supports one colour, and doesn't have
		# an "indeterminate" state, so when we have multiple plugs
		# the best we can do is take an average.
		if len( values ) :
			color = sum( values ) / len( values )
		else :
			color = imath.Color4f( 0 )

		with Gaffer.Signals.BlockedConnection( self.__colorChangedConnection ) :
			self.__colorChooser.setColor( color )
			self.__colorChooser.setErrored( exception is not None )

	def _updateFromEditable( self ) :

		self.__colorChooser.setEnabled( self.__allComponentsEditable() )

	def __colorChanged( self, colorChooser, reason ) :

		if not GafferUI.ColorChooser.changesShouldBeMerged( self.__lastChangedReason, reason ) :
			self.__mergeGroupId += 1
		self.__lastChangedReason = reason

		with Gaffer.UndoScope(
			next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ),
			mergeGroup = "ColorPlugValueWidget%d%d" % ( id( self, ), self.__mergeGroupId )
		) :

			with self._blockedUpdateFromValues() :
				for plug in self.getPlugs() :
					plug.setValue( self.__colorChooser.getColor() )

	def __colorChooserOptionChanged( self, keySuffix, value ) :

		for p in self.getPlugs() :
			Gaffer.Metadata.deregisterValue( p, "colorChooser:inline:" + keySuffix )
			Gaffer.Metadata.registerValue( p, "colorChooser:inline:" + keySuffix, value, persistent = False )

	def __colorChooserOption( self, keySuffix ) :

		return sole( Gaffer.Metadata.value( p, "colorChooser:inline:" + keySuffix ) for p in self.getPlugs() )

	def __colorChooserVisibleComponentsChanged( self, colorChooser ) :

		self.__colorChooserOptionChanged( "visibleComponents", colorChooser.getVisibleComponents() )

	def __colorChooserStaticComponentChanged( self, colorChooser ) :

		self.__colorChooserOptionChanged( "staticComponent", colorChooser.getColorFieldStaticComponent() )

	def __colorChooserColorFieldVisibleChanged( self, colorChooser ) :

		self.__colorChooserOptionChanged( "colorFieldVisible", colorChooser.getColorFieldVisible() )

	def __colorChooserOptionsMenu( self, colorChooser, menuDefinition ) :

		menuDefinition.append( "/__saveDefaultOptions__", { "divider": True, "label": "Defaults" } )

		menuDefinition.append(
			"/Save Inline Defaults",
			{
				"command": functools.partial(
					saveDefaultOptions,
					colorChooser,
					"colorChooser:inline:",
					self.ancestor( GafferUI.ScriptWindow ).scriptNode().applicationRoot().preferencesLocation() / "__colorChooser.py"
				),
			}
		)

	def __allComponentsEditable( self ) :

		if not self._editable() :
			return False

		# The base class `_editable()` call doesn't consider that
		# child plugs might be read only, so check for that.
		## \todo Should the base class be doing this for us?
		for plug in self.getPlugs() :
			for child in Gaffer.Plug.Range( plug ) :
				if Gaffer.MetadataAlgo.readOnly( child ) :
					return False

		return True

def saveDefaultOptions( colorChooser, keyPrefix, scriptPath = None ) :

	for k in [ "visibleComponents", "staticComponent", "colorFieldVisible" ] :
		Gaffer.Metadata.deregisterValue( Gaffer.Color3fPlug, keyPrefix + k )
		Gaffer.Metadata.deregisterValue( Gaffer.Color4fPlug, keyPrefix + k )

	visibleComponents = colorChooser.getVisibleComponents()
	Gaffer.Metadata.registerValue( Gaffer.Color3fPlug, keyPrefix + "visibleComponents", visibleComponents )
	Gaffer.Metadata.registerValue( Gaffer.Color4fPlug, keyPrefix + "visibleComponents", visibleComponents )

	staticComponent = colorChooser.getColorFieldStaticComponent()
	Gaffer.Metadata.registerValue( Gaffer.Color3fPlug, keyPrefix + "staticComponent", staticComponent )
	Gaffer.Metadata.registerValue( Gaffer.Color4fPlug, keyPrefix + "staticComponent", staticComponent )

	colorFieldVisible = colorChooser.getColorFieldVisible()
	Gaffer.Metadata.registerValue( Gaffer.Color3fPlug, keyPrefix + "colorFieldVisible", colorFieldVisible )
	Gaffer.Metadata.registerValue( Gaffer.Color4fPlug, keyPrefix + "colorFieldVisible", colorFieldVisible )

	if scriptPath is None :
		return

	if scriptPath.is_dir() :
		raise RuntimeError( f"Cannot write Color Chooser default options script \"{scriptPath}\", a directory at that path exists.")

	if scriptPath.exists() :
		with open( scriptPath, "r" ) as inFile :
			script = inFile.readlines()
	else :
		script = [
			"# This file was automatically generated by Gaffer.\n",
			"# Do not edit this file - it will be overwritten.\n",
			"\n",
			"import Gaffer\n",
			"\n"
		]

	newScript = [l for l in script if keyPrefix not in l]

	for c in [ "3", "4" ] :
		newScript.append( f"Gaffer.Metadata.registerValue( Gaffer.Color{c}fPlug, \"{keyPrefix}visibleComponents\", \"{visibleComponents}\" )\n" )
		newScript.append( f"Gaffer.Metadata.registerValue( Gaffer.Color{c}fPlug, \"{keyPrefix}staticComponent\", \"{staticComponent}\" )\n" )
		newScript.append( f"Gaffer.Metadata.registerValue( Gaffer.Color{c}fPlug, \"{keyPrefix}colorFieldVisible\", {colorFieldVisible} )\n" )

	with open( scriptPath, "w" ) as outFile :
		outFile.writelines( newScript )