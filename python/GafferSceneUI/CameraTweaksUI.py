##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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
import six
import imath

import IECore

import Gaffer
import GafferUI
import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.CameraTweaks,

	"description",
	"""
	Applies modifications, also known as "tweaks" to camera
	parameters or render options in the scene. Supports any number
	of tweaks, and custom camera parameters. Tweaks to camera
	parameters apply to every camera specified by the filter.

	Tweaks apply to every camera specified by the filter.

	Can add new camera parameters or render options.

	Any existing parameters/options can be replaced or removed.
	Numeric parameters/options can also be added to, subtracted
	from, or multiplied.

	Tweaks are applied in order, so if there is more than one tweak
	to the same parameter/option, the first tweak will be applied
	first, then the second, etc.
	""",

	plugs = {

		"tweaks" : [

			"description",
			"""
			Add a camera tweak.

			Arbitrary numbers of user defined tweaks may be
			added as children of this plug via the user
			interface, or via the CameraTweaks API in Python.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:customWidget:footer:widgetType", "GafferSceneUI.CameraTweaksUI._TweaksFooter",
			"layout:customWidget:footer:index", -1,

		],

		"tweaks.*" : [

			"tweakPlugValueWidget:allowRemove", True,

		],

	}

)

_parameterCategoriesAndDefaults = []

def __registerTweakMetadata( tweakName, childName, metadataName, value ) :

	Gaffer.Metadata.registerValue( GafferScene.CameraTweaks.staticTypeId(), "tweaks.{}.{}".format( tweakName, childName ), metadataName, value )
	# In case the same tweak is added twice, we register again for the same tweak with a numeric suffix.
	Gaffer.Metadata.registerValue( GafferScene.CameraTweaks.staticTypeId(), "tweaks.{}[0-9].{}".format( tweakName, childName ), metadataName, value )

def __populateMetadata():
	global _parameterCategoriesAndDefaults

	# Create a temporary camera object just to read the default parameter values off of it,
	# and access the metadata
	tempCam = GafferScene.Camera()

	parameterCategories = [ ("Camera Parameters", i ) for i in ["projection","fieldOfView","apertureAspectRatio",
			"aperture","focalLength","apertureOffset","fStop","focalLengthWorldScale","focusDistance",
			"clippingPlanes" ] ] + [
			("Render Overrides", i ) for i in [ "filmFit", "shutter", "resolution", "pixelAspectRatio",
			"resolutionMultiplier", "overscan", "overscanLeft", "overscanRight", "overscanTop",
			"overscanBottom", "cropWindow", "depthOfField" ] ]

	for category, plugName in parameterCategories:
		if category == "Render Overrides":
			cameraPlug = tempCam["renderSettingOverrides"][plugName]["value"]
		else:
			cameraPlug = tempCam[plugName]

		data = Gaffer.PlugAlgo.extractDataFromPlug( cameraPlug )

		_parameterCategoriesAndDefaults.append( ( category, plugName, data ) )

		__registerTweakMetadata( plugName, "name", "readOnly", True )

		for metaName in Gaffer.Metadata.registeredValues( cameraPlug ):
			metaValue = Gaffer.Metadata.value( cameraPlug, metaName )
			if metaName != "layout:section" and metaValue is not None :
				__registerTweakMetadata( plugName, "value", metaName, metaValue )

		# The Camera node only offers a choice between "perspective" and "orthographic", since
		# they are the two that make sense in the UI.  But if you're putting down a special
		# tweak node, you might want to use a non-standard camera supported by your specific
		# renderer backend ( eg. spherical_camera in Arnold )
		if plugName == "projection":
			__registerTweakMetadata( plugName, "value", "presetsPlugValueWidget:allowCustom", True )

__populateMetadata()

class _TweaksFooter( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug )

		with row :

				GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

				GafferUI.MenuButton(
					image = "plus.png",
					hasFrame = False,
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
				)

				GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

	def _updateFromPlug( self ) :

		self.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()

		for category, name, defaultData in _parameterCategoriesAndDefaults:

			result.append(
				"/" + category + "/" + name,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__addTweak ), name, defaultData )
				}
			)

		# TODO - would be nice to share these default options with other users of TweakPlug
		for item in [
			Gaffer.BoolPlug,
			Gaffer.FloatPlug,
			Gaffer.IntPlug,
			"NumericDivider",
			Gaffer.StringPlug,
			"StringDivider",
			Gaffer.V2iPlug,
			Gaffer.V3iPlug,
			Gaffer.V2fPlug,
			Gaffer.V3fPlug,
			"VectorDivider",
			Gaffer.Color3fPlug,
			Gaffer.Color4fPlug
		] :

			if isinstance( item, six.string_types ) :
				result.append( "/Custom Parameter/" + item, { "divider" : True } )
			else :
				result.append(
					"/Custom Parameter/" + item.__name__.replace( "Plug", "" ),
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__addTweak ), "", item ),
					}
				)

		return result

	def __addTweak( self, name, plugTypeOrValue ) :

		if isinstance( plugTypeOrValue, IECore.Data ) :
			plug = GafferScene.TweakPlug( name, plugTypeOrValue )
		else :
			plug = GafferScene.TweakPlug( name, plugTypeOrValue() )

		plug.setName( name or "tweak1" )

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().addChild( plug )

