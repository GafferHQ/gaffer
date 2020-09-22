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

import imath

import Gaffer
import GafferUI
import GafferSceneUI

Gaffer.Metadata.registerNode(

	GafferSceneUI.CropWindowTool,

	"description",
	"""
	Tool for adjusting crop window for rendering. The crop window is displayed as a
	masked area which can be adjusted using drag and drop.

	Note that the view must be locked to a render camera for this tool to be used.
	Additionally, an upstream node much be capable of setting the crop window so
	that there is something to adjust - typically this will be a StandardOptions
	node. The name of the plug being manipulated is displayed underneath the
	cropped area - it can be used to verify that the expected node is being adjusted.
	""",

	"viewer:shortCut", "C",
	"viewer:shouldAutoActivate", False,

	"nodeToolbar:bottom:type", "GafferUI.StandardNodeToolbar.bottom",

	"toolbarLayout:customWidget:SelectionWidget:widgetType", "GafferSceneUI.CropWindowToolUI._StatusWidget",
	"toolbarLayout:customWidget:SelectionWidget:section", "Bottom",

	# So our widget doesn't center, add a stretchy spacer to the right
	"toolbarLayout:customWidget:RightSpacer:widgetType", "GafferSceneUI.CropWindowToolUI._RightSpacer",
	"toolbarLayout:customWidget:RightSpacer:section", "Bottom",
	"toolbarLayout:customWidget:RightSpacer:index", -1,

)

class _RightSpacer( GafferUI.Spacer ) :

	def __init__( self, imageView, **kw ) :

		GafferUI.Spacer.__init__( self, size = imath.V2i( 0, 0 ) )

class _StatusWidget( GafferUI.Frame ) :

	def __init__( self, tool, **kw ) :

		GafferUI.Frame.__init__( self, borderWidth = 4, **kw )

		self.__tool = tool

		with self :
			with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal ) as self.__row :

				self.__infoIcon = GafferUI.Image( "infoSmall.png" )
				self.__errorIcon = GafferUI.Image( "errorSmall.png" )
				self.__warningIcon = GafferUI.Image( "warningSmall.png" )
				GafferUI.Spacer( size = imath.V2i( 4 ), maximumSize = imath.V2i( 4 ) )
				self.__label = GafferUI.Label( "" )

				GafferUI.Spacer( size = imath.V2i( 8 ), maximumSize = imath.V2i( 8 ) )
				GafferUI.Divider( orientation = GafferUI.Divider.Orientation.Vertical )
				GafferUI.Spacer( size = imath.V2i( 8 ), maximumSize = imath.V2i( 8 ) )

				with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal ) as self.__controls :

					self.__enabledLabel = GafferUI.Label( "Enabled" )
					self.__enabled = GafferUI.BoolPlugValueWidget( None )
					self.__enabled.boolWidget().setDisplayMode( GafferUI.BoolWidget.DisplayMode.Switch )

					button = GafferUI.Button( "Reset" )
					button._qtWidget().setFixedWidth( 50 )
					button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ), scoped = False )

		self.__tool.statusChangedSignal().connect( Gaffer.WeakMethod( self.__update, fallbackResult = None ), scoped = False )

		self.__update()

	def context( self ) :

		return self.ancestor( GafferUI.NodeToolbar ).getContext()

	def getToolTip( self ) :

		toolTip = GafferUI.Frame.getToolTip( self )
		if toolTip :
			return toolTip

		return self.__tool.status()

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __update( self, *unused ) :

		if not self.__tool["active"].getValue() :
			# We're about to be made invisible so all our update
			# would do is cause unnecessary flickering in Qt's
			# redraw.
			return

		status = self.__tool.status()
		self.setVisible( bool(status) )

		state, _, message = status.partition( ":" )

		self.__label.setText( message.strip() )

		state = state.strip().lower()
		info = warn = error = False
		if state == "error" :
			error = True
		elif state == "warning" :
			warn = True
		else :
			info = True

		self.__infoIcon.setVisible( info )
		self.__warningIcon.setVisible( warn )
		self.__errorIcon.setVisible( error )

		plug = self.__tool.plug()
		enabledPlug = self.__tool.enabledPlug()

		self.__controls.setVisible( plug is not None )

		self.__enabled.setPlug( enabledPlug )
		self.__enabled.setVisible( enabledPlug is not None )
		self.__enabledLabel.setVisible( enabledPlug is not None )

	def __buttonClicked( self, *unused ) :

		plug = self.__tool.plug()

		if plug is None :
			return

		with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
			plug["min"].setValue( imath.V2f( 0 ) )
			plug["max"].setValue( imath.V2f( 1 ) )
