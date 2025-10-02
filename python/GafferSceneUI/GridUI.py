##########################################################################
#
#  Copyright (c) 2014, John Haddon. All rights reserved.
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
import GafferScene
import GafferUI

Gaffer.Metadata.registerNode(

	GafferScene.Grid,

	"description",
	""""
	A grid. This is used to draw the grid in the viewer,
	but is also included as a node in case it might be
	useful, perhaps for placing a grid in renders done
	using the OpenGLRender node.
	""",

	plugs = {

		"name" : {

			"description" :
			"""
			The name of the grid.
			""",

		},

		"transform" : {

			"description" :
			"""
			The transform applied to the grid.
			""",

			"layout:section" : "Transform",

		},

		"dimensions" : {

			"description" :
			"""
			The size of the grid in the x and y
			axes. Use the transform to rotate the
			grid into a different plane.
			""",

		},

		"spacing" : {

			"description" :
			"""
			The size of the space between adjacent lines
			in the grid.
			"""

		},

		"gridColor" : {

			"description" :
			"""
			The colour of the lines forming the main part
			of the grid.
			"""

		},

		"centerColor" : {

			"description" :
			"""
			The colour of the two lines forming the central
			cross of the grid.
			"""

		},

		"borderColor" : {

			"description" :
			"""
			The colour of the lines forming the border
			of the grid.
			"""

		},

		"gridPixelWidth" : {

			"description" :
			"""
			The width of the lines forming the main part
			of the grid. This width applies only to the
			OpenGL representation of the grid.
			"""

		},


		"centerPixelWidth" : {

			"description" :
			"""
			The width of the two lines forming the central
			cross of the grid. This width applies only to the
			OpenGL representation of the grid.
			"""

		},

		"borderPixelWidth" : {

			"description" :
			"""
			The width of the lines forming the border
			of the grid. This width applies only to the
			OpenGL representation of the grid.
			"""

		},

	}

)
