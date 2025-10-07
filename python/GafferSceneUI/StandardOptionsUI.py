##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import IECore
import IECoreScene

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

from GafferUI.PlugValueWidget import sole

##########################################################################
# Metadata
##########################################################################

def __cameraSummary( plug ) :

	info = []
	if plug["render:camera"]["enabled"].getValue() :
		info.append( plug["render:camera"]["value"].getValue() )
	if plug["render:filmFit"]["enabled"].getValue() :
		info.append( "Fit Mode %s" %
			IECoreScene.Camera.FilmFit.values[ plug["render:filmFit"]["value"].getValue() ].name
		)
	if plug["render:resolution"]["enabled"].getValue() :
		resolution = plug["render:resolution"]["value"].getValue()
		info.append( "%dx%d" % ( resolution[0], resolution[1] ) )
	if plug["render:pixelAspectRatio"]["enabled"].getValue() :
		pixelAspectRatio = plug["render:pixelAspectRatio"]["value"].getValue()
		info.append( "Aspect %s" % GafferUI.NumericWidget.valueToString( pixelAspectRatio ) )
	if plug["render:resolutionMultiplier"]["enabled"].getValue() :
		resolutionMultiplier = plug["render:resolutionMultiplier"]["value"].getValue()
		info.append( "Mult %s" % GafferUI.NumericWidget.valueToString( resolutionMultiplier ) )
	if plug["render:cropWindow"]["enabled"].getValue() :
		crop = plug["render:cropWindow"]["value"].getValue()
		info.append( "Crop %s,%s-%s,%s" % tuple( GafferUI.NumericWidget.valueToString( x ) for x in ( crop.min().x, crop.min().y, crop.max().x, crop.max().y ) ) )
	if plug["render:overscan"]["enabled"].getValue() :
		info.append( "Overscan %s" % ( "On" if plug["render:overscan"]["value"].getValue() else "Off" ) )
	if plug["render:depthOfField"]["enabled"].getValue() :
		info.append( "DOF " + ( "On" if plug["render:depthOfField"]["value"].getValue() else "Off" ) )

	return ", ".join( info )

def __rendererSummary( plug ) :

	if plug["render:defaultRenderer"]["enabled"].getValue() :
		return plug["render:defaultRenderer"]["value"].getValue()

	return ""

def __renderSetSummary( plug ) :

	info = []
	if plug["render:includedPurposes"]["enabled"].getValue() :
		purposes = plug["render:includedPurposes"]["value"].getValue()
		info.append( "Purposes {}".format( " / ".join( [ p.capitalize() for p in purposes ] ) if purposes else "None" ) )
	if plug["render:inclusions"]["enabled"].getValue() :
		info.append( "Inclusions {}".format( plug["render:inclusions"]["value"].getValue() ) )
	if plug["render:exclusions"]["enabled"].getValue() :
		info.append( "Exclusions {}".format( plug["render:exclusions"]["value"].getValue() ) )
	if plug["render:additionalLights"]["enabled"].getValue() :
		info.append( "Lights {}".format( plug["render:additionalLights"]["value"].getValue() ) )

	return ", ".join( info )

def __motionBlurSummary( plug ) :

	info = []
	if plug["render:transformBlur"]["enabled"].getValue() :
		info.append( "Transform " + ( "On" if plug["render:transformBlur"]["value"].getValue() else "Off" ) )
	if plug["render:deformationBlur"]["enabled"].getValue() :
		info.append( "Deformation " + ( "On" if plug["render:deformationBlur"]["value"].getValue() else "Off" ) )
	if plug["render:shutter"]["enabled"].getValue() :
		info.append( "Shutter " + str( plug["render:shutter"]["value"].getValue() ) )

	return ", ".join( info )

def __statisticsSummary( plug ) :

	info = []
	if plug["render:performanceMonitor"]["enabled"].getValue() :
		info.append( "Performance Monitor " + ( "On" if plug["render:performanceMonitor"]["value"].getValue() else "Off" ) )

	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferScene.StandardOptions,

	"description",
	"""
	Specifies the standard options (global settings) for the
	scene. These should be respected by all renderers.
	""",

	plugs = {

		# Section summaries

		"options" : {

			"layout:section:Camera:summary" : __cameraSummary,
			"layout:section:Renderer:summary" : __rendererSummary,
			"layout:section:Render Set:summary" : __renderSetSummary,
			"layout:section:Motion Blur:summary" : __motionBlurSummary,
			"layout:section:Statistics:summary" : __statisticsSummary,

		},

	}

)

class _IncludedPurposesPlugValueWidget( GafferUI.PlugValueWidget ) :

	__allPurposes = [ "default", "render", "proxy", "guide" ]

	def __init__( self, plugs, **kw ) :

		self.__menuButton = GafferUI.MenuButton( "", menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )
		GafferUI.PlugValueWidget.__init__( self, self.__menuButton, plugs, **kw )

		self._addPopupMenu( self.__menuButton )

		self.__currentValue = None

	def _updateFromValues( self, values, exception ) :

		self.__currentValue = sole( values )
		if self.__currentValue :
			self.__menuButton.setText( ", ".join( [ p.capitalize() for p in self.__currentValue ] ) )
		else :
			# A value of `None` means we have multiple different values (from different plugs),
			# and a value of `[]` means the user has disabled all purposes.
			self.__menuButton.setText( "---" if self.__currentValue is None else "None" )
		self.__menuButton.setErrored( exception is not None )

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		currentValue = self.__currentValue or []
		for purpose in self.__allPurposes :

			result.append(
				"/{}".format( purpose.capitalize() ),
				{
					"checkBox" : purpose in currentValue,
					"command" : functools.partial( Gaffer.WeakMethod( self.__togglePurpose ), purpose = purpose )
				}
			)


		return result

	def __togglePurpose( self, checked, purpose ) :

		with self.context() :
			with Gaffer.UndoScope( self.scriptNode() ) :
				for plug in self.getPlugs() :
					value = plug.getValue()
					# Conform value so that only valid purposes are present, and they are
					# always presented in the same order.
					value = [
						p for p in self.__allPurposes
						if
						( p != purpose and p in value ) or ( p == purpose and checked )
					]
					plug.setValue( IECore.StringVectorData( value ) )
