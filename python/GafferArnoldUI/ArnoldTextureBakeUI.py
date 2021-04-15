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

import Gaffer
import GafferArnold

Gaffer.Metadata.registerNode(

	GafferArnold.ArnoldTextureBake,

	"description",
	"""
	Render meshes in Arnold, storing the results into images in the texture space of the meshes.
	Supports multiple meshes and UDIMs, and any AOVs output by Arnold.  The file name and
	resolution can be overridden per mesh using the "bake:fileName" and "bake:resolution" attributes.
	""",
	"layout:activator:medianActivator", lambda parent : parent["applyMedianFilter"].getValue(),

	plugs = {

		"in" : [

			"description",
			"""
			The input scene containing the meshes to bake, and any lights which affect them.
			""",
			"nodule:type", "GafferUI::StandardNodule",
		],

		"filter" : [

			"description",
			"""
			The filter used to control which meshes the textures will be baked for.
			A Filter node should be connected here.
			""",

			"layout:section", "Filter",
			"noduleLayout:section", "right",
			"layout:index", -3, # Just before the enabled plug,
			"nodule:type", "GafferUI::StandardNodule",
			"plugValueWidget:type", "GafferSceneUI.FilterPlugValueWidget",

		],

		"bakeDirectory" : [

			"description",
			"""
			Sets the Context Variable used in the default file name to control where all the bakes will be stored.
			""",
		],

		"defaultFileName" : [

			"description",
			"""
			The file name to use for each texture file written.  <UDIM> will be replaced by the UDIM number,
			and <AOV> will be replaced by the aov name specified in "aovs".  If you want to do an animated bake,
			you can also use #### which will be replaced by the frame number.

			May be overridden per mesh by specifying the "bake:fileName" string attribute on the meshes to be baked.
			""",
		],

		"defaultResolution" : [

			"description",
			"""
			The resolution to use for each texture file written.

			May be overridden per mesh by specifying the "bake:resolution" integer attribute on the meshes to be baked.
			""",
		],

		"uvSet" : [

			"description",
			"""
			The name of the primitive variable containing uvs which will determine how the mesh is unwrapped
			for baking.  Must be a Face-Varying or Vertex V2f primitive variable.
			""",
		],

		"udims" : [
			"description",
			"""
			If non-empty, only UDIMs in this list will be baked. The formatting is the same as a frame list:
			comma separated, with dashes indicating ranges.
			""",
		],

		"normalOffset" : [

			"description",
			"""
			How far Arnold steps away from the surface before tracing back.  If too large for your scene,
			you will incorrectly capture occluders near the mesh instead of the mesh itself.  If too small,
			everything will go speckly because Arnold has insufficient precision to hit the mesh.  For objects
			which are fairly large and simple, the default 0.1 should work.  Smaller objects may require smaller
			values.
			""",
		],

		"aovs" : [

			"description",
			"""
			A space separated list of colon separated pairs of image name and data to render.

			For example, you could set this to "myName1:RGBA myName2:diffuse myName3:diffuse_albedo", to
			render 3 sets of images for every UDIM and mesh baked, containing all lighting, just diffuse
			lighting, and the diffuse albedo.
			""",
		],

		"tasks" : [
			"description",
			"""
			How many tasks the bake process will be split into.  UDIMs cannot be split across tasks, so if you
			have few UDIMs available, the extra tasks won't do anything, but if you have a large number of
			UDIMs, and are dispatching to a pool of machines, increasing the number of tasks used will speed
			up bakes, at the cost of using more machines.
			""",
		],

		"cleanupIntermediateFiles" : [
			"description",
			"""
			During baking, we first render exrs ( potentially multiple EXRs per udim if multiple objects
			are present ).  We then combine them, fill in the background, and convert to textures.  This
			causes all intermediate EXRs, and the index txt file to be removed, and just the final .tx to be kept.
			""",
			"divider", True,
		],

		"applyMedianFilter" : [
			"description",
			"""
			Adds a simple denoising filter to the texture bake. Mostly preserves high-contrast edges.
			""",
		],

		"medianRadius" : [
			"description",
			"""
			The radius of the median filter. Values greater than 1 will likely remove small details from the texture.
			""",
			"layout:activator", "medianActivator",
		],

	}

)
