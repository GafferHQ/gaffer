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

	GafferSceneUI.ImageSelectionTool,

	"description",
	"""
	""",

	"viewer:shortCut", "Q",
	"order", 1,
	"viewer:shouldAutoActivate", False,

	"nodeToolbar:bottom:type", "GafferUI.StandardNodeToolbar.bottom",

	"toolbarLayout:customWidget:SelectionWidget:widgetType", "GafferSceneUI.ImageSelectionToolUI._StatusWidget",
	"toolbarLayout:customWidget:SelectionWidget:section", "Bottom",

	# So our widget doesn't center, add a stretchy spacer to the right
	"toolbarLayout:customWidget:RightSpacer:widgetType", "GafferSceneUI.ImageSelectionToolUI._RightSpacer",
	"toolbarLayout:customWidget:RightSpacer:section", "Bottom",
	"toolbarLayout:customWidget:RightSpacer:index", -1,

	plugs = {

		"active" : [

			"boolPlugValueWidget:image", "gafferSceneUISelectionTool.png"

		],

	}

)

class _RightSpacer( GafferUI.Spacer ) :

	def __init__( self, imageView, **kw ) :

		GafferUI.Spacer.__init__( self, size = imath.V2i( 0, 0 ) )

class _StatusWidget( GafferUI.ListContainer ) :

	def __init__( self, tool, **kw ) :

		GafferUI.ListContainer.__init__( self, **kw )

		self.__tool = tool

		with self :
			with GafferUI.Frame( borderWidth = 4 ) as self.__frame:
				with GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal ) :

					self.__infoIcon = GafferUI.Image( "infoSmall.png" )
					self.__errorIcon = GafferUI.Image( "errorSmall.png" )
					self.__warningIcon = GafferUI.Image( "warningSmall.png" )
					GafferUI.Spacer( size = imath.V2i( 4 ), maximumSize = imath.V2i( 4 ) )
					self.__label = GafferUI.Label( "" )
					self.__label.setTextSelectable( True )

		self.__frame._qtWidget().setObjectName( "gafferImageSelectionStatus" )

		self.__tool.statusChangedSignal().connect( Gaffer.WeakMethod( self.__update, fallbackResult = None ) )

		self.__update()

	def scriptNode( self ) : # For LazyMethod's `deferUntilPlaybackStops`

		return self.__tool.ancestor( GafferUI.View ).scriptNode()

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __update( self, *unused ) :
		if not self.__tool["active"].getValue() :
			# We're about to be made invisible so all our update
			# would do is cause unnecessary flickering in Qt's
			# redraw.
			return

		status = self.__tool.status()
		self.__frame.setVisible( bool(status) )

		state, _, message = status.partition( ":" )

		self.__label.setText( message )

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
