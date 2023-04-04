##########################################################################
#
#  Copyright (c) 2017, Lucien Fostier. All rights reserved.
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

import IECore

import Gaffer
import GafferUI
import GafferImage

import PyOpenColorIO

def __colorSpaceMenuHelper( plug ) :

	config = PyOpenColorIO.GetCurrentConfig()
	parameters = PyOpenColorIO.ColorSpaceMenuParameters( config )

	categories = Gaffer.Metadata.value( plug, "openColorIO:categories" )
	if categories is not None :
		parameters.setAppCategories( categories )

	includeRoles = Gaffer.Metadata.value( plug, "openColorIO:includeRoles" )
	if includeRoles is not None :
		parameters.setIncludeRoles( includeRoles )

	return PyOpenColorIO.ColorSpaceMenuHelper( parameters )

def colorSpacePresetNames( plug, noneLabel = "None" ) :

	helper = __colorSpaceMenuHelper( plug )
	return IECore.StringVectorData(
		[ noneLabel ] + [
			"/".join(
				list( helper.getHierarchyLevels( i ) ) +
				[ helper.getUIName( i ) ]
			)
			for i in range( 0, helper.getNumColorSpaces() )
		]
	)

def colorSpacePresetValues( plug ) :

	helper = __colorSpaceMenuHelper( plug )
	return IECore.StringVectorData(
		[ "" ] +
		[ helper.getName( i ) for i in range( 0, helper.getNumColorSpaces() ) ]
	)

Gaffer.Metadata.registerNode(

	GafferImage.OpenColorIOTransform,

	"description",
	"""
	Applies color transformations provided by
	OpenColorIO.
	""",

	plugs = {

		"context" : [

			"description",
			"""
			Context override for OCIO config.
			""",

			# We don't use the default CompoundDataPlugValueWidget because
			# it allows the addition of all sorts of member plugs, and we
			# only want to add strings. Instead we use the _ContextFooter
			# to provide a button for only adding strings.
			## \todo Perhaps we should invent some metadata scheme to give
			# this behaviour to the CompoundDataPlugValueWidget?
			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:customWidget:addButton:widgetType", "GafferImageUI.OpenColorIOTransformUI._ContextFooter",
			"layout:customWidget:addButton:index", -1,

			"layout:section", "Context",
			"layout:index", -3,

		],

	}

)

class _ContextFooter( GafferUI.Widget ) :

	def __init__( self, plug, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
		GafferUI.Widget.__init__( self, row, **kw )

		with row :

			GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

			button = GafferUI.Button(
				image = "plus.png",
				hasFrame = False,
				toolTip = "Click to add variables",
			)

			button.clickedSignal().connect( Gaffer.WeakMethod( self.__clicked ), scoped = False )

			GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

		self.__plug = plug

	def __clicked( self, button ) :

		if Gaffer.MetadataAlgo.readOnly( self.__plug ) :
			return

		with Gaffer.UndoScope( self.__plug.ancestor( Gaffer.ScriptNode ) ) :
			self.__plug.addChild( Gaffer.NameValuePlug( "", "", True, "member1", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
