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

def __colorSpaceMenuHelper( plug, config = None ) :

	config = GafferImage.OpenColorIOAlgo.currentConfig() if config is None else config
	parameters = PyOpenColorIO.ColorSpaceMenuParameters( config )

	categories = Gaffer.Metadata.value( plug, "openColorIO:categories" )
	if categories is not None :
		parameters.setAppCategories( categories )

	includeRoles = Gaffer.Metadata.value( plug, "openColorIO:includeRoles" )
	if includeRoles is not None :
		parameters.setIncludeRoles( includeRoles )

	return PyOpenColorIO.ColorSpaceMenuHelper( parameters )

def colorSpacePresetNames( plug, config = None ) :

	helper = __colorSpaceMenuHelper( plug, config )

	names = IECore.StringVectorData( [
		"/".join(
			list( helper.getHierarchyLevels( i ) ) +
			[ helper.getUIName( i ) ]
		)
		for i in range( 0, helper.getNumColorSpaces() )
	] )

	extraNames = Gaffer.Metadata.value( plug, "openColorIO:extraPresetNames" )
	if extraNames is not None :
		names[0:0] = extraNames

	return names

def colorSpacePresetValues( plug, config = None ) :

	helper = __colorSpaceMenuHelper( plug, config )

	values = IECore.StringVectorData( [
		helper.getName( i ) for i in range( 0, helper.getNumColorSpaces() )
	] )

	extraValues = Gaffer.Metadata.value( plug, "openColorIO:extraPresetValues" )
	if extraValues is not None :
		values[0:0] = extraValues

	return values

Gaffer.Metadata.registerNode(

	GafferImage.OpenColorIOTransform,

	"description",
	"""
	Applies color transformations provided by
	OpenColorIO.
	""",

	plugs = {

		"context" : {

			"description" :
			"""
			> Warning : Deprecated - please use the `OpenColorIOContext`
			> node instead.
			""",

			"plugValueWidget:type" : "GafferUI.LayoutPlugValueWidget",
			"layout:customWidget:addButton:widgetType" : "GafferUI.PlugCreationWidget",
			"layout:customWidget:addButton:index" : -1,
			"plugCreationWidget:includedTypes" : "Gaffer.StringPlug",

			"layout:section" : "Context",
			"layout:index" : -3,
			# Only show plug if it has been used previously, to discourage new
			# use (since the plug is deprecated).
			"layout:visibilityActivator" : lambda plug : bool( len( plug ) ),

		},

	}

)
