##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
#      * Neither the name of Image Engine Design Inc nor the names of
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

Gaffer.Metadata.registerNode(

	GafferScene.DeletePoints,

	"description",
	"""
	Deletes points from a points primitive using a primitive variable or id list to choose the points.
	""",

	plugs = {
		"selectionMode" : [
			"description",
			"""
			Chooses how to select points to delete.

			- VertexPrimitiveVariable : Deletes points with a non-zero value in the `points` primitive variable.
			- IdListPrimitiveVariable : Deletes points with Ids in the `idListVariable` primitive variable.
			- IdList : Deletes points with Ids in the `idList`.
			""",
			"preset:Vertex Primitive Variable", GafferScene.DeletePoints.SelectionMode.VertexPrimitiveVariable,
			"preset:Id List Primitive Variable", GafferScene.DeletePoints.SelectionMode.IdListPrimitiveVariable,
			"preset:Id List", GafferScene.DeletePoints.SelectionMode.IdList,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		],


		"adjustBounds" : [

			"userDefault", False,

		],

		"points" : [
			"description",
			"""
			Vertex interpolated int, float or bool primitive variable to choose which points to delete. Note a non-zero value indicates the point will be deleted. Only used when `selectionMode` is "VertexPrimitiveVariable".
			""",

			"layout:visibilityActivator", lambda plug : plug.node()["selectionMode"].getValue() == GafferScene.DeletePoints.SelectionMode.VertexPrimitiveVariable
		],

		"idListVariable" : [
			"description",
			"""
			The name of a constant primitive variable holding a list of ids to delete. Must be type IntVectorData or Int64VectorData. Only used when `selectionMode` is "IdListPrimitiveVariable".
			""",

			"layout:visibilityActivator", lambda plug : plug.node()["selectionMode"].getValue() == GafferScene.DeletePoints.SelectionMode.IdListPrimitiveVariable
		],

		"idList" : [
			"description",
			"""
			A list of ids to delete. Only used when `selectionMode` is "IdList".
			""",

			"layout:visibilityActivator", lambda plug : plug.node()["selectionMode"].getValue() == GafferScene.DeletePoints.SelectionMode.IdList
		],

		"id" : [
			"description",
			"""
			When using an id list to delete points, this primitive variable defines the id used for each point.
			If this primitive variable is not found, then the index of each point is its id.
			""",

			"layout:visibilityActivator", lambda plug : plug.node()["selectionMode"].getValue() in [ GafferScene.DeletePoints.SelectionMode.IdList, GafferScene.DeletePoints.SelectionMode.IdListPrimitiveVariable ]
		],


		"invert" : [
			"description",
			"""
			Invert the condition used to delete points. If the primvar is zero then the point will be deleted.
			"""
		],

		"ignoreMissingVariable" : [
			"description",
			"""
			Causes the node to do nothing if the primitive variable doesn't exist on the points, instead of erroring.
			"""
		],

	}

)
