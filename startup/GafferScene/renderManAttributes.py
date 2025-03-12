##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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
import pathlib
import re

import IECore

import Gaffer

# Pull all the attribute definitions out of RenderMan's `PRManAttributes.args`
# and `PRManPrimVars.args` files, and register them using Gaffer's standard
# metadata conventions. This is then used to populate the RenderManAttributes
# node and the AttributeEditor etc.

if "RMANTREE" in os.environ :

	import GafferRenderMan.ArgsFileAlgo

	rmanTree = pathlib.Path( os.environ["RMANTREE"] )

	GafferRenderMan.ArgsFileAlgo.registerMetadata(
		rmanTree / "lib" / "defaults" / "PRManAttributes.args", "attribute:ri:",
		parametersToIgnore = {
			# Things that Gaffer has renderer-agnostic attributes for already.
			"Ri:Sides",
			"lighting:mute",
			# Things that we specify internally in the Renderer class.
			"identifier:name",
			# Things that we might want to use internally in the Renderer class.
			"identifier:id",
			"identifier:id2",
			"stats:identifier",
			"Ri:ReverseOrientation",
			# Things that we probably want to expose, but which will require
			# additional plumbing before they will be useful.
			"lightfilter:subset",
			"lighting:excludesubset",
			"lighting:subset",
			"trace:reflectexcludesubset",
			"trace:reflectsubset",
			"trace:shadowexcludesubset",
			"trace:shadowsubset",
			"trace:transmitexcludesubset",
			"trace:transmitsubset",
			# Might it be better if we populate this automatically based on set
			# memberships and/or light links? Don't expose it until we know.
			"grouping:membership",
		}
	)

	GafferRenderMan.ArgsFileAlgo.registerMetadata(
		rmanTree / "lib" / "defaults" / "PRManPrimVars.args", "attribute:ri:",
		parametersToIgnore = {
			# Things which we probably need to handle automatically in the
			# Renderer class.
			"identifier:object",
			"stats:prototypeIdentifier",
			"Ri:Bound",
			"Ri:Orientation",
			# Things that we might want to expose but which might need extra
			# plumbing to make work.
			"dice:referencecamera",
			"dice:referenceinstance",
			"shade:faceset",
			"trimcurve:sense",
			# Things that we think might just be too esoteric or which have no
			# documentation to explain them. People can always use
			# CustomAttributes to specify these.
			"polygon:concave",
			"displacement:ignorereferenceinstance",
			"stitchbound:CoordinateSystem",
			"stitchbound:sphere",
		}
	)

	# Override dodgy bits with our own metadata.

	Gaffer.Metadata.registerValue( "attribute:ri:derivatives:extrapolate", "label", "Extrapolate Derivatives" )
	Gaffer.Metadata.registerValue( "attribute:ri:trace:sssautobias", "label", "SSS Auto Trace Bias" )
	Gaffer.Metadata.registerValue( "attribute:ri:trace:sssbias", "label", "SSS Trace Bias" )
	Gaffer.Metadata.registerValue( "attribute:ri:dice:strategy", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )

	# Move displacement stuff into its own section. This simplifies the very
	# long shading section and allows us to use shorter labels that fit the
	# available space.

	for attribute in [
		"trace:displacements",
		"displacementbound:CoordinateSystem",
		"displacementbound:CoordinateSystem",
		"displacementbound:offscreen",
		"displacementbound:sphere",
	] :
		target = f"attribute:ri:{attribute}"
		Gaffer.Metadata.registerValue( target, "layout:section", "Displacement" )
		if attribute == "trace:displacements" :
			label = "Trace"
		else :
			label = re.sub( r"[dD]isplacement ?", "", Gaffer.Metadata.value( target, "label" ) )
		Gaffer.Metadata.registerValue( target, "label", label )

	Gaffer.Metadata.registerValue( "attribute:ri:displacementbound:CoordinateSystem", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
	Gaffer.Metadata.registerValue( "attribute:ri:displacementbound:CoordinateSystem", "presetNames", IECore.StringVectorData( [ "Object", "World" ] ) )
	Gaffer.Metadata.registerValue( "attribute:ri:displacementbound:CoordinateSystem", "presetValues", IECore.StringVectorData( [ "object", "world" ] ) )

	# Register BoolPlugValueWidget for attributes which are actually integers
	# but would more logically be bools. We can't change their type, because
	# then we're not going to line up with USD on export/import. But we can at
	# least improve the user interaction.

	for attribute in [
		"visibility:camera",
		"visibility:indirect",
		"visibility:transmission",
		"trace:holdout",
		"Ri:Matte",
		"curves:widthaffectscurvature",
		"displacementbound:offscreen",
	] :
		Gaffer.Metadata.registerValue( f"attribute:ri:{attribute}", "plugValueWidget:type", "GafferUI.BoolPlugValueWidget" )
