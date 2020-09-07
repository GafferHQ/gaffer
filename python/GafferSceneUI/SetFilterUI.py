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

import Gaffer
import GafferUI
import GafferScene

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.SetFilter,

	"description",
	"""
	A filter which uses sets to define which locations are matched.
	""",

	plugs = {

		"setExpression" : [

			"description",
			"""
			A set expression that computes a set that defines
			the locations to be matched.

			For example, the expression `mySpheresSet | myCubesSet`
			will create a set that contains all objects in
			`mySpheresSet` and `myCubesSet`.

			Gaffer supports the union operator (`|`) as shown in the
			example and also provides intersection (`&`) and difference (`-`)
			operations for set expressions. Names of locations
			can be used to represent a set that contains only
			that one location.

			In addition, the `in` and `containing` operators can be
			used to query descendant and ancestor matches. For example,
			`materialA in assetB` will select all locations in the `materialA`
			set that are at or below locations in the `assetB` set. This
			allows leaf matches to be made against sets that only contain
			root or parent locations. `allAssets containing glass` will
			selection locations in `allAssets` that have children in the
			`glass` set.

			For more examples please consult the Scripting Reference
			section in Gaffer's documentation.

			The context menu of the set expression text field provides
			entries that help construct set expressions.
			""",

			"ui:scene:acceptsSetExpression", True,
			"nodule:type", "",

		],

	}

)
