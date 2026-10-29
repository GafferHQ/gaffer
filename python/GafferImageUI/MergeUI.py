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
import GafferImage

def __inputLabel( plug ) :

	s = int( plug.getName().replace( "in", "" ) )
	if s == 0 :
		return "B"
	elif s == 1 :
		return "A"
	else :
		return "A{}".format( s )

def __inputDescription( plug ) :

	return "The {} input.".format( __inputLabel( plug ) )

Gaffer.Metadata.registerNode(

	GafferImage.Merge,

	"description",
	"""
	Composites two or more images together. The following operations
	are available :

	  - Add : A + B
	  - Atop : Ab + B(1-a)
	  - Divide : A / B
	  - In : Ab
	  - Out : A(1-b)
	  - Mask : Ba
	  - Matte : Aa + B(1.-a)
	  - Multiply : AB
	  - Over : A + B(1-a)
	  - Subtract : A - B
	  - Difference : fabs( A - B )
	  - Under : A(1-b) + B
	  - Min : min( A, B )
	  - Max : max( A, B )
	""",

	"layout:activator:modeCollect", lambda node : node["mode"].getValue() == GafferImage.Merge.Mode.Collect,
	"ui:spreadsheet:enabledRowNamesConnection", "contextValues",
	"ui:spreadsheet:selectorContextVariablePlug", "contextVariable",

	plugs = {

		"in.*" : {

			"description" : __inputDescription,
			"noduleLayout:label" : __inputLabel,

		},

		"operation" : {

			"description" :
			"""
			The compositing operation used to merge the
			image together. See node documentation for
			more details.
			""",

			"preset:Add" : GafferImage.Merge.Operation.Add,
			"preset:Atop" : GafferImage.Merge.Operation.Atop,
			"preset:Divide" : GafferImage.Merge.Operation.Divide,
			"preset:In" : GafferImage.Merge.Operation.In,
			"preset:Out" : GafferImage.Merge.Operation.Out,
			"preset:Mask" : GafferImage.Merge.Operation.Mask,
			"preset:Matte" : GafferImage.Merge.Operation.Matte,
			"preset:Multiply" : GafferImage.Merge.Operation.Multiply,
			"preset:Over" : GafferImage.Merge.Operation.Over,
			"preset:Subtract" : GafferImage.Merge.Operation.Subtract,
			"preset:Difference" : GafferImage.Merge.Operation.Difference,
			"preset:Under" : GafferImage.Merge.Operation.Under,
			"preset:Min" : GafferImage.Merge.Operation.Min,
			"preset:Max" : GafferImage.Merge.Operation.Max,

			"userDefault" : GafferImage.Merge.Operation.Over,

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

		},

		"mode" : {

			"description" :
			"""
			Defines how inputs are selected for merging :

			- Standard : Each input plug is used once.
			- Collect : Each input plug is evaluated for each value in `contextValues`.
			""",

			"preset:Standard" : GafferImage.Merge.Mode.Standard,
			"preset:Collect" : GafferImage.Merge.Mode.Collect,

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		},

		"contextValues" : {

			"description" :
			"""
			The values to use for the `contextVariable` when in `Collect` mode. Each input will be evaluated for
			each value, forming multiple layers in the merge. This value will be passed to `contextVariable`, and
			the length of this list determines the number of times each input is evaluated.
			""",

			"layout:visibilityActivator" : "modeCollect",
		},

		"contextVariable" : {

			"description" :
			"""
			Name of the context variable that takes values from `contextValues` in Collect mode. May be used
			upstream to vary the multiple layers being taken from each input.
			""",

			"layout:visibilityActivator" : "modeCollect",

		},

		"indexContextVariable" : {

			"description" :
			"""
			Name of the context variable that contains the index of the current context value when in Collect
			mode. Ranges from 0 to `len( contextValues ) - 1`. May be used upstream to vary the multiple
			layers being taken from each input.
			""",

			"layout:visibilityActivator" : "modeCollect",

		},

	}

)
