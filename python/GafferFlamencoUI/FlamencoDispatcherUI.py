##########################################################################
#
#  Copyright (c) 2025, John Haddon. All rights reserved.
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

import pathlib
import shutil
import sys

import imath

import Gaffer
import GafferUI
import GafferFlamenco

from GafferUI._StyleSheet import _styleColors

from Qt import QtGui

Gaffer.Metadata.registerNode(

	GafferFlamenco.FlamencoDispatcher,

	"description",
	"""
	Dispatches tasks to be run by the [Flamenco](https://flamenco.blender.org) render farm
	manager.
	""",

	plugs = {

		"managerURL" : {

			"description" :
			"""
			The URL used to connect to the Flamenco manager. If not specified, the
			manager will be discovered automatically.

			> Tip : The Flamenco manager displays its own URL when it is first started.
			""",

			"plugValueWidget:type" : "GafferFlamencoUI.FlamencoDispatcherUI._ManagerURLPlugValueWidget",
			"stringPlugValueWidget:placeholderText" : "Auto",

		},

		"priority" : {

			"description" :
			"""
			The priority of the job relative to other jobs.
			""",

		},

		"workerTag" : {

			"description" :
			"""
			Limits the job to workers with a matching tag. This allows jobs to
			be directed to subsets of the render farm.
			""",

		},

		"startPaused" : {

			"description" :
			"""
			Submits the job in a paused state, so that it doesn't
			pick up workers until it is unpaused via the
			Flamenco dashboard.
			""",

		},

	}

)

class _ManagerURLPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		column = GafferUI.ListContainer( spacing = 4 )
		GafferUI.PlugValueWidget.__init__( self, column, plugs )

		with column :

			GafferUI.StringPlugValueWidget( plugs )

			with GafferUI.Frame( borderWidth = 4, borderStyle = GafferUI.Frame.BorderStyle.None_, ) as frame :

				## \todo Add public "role" property to Frame widget and use that to determine styling.
				frame._qtWidget().setProperty( "gafferDiff", "Other" )

				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

					self.__statusIcon = GafferUI.Image( "infoSmall.png" )
					self.__statusLabel = GafferUI.Label( "Checking..." )
					self.__statusLabel.linkActivatedSignal().connect( Gaffer.WeakMethod( self.__installJobType ) )

					GafferUI.Spacer( imath.V2i( 1 ) )

					refreshButton = GafferUI.Button( hasFrame = False, image = "refresh.png" )
					refreshButton.clickedSignal().connect( Gaffer.WeakMethod( self.__refreshClicked ) )

		self.__currentURL = None

	def _updateFromValues( self, values, exception ) :

		if not values or values[0] == self.__currentURL :
			return

		self.__currentURL = values[0]
		self.__updateStatusInBackground( self.__currentURL )

	def __refreshClicked( self, button ) :

		self.__currentURL = None
		self._requestUpdateFromValues()

	@GafferUI.BackgroundMethod()
	def __updateStatusInBackground( self, managerURL ) :

		return GafferFlamenco.FlamencoDispatcher.managerStatus( managerURL )

	@__updateStatusInBackground.plug
	def __updateStatusInBackgroundPlug( self ) :

		# We don't depend on any graph state, so don't need
		# to be cancelled before the graph is edited.
		return None

	@__updateStatusInBackground.preCall
	def __updateStatusInBackgroundPreCall( self ) :

		self.__updateIconAndLabel( "infoSmall.png", "Checking..." )

	@__updateStatusInBackground.postCall
	def __updateStatusInBackgroundPostCall( self, status ) :

		match status :
			case GafferFlamenco.FlamencoDispatcher.ManagerStatus.NotFound :
				self.__updateIconAndLabel( "warningSmall.png", "Manager not found" )
			case GafferFlamenco.FlamencoDispatcher.ManagerStatus.JobTypeMissing :
				if not self.__haveInstalledJobType :
					self.__updateIconAndLabel(
						"warningSmall.png",
						"Gaffer job type missing. <a href=install>Install now</a>"
					)
				else :
					# Flamenco doesn't notice a newly-installed job type if the
					# `scripts` directory didn't exist when it was first
					# started.
					## \todo Get Flamenco to recheck the scripts directory so we
					# can remove this friction.
					self.__updateIconAndLabel(
						"warningSmall.png",
						"Manager restart required</a>"
					)
			case GafferFlamenco.FlamencoDispatcher.ManagerStatus.OK :
				self.__updateIconAndLabel( "infoSmall.png", status.url )

	def __updateIconAndLabel( self, icon, label ) :

		textColor = QtGui.QColor( *_styleColors["foregroundFaded"] ).name()
		linkColor = QtGui.QColor( *_styleColors["foregroundInfo"] ).name()
		label = f"<html><header><style type=text/css> * {{ color:{textColor} }} a {{ color:{linkColor}}}></style></head><body>{label}</body></html>"

		self.__statusIcon.updateImage( icon )
		self.__statusLabel.setText( label )

	__haveInstalledJobType = False
	def __installJobType( self, *unused ) :

		filter = Gaffer.MatchPatternPathFilter(
			patterns = [ "flamenco-manager{}".format( ".exe" if sys.platform == "win32" else "" ) ],
		)
		filter.userData()["UI"] = { "visible" : False }

		dialogue = GafferUI.PathChooserDialogue(
			Gaffer.FileSystemPath( pathlib.Path.cwd(), filter ),
			title = "Locate Flamenco Manager",
			cancelLabel = "Cancel", confirmLabel = "Install",
			allowMultipleSelection = False, valid = True, leaf = True
		)
		flamencoManager = dialogue.waitForPath( parentWindow = self.ancestor( GafferUI.Window ) )
		if not flamencoManager :
			return

		scriptsDir = pathlib.Path( flamencoManager ).parent / "scripts"
		scriptsDir.mkdir( exist_ok = True )
		shutil.copy( Gaffer.rootPath() / "python" / "GafferFlamenco" / "gaffer.js", scriptsDir )

		_ManagerURLPlugValueWidget.__haveInstalledJobType = True
		self.__currentURL = None
		self._requestUpdateFromValues()
