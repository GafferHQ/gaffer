##########################################################################
#
#  Copyright (c) 2015-2016, Image Engine Design Inc. All rights reserved.
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

import os

import IECore
import IECoreScene

import Gaffer
import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.ResamplePrimitiveVariables,

	"description",
	"""
	<p>Resamples the list of primitive variables in <i>Names</i> for either mesh, curves or point primitives.</p>

	<p>The reampling algorithm either expands or reduces each primitive variable's data based on the primitive type, primitive variable source interpolation and target interpolation as detailed in the tables below</p>

	<h4>Mesh Primitive</h4>
	<table border="2" style="width:100%;border:1px black">
	  <tr>
	  	<td>source / target</td>
		<td>Constant</td>
		<td>Uniform</td>
		<td>Vertex</td>
		<td>FaceVarying</td>
	  </tr>
	  <tr>
	    <td>Constant</td>
		<td>-</td>
		<td>copy</td>
		<td>copy</td>
		<td>copy</td>
	  </tr>
	  <tr>
	    <td>Uniform</td>
		<td>average</td>
		<td>-</td>
		<td>copy</td>
		<td>copy</td>
	  </tr>
	  <tr>
	    <td>Vertex / Varying</td>
		<td>average</td>
		<td>polygon average</td>
		<td>-</td>
		<td>copy</td>
	  </tr>
	  <tr>
	    <td>FaceVarying</td>
		<td>average</td>
		<td>polygon average</td>
		<td>vertex average</td>
		<td>-</td>
	  </tr>
	</table>

	<h4>Curves Primitive</h4>
	<table border="2" style="width:100%;border:1px black">
	  <tr>
	  	<td>source / target</td>
		<td>Constant</td>
		<td>Uniform</td>
		<td>Vertex</td>
		<td>FaceVarying</td>
	  </tr>
	  <tr>
	    <td>Constant</td>
		<td>-</td>
		<td>copy</td>
		<td>copy</td>
		<td>copy</td>
	  </tr>
	  <tr>
	    <td>Uniform</td>
		<td>average</td>
		<td>-</td>
		<td>copy</td>
		<td>copy</td>
	  </tr>
	  <tr>
	    <td>Vertex</td>
		<td>average</td>
		<td>curve average</td>
		<td>-</td>
		<td>evaluated</td>
	  </tr>
	  <tr>
	    <td>Varying / FaceVarying</td>
		<td>average</td>
		<td>curve average</td>
		<td>evaluated</td>
		<td>-</td>
	  </tr>
	</table>

	<h4>Points Primitive</h4>
	<table border="2" style="width:100%;border:1px black">
	  <tr>
	  	<td>source / target</td>
		<td>Constant</td>
		<td>Uniform</td>
		<td>Vertex / FaceVarying</td>
	  </tr>
	  <tr>
	    <td>Constant</td>
		<td>-</td>
		<td>copy</td>
		<td>copy</td>
	  </tr>
	  <tr>
	    <td>Uniform</td>
		<td>copy</td>
		<td>-</td>
		<td>copy</td>
	  </tr>
	  <tr>
	    <td>Vertex / Varying / FaceVarying</td>
		<td>average</td>
		<td>average</td>
		<td>-</td>
	  </tr>

	</table>

	<p><i>evaluated</i> : spline evaluated to approximate vertex or varying values</p>
	<p><i>copy</i> : expand source values to target based on topology </p>
	<p><i>average</i> : calculate the mean of the primitive variable (either for the whole primitive, for face / curve or vertex)</p>

	""",

	plugs = {

		"interpolation" : [

			"description",
			"""
			Target interpolation for the primitive variables
			""",

			"preset:Constant", IECoreScene.PrimitiveVariable.Interpolation.Constant,
			"preset:Uniform", IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			"preset:Vertex", IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			"preset:FaceVarying", IECoreScene.PrimitiveVariable.Interpolation.FaceVarying,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		]
	}

)
