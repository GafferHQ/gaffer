##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUI

import GafferScene

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.PathFilter,

	"description",
	"""
	Chooses locations by matching them against a list of
	paths.
	""",

	plugs = {

		"paths" : [

			"description",
			"""
			The list of paths to the locations to be matched by the filter.
			A path is formed by a sequence of names separated by '/', and
			specifies the hierarchical position of a location within the scene.
			Paths may use Gaffer's standard wildcard characters to match
			multiple locations.

			The '*' wildcard matches any sequence of characters within
			an individual name, but never matches across names separated
			by a '/'.

			 - /robot/*Arm matches /robot/leftArm, /robot/rightArm and
			   /robot/Arm. But does not match /robot/limbs/leftArm or
			   /robot/arm.

			The "..." wildcard matches any sequence of names, and can be
			used to match locations no matter where they are parented in
			the hierarchy.

			 - /.../house matches /house, /street/house and /city/street/house.
			""",

		],

	}

)

##########################################################################
# Widgets and nodules
##########################################################################

def __pathsPlugWidgetCreator( plug ) :

	result = GafferUI.VectorDataPlugValueWidget( plug )
	result.vectorDataWidget().setDragPointer( "objects" )
	return result

GafferUI.PlugValueWidget.registerCreator(
	GafferScene.PathFilter,
	"paths",
	__pathsPlugWidgetCreator,
)

GafferUI.Nodule.registerNodule(
	GafferScene.PathFilter,
	"paths",
	lambda plug : None,
)
