##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
import GafferUSD

Gaffer.Metadata.registerNode(

	GafferUSD.USDLight,

	plugs = {

		"parameters" : {

			"layout:section:Basic:collapsed" : False,

			"layout:customWidget:parameterFilter:widgetType" : "GafferUSDUI.USDLightUI._ParameterFilter",
			"layout:customWidget:parameterFilter:index" : 0,

		},

		"parameters.colorTemperature" : { "layout:activator" : lambda plug : plug.parent()["enableColorTemperature"].getValue() },

		"parameters.shaping:ies:file.value" : {
			"plugValueWidget:type" : "GafferUI.FileSystemPathPlugValueWidget",
			"path:bookmarks" : "iesProfile",
			"path:leaf" : True,
			"path:value" : True,
			"fileSystemPath:extensions" : "ies",
		},

	}
)

class _ParameterFilter( GafferUI.Widget ) :

	def __init__( self, plug, **kw ) :

		self.__listContainer = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.Widget.__init__( self, self.__listContainer, **kw )

		self.__parametersPlug = plug

		self.__customFilterActive = Gaffer.Metadata.value( self.__parametersPlug, "layout:filterEnabled" ) or False

		visible = Gaffer.Metadata.value( self.__parametersPlug, "layout:visibleRenderers" )
		self.__rendererVisibility = {}

		visited = set()

		for rendererTarget in Gaffer.Metadata.targetsWithMetadata( "renderer:*", "optionPrefix" ) :
			renderer = rendererTarget[9:]  # Trim of "renderer:"
			# \todo Once we standardize on `arnold:` prefix instead of `ai:`, we can remove this special case.
			prefix = "arnold:" if renderer == "Arnold" else Gaffer.Metadata.value( rendererTarget, "optionPrefix" )
			if (
				any( i.getName().startswith( prefix ) for i in Gaffer.Plug.Range( self.__parametersPlug ) ) and
				prefix not in visited
			) :
				visited.add( prefix )
				self.__rendererVisibility[renderer] = (
					renderer in visible if visible is not None else (
						Gaffer.Metadata.value( rendererTarget, "ui:enabled" ) is not False
					)
				)

		with self.__listContainer :

			# `ui:enabled` may be `False` but the renderer may still be registered with Gaffer and have
			# plugs on the light. For example, Cycles has the `GAFFERCYCLES_HIDE_UI` environment variable.
			# We need to hide the plugs in that case (taken care of by `__visibleRenderers` initial value above)
			# and also not show a toggle button for it to honor the `ui:enabled` state.
			renderersWithIcons = [ i for i in self.__rendererVisibility.keys() if Gaffer.Metadata.value( "renderer:" + i, "ui:enabled" ) is not False ]
			# Indent the filter UI so `customFilterValue` lines up with the plug widgets below.
			# The `20` pixel spacing consists of 16 for the icon and 4 for the spacing between widgets.
			# The vertical space prevents a slight resizing of the UI below when toggling the filter Text.
			leftIndent = GafferUI.PlugWidget.labelWidth() - ( ( len( renderersWithIcons ) + 1 ) * 20 )
			GafferUI.Spacer( imath.V2i( leftIndent, 18 ), maximumSize = imath.V2i( leftIndent, 18 ) )

			self.__rendererIcons = {}
			for r in renderersWithIcons :
				self.__rendererIcons[r] = GafferUI.Button( "", hasFrame = False, toolTip = "Include {} parameters".format( r ) )
				self.__rendererIcons[r].clickedSignal().connect( functools.partial( Gaffer.WeakMethod( self.__rendererIconClicked ), r ) )

			self.__customFilterButton = GafferUI.Button( "", "search.png", hasFrame = False )
			self.__customFilterButton.setToolTip( "Toggles filtering of the visible plugs by the filter text.")
			self.__customFilterButton.clickedSignal().connect( Gaffer.WeakMethod( self.__customFilterButtonClicked ) )

			customFilterValue = Gaffer.Metadata.value( self.__parametersPlug, "layout:filter" ) or "*"
			self.__customFilterText = GafferUI.TextWidget( customFilterValue, placeholderText = "Filter..." )
			self.__customFilterText.textChangedSignal().connect( Gaffer.WeakMethod( self.__customFilterTextChanged )  )
			self.__customFilterText.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__customFilterEditingFinished ) )

		self.parentChangedSignal().connect( Gaffer.WeakMethod( self.__parentChanged ) )

	def __parentChanged( self, widget ) :

		self.__updateFilter()
		self.__updateWidgets()

	def __plugFilter( self, customFilter, rendererPrefixes, plug ) :

		label = Gaffer.Metadata.value( plug, "label" ).lower()
		if not IECore.StringAlgo.matchMultiple( label, customFilter.lower() ) :
			return False

		prefix = plug.getName().partition( ":" )[0] + ":"
		return rendererPrefixes.get( prefix, True )

	def __plugLayout( self ) :

		return self.ancestor( GafferUI.PlugLayout )

	def __updateFilter( self ) :

		assert( self.__plugLayout is not None )

		if self.__customFilterActive :
			customFilterValue = self.__customFilterText.getText().lower()
			customFilterValue = customFilterValue if IECore.StringAlgo.hasWildcards( customFilterValue ) else ( "*" + customFilterValue + "*" )
		else :
			customFilterValue = "*"

		# \todo Once we standardize on `arnold:` prefix instead of `ai:`, we can remove this special case.
		prefixes = { ( "arnold:" if k == "Arnold" else Gaffer.Metadata.value( "renderer:" + k, "optionPrefix" ) ) : v for k, v in self.__rendererVisibility.items() }
		self.__plugLayout().setFilter( functools.partial( Gaffer.WeakMethod( self.__plugFilter ), customFilterValue, prefixes ) )

	def __customFilterButtonClicked( self, button ) :

		self.__customFilterActive = not self.__customFilterActive
		Gaffer.Metadata.registerValue( self.__parametersPlug, "layout:filterEnabled", self.__customFilterActive, persistent = False )

		if self.__customFilterActive :
			self.__customFilterText.setSelection( 0, None )  # All
			self.__customFilterText.grabFocus()

		self.__updateFilter()
		self.__updateWidgets()

	def __customFilterTextChanged( self, textWidget ) :

		self.__updateFilter()

	def __customFilterEditingFinished( self, textWidget ) :

		Gaffer.Metadata.registerValue( self.__parametersPlug, "layout:filter", textWidget.getText(), persistent = False )

	def __updateWidgets( self ) :

		self.__customFilterButton.setImage( "searchOn.png" if self.__customFilterActive else "search.png" )
		self.__customFilterText.setVisible( self.__customFilterActive )

		for renderer, button in self.__rendererIcons.items() :
			button.setImage( "renderer" + renderer + ( "On" if self.__rendererVisibility[renderer] else "Off" ) + "Icon.png" )

	def __rendererIconClicked( self, renderer, widget ) :

		self.__rendererVisibility[renderer] = not self.__rendererVisibility[renderer]

		Gaffer.Metadata.registerValue( self.__parametersPlug, "layout:visibleRenderers", IECore.StringVectorData( k for k, v in self.__rendererVisibility.items() if v ), persistent = False )

		self.__updateFilter()
		self.__updateWidgets()