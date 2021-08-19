##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import string

import IECore

import Gaffer
import GafferUI
import GafferArnold

def __visibilitySummary( plug ) :

	info = []
	for childName, label in (

		( "camera", "Camera" ),
		( "shadow", "Shad" ),
		( "diffuseReflection", "DiffRefl" ),
		( "specularReflection", "SpecRefl" ),
		( "diffuseTransmission", "DiffTrans" ),
		( "specularTransmission", "SpecTrans" ),
		( "volume", "Volume" ),
		( "subsurface", "Subsurf" ),

	)	:
		if plug[childName+"Visibility"]["enabled"].getValue() :
			info.append( label + ( " On" if plug[childName+"Visibility"]["value"].getValue() else " Off" ) )

	if plug["shadowGroup"]["enabled"].getValue() :
		info.append( "ShadowGroup Applied" )

	return ", ".join( info )

__transformTypeEnumNames = { "linear" : "Linear", "rotate_about_origin" : "RotateAboutOrigin",
	"rotate_about_center" : "RotateAboutCenter" }

def __autoBumpVisibilitySummary( plug ) :

	info = []
	for childName, label in (

		( "camera", "Camera" ),
		( "diffuseReflection", "DiffRefl" ),
		( "specularReflection", "SpecRefl" ),
		( "diffuseTransmission", "DiffTrans" ),
		( "specularTransmission", "SpecTrans" ),
		( "volume", "Volume" ),
		( "subsurface", "Subsurf" ),

	)	:
		if plug[childName+"AutoBumpVisibility"]["enabled"].getValue() :
			info.append( label + ( " On" if plug[childName+"AutoBumpVisibility"]["value"].getValue() else " Off" ) )

	return ", ".join( info )

def __transformSummary( plug ) :

	info = []

	if plug["transformType"]["enabled"].getValue() :
		info.append( "Transform Type " + __transformTypeEnumNames[ plug["transformType"]["value"].getValue() ] )

	return ", ".join( info )

def __shadingSummary( plug ) :

	info = []
	for childName in ( "matte", "opaque", "receiveShadows", "selfShadows" ) :
		if plug[childName]["enabled"].getValue() :
			info.append( IECore.CamelCase.toSpaced( childName ) + ( " On" if plug[childName]["value"].getValue() else " Off" ) )

	if plug["sssSetName"]["enabled"].getValue() :
		info.append( "SSS Set Name " + plug["sssSetName"]["value"].getValue() )

	return ", ".join( info )

def __subdivisionSummary( plug ) :

	info = []
	if plug["subdivIterations"]["enabled"].getValue() :
		info.append( "Iterations %d" % plug["subdivIterations"]["value"].getValue() )
	if plug["subdivAdaptiveError"]["enabled"].getValue() :
		info.append( "Error %s" % GafferUI.NumericWidget.valueToString( plug["subdivAdaptiveError"]["value"].getValue() ) )
	if plug["subdivAdaptiveMetric"]["enabled"].getValue() :
		info.append( string.capwords( plug["subdivAdaptiveMetric"]["value"].getValue().replace( "_", " " ) ) + " Metric" )
	if plug["subdivAdaptiveSpace"]["enabled"].getValue() :
		info.append( string.capwords( plug["subdivAdaptiveSpace"]["value"].getValue() ) + " Space" )
	if plug["subdivUVSmoothing"]["enabled"].getValue() :
		info.append(
			{
				"pin_corners" : "Pin UV Corners",
				"pin_borders" : "Pin UV Borders",
				"linear" : "Linear UVs",
				"smooth" : "Smooth UVs",
			}.get( plug["subdivUVSmoothing"]["value"].getValue() )
		)
	if plug["subdivSmoothDerivs"]["enabled"].getValue() :
		info.append( "Smooth Derivs " + ( "On" if plug["subdivSmoothDerivs"]["value"].getValue() else "Off" ) )
	if plug["subdividePolygons"]["enabled"].getValue() :
		info.append( "Subdivide Polygons " + ( "On" if plug["subdividePolygons"]["value"].getValue() else "Off" ) )

	return ", ".join( info )

def __curvesSummary( plug ) :

	info = []
	if plug["curvesMode"]["enabled"].getValue() :
		info.append( string.capwords( plug["curvesMode"]["value"].getValue() ) )
	if plug["curvesMinPixelWidth"]["enabled"].getValue() :
		info.append( "Min Pixel Width %s" % GafferUI.NumericWidget.valueToString( plug["curvesMinPixelWidth"]["value"].getValue() ) )

	return ", ".join( info )

def __volumeSummary( plug ) :

	info = []
	if plug["volumeStepScale"]["enabled"].getValue() :
		info.append( "Volume Step Scale %s" % GafferUI.NumericWidget.valueToString( plug["volumeStepScale"]["value"].getValue() ) )
	if plug["volumeStepSize"]["enabled"].getValue() :
		info.append( "Volume Step Size %s" % GafferUI.NumericWidget.valueToString( plug["volumeStepSize"]["value"].getValue() ) )
	if plug["shapeStepScale"]["enabled"].getValue() :
		info.append( "Shape Step Scale %s" % GafferUI.NumericWidget.valueToString( plug["shapeStepScale"]["value"].getValue() ) )
	if plug["shapeStepSize"]["enabled"].getValue() :
		info.append( "Shape Step Size %s" % GafferUI.NumericWidget.valueToString( plug["shapeStepSize"]["value"].getValue() ) )
	if plug["volumePadding"]["enabled"].getValue() :
		info.append( "Padding %s" % GafferUI.NumericWidget.valueToString( plug["volumePadding"]["value"].getValue() ) )
	if plug["velocityScale"]["enabled"].getValue() :
		info.append( "Velocity Scale %s" % GafferUI.NumericWidget.valueToString( plug["velocityScale"]["value"].getValue() ) )
	if plug["velocityFPS"]["enabled"].getValue() :
		info.append( "Velocity FPS %s" % GafferUI.NumericWidget.valueToString( plug["velocityFPS"]["value"].getValue() ) )
	if plug["velocityOutlierThreshold"]["enabled"].getValue() :
		info.append( "Velocity Outlier Threshold %s" % GafferUI.NumericWidget.valueToString( plug["velocityOutlierThreshold"]["value"].getValue() ) )

	return ", ".join( info )

def __toonSummary( plug ) :

	info = []
	if plug["toonId"]["enabled"].getValue() :
		info.append( "Toon Id " + plug["toonId"]["value"].getValue() )

	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferArnold.ArnoldAttributes,

	"description",
	"""
	Applies Arnold attributes to objects in the scene.
	""",

	plugs = {

		# Sections

		"attributes" : [

			"layout:section:Visibility:summary", __visibilitySummary,
			"layout:section:Displacement.Auto Bump Visibility:summary", __autoBumpVisibilitySummary,
			"layout:section:Transform:summary", __transformSummary,
			"layout:section:Shading:summary", __shadingSummary,
			"layout:section:Subdivision:summary", __subdivisionSummary,
			"layout:section:Curves:summary", __curvesSummary,
			"layout:section:Volume:summary", __volumeSummary,
			"layout:section:Toon:summary", __toonSummary,

		],

		# Visibility

		"attributes.cameraVisibility" : [

			"description",
			"""
			Whether or not the object is visible to camera
			rays. To hide an object completely, use the
			visibility settings on the StandardAttributes
			node instead.
			""",

			"layout:section", "Visibility",
			"label", "Camera",

		],

		"attributes.shadowVisibility" : [

			"description",
			"""
			Whether or not the object is visible to shadow
			rays (whether or not it casts shadows).
			""",

			"layout:section", "Visibility",
			"label", "Shadow",

		],

		"attributes.shadowGroup" : [

			"description",
			"""
			The lights that cause this object to cast shadows.
			Accepts a set expression or a space separated list of
			lights. Use \"defaultLights\" to refer to all lights that
			contribute to illumination by default.
			""",

			"layout:section", "Visibility",
			"label", "Shadow Group",
		],

		"attributes.diffuseReflectionVisibility" : [

			"description",
			"""
			Whether or not the object is visible in
			reflected diffuse ( ie. if it casts bounce light )
			""",

			"layout:section", "Visibility",
			"label", "Diffuse Reflection",

		],

		"attributes.specularReflectionVisibility" : [

			"description",
			"""
			Whether or not the object is visible in
			reflected specular ( ie. if it is visible in mirrors ).
			""",

			"layout:section", "Visibility",
			"label", "Specular Reflection",

		],

		"attributes.diffuseTransmissionVisibility" : [

			"description",
			"""
			Whether or not the object is visible in
			transmitted diffuse ( ie. if it casts light through leaves ).
			""",

			"layout:section", "Visibility",
			"label", "Diffuse Transmission",

		],

		"attributes.specularTransmissionVisibility" : [

			"description",
			"""
			Whether or not the object is visible in
			refracted specular ( ie. if it can be seen through glass ).
			""",

			"layout:section", "Visibility",
			"label", "Specular Transmission",

		],

		"attributes.volumeVisibility" : [

			"description",
			"""
			Whether or not the object is visible in
			volume scattering.
			""",

			"layout:section", "Visibility",
			"label", "Volume",

		],

		"attributes.subsurfaceVisibility" : [

			"description",
			"""
			Whether or not the object is visible to subsurface
			rays.
			""",

			"layout:section", "Visibility",
			"label", "Subsurface",

		],

		"attributes.autoBump" : [

			"description",
			"""
			Automatically turns the details of the displacement map
			into bump, wherever the mesh is not subdivided enough
			to properly capture them.
			""",

			"nodule:type", "",
			"layout:section", "Displacement",

		],

		"attributes.cameraAutoBumpVisibility" : [

			"description",
			"""
			Whether or not the autobump is visible to camera
			rays.
			""",

			"layout:section", "Displacement.Auto Bump Visibility",
			"label", "Camera",

		],

		"attributes.diffuseReflectionAutoBumpVisibility" : [

			"description",
			"""
			Whether or not the autobump is visible in
			reflected diffuse ( ie. if it casts bounce light )
			""",

			"layout:section", "Displacement.Auto Bump Visibility",
			"label", "Diffuse Reflection",

		],

		"attributes.specularReflectionAutoBumpVisibility" : [

			"description",
			"""
			Whether or not the autobump is visible in
			reflected specular ( ie. if it is visible in mirrors ).
			""",

			"layout:section", "Displacement.Auto Bump Visibility",
			"label", "Specular Reflection",

		],

		"attributes.diffuseTransmissionAutoBumpVisibility" : [

			"description",
			"""
			Whether or not the autobump is visible in
			transmitted diffuse ( ie. if it casts light through leaves ).
			""",

			"layout:section", "Displacement.Auto Bump Visibility",
			"label", "Diffuse Transmission",

		],

		"attributes.specularTransmissionAutoBumpVisibility" : [

			"description",
			"""
			Whether or not the autobump is visible in
			refracted specular ( ie. if it can be seen through glass ).
			""",

			"layout:section", "Displacement.Auto Bump Visibility",
			"label", "Specular Transmission",

		],

		"attributes.volumeAutoBumpVisibility" : [

			"description",
			"""
			Whether or not the autobump is visible in
			volume scattering.
			""",

			"layout:section", "Displacement.Auto Bump Visibility",
			"label", "Volume",

		],

		"attributes.subsurfaceAutoBumpVisibility" : [

			"description",
			"""
			Whether or not the autobump is visible to subsurface
			rays.
			""",

			"layout:section", "Displacement.Auto Bump Visibility",
			"label", "Subsurface",

		],

		# Transform

		"attributes.transformType" : [

			"description",
			"""
			Choose how transform motion is interpolated.  Linear
			produces classic linear vertex motion, RotateAboutOrigin
			produces curved arcs centred on the object's origin, and
			RotateAboutCenter, the default, produces curved arcs
			centred on the object's bounding box middle.
			""",

			"layout:section", "Transform",

		],
		"attributes.transformType.value" : [

			"presetNames", lambda plug : IECore.StringVectorData( __transformTypeEnumNames.values() ),
			"presetValues", lambda plug : IECore.StringVectorData( __transformTypeEnumNames.keys() ),

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		# Shading

		"attributes.matte" : [

			"description",
			"""
			Turns the object into a holdout matte.
			This only affects primary (camera) rays.
			""",

			"layout:section", "Shading",

		],

		"attributes.opaque" : [

			"description",
			"""
			Flags the object as being opaque, allowing
			Arnold to render faster. Should be turned off
			when using partially transparent shaders.
			""",

			"layout:section", "Shading",

		],

		"attributes.receiveShadows" : [

			"description",
			"""
			Whether or not the object receives shadows.
			""",

			"layout:section", "Shading",

		],

		"attributes.selfShadows" : [

			"description",
			"""
			Whether or not the object casts shadows
			onto itself.
			""",

			"layout:section", "Shading",

		],

		"attributes.sssSetName" : [

			"description",
			"""
			If given, subsurface will be blended across any other objects which share the same sss set name.
			""",

			"layout:section", "Shading",
			"label", "SSS Set Name",
		],

		# Subdivision

		"attributes.subdivIterations" : [

			"description",
			"""
			The maximum number of subdivision
			steps to apply when rendering subdivision
			surface. To set an exact number of
			subdivisions, set the adaptive error to
			0 so that the maximum becomes the
			controlling factor.

			Use the MeshType node to ensure that a
			mesh is treated as a subdivision surface
			in the first place.
			""",

			"layout:section", "Subdivision",
			"label", "Iterations",

		],

		"attributes.subdivAdaptiveError" : [

			"description",
			"""
			The maximum allowable deviation from the true
			surface and the subdivided approximation. How
			the error is measured is determined by the
			metric below. Note also that the iterations
			value above provides a hard limit on the maximum
			number of subdivision steps, so if changing the
			error setting appears to have no effect,
			you may need to raise the maximum.

			> Note : Objects with a non-zero value will not take part in
			> Gaffer's automatic instancing unless subdivAdaptiveSpace is
			> set to "object".
			""",

			"layout:section", "Subdivision",
			"label", "Adaptive Error",

		],

		"attributes.subdivAdaptiveMetric" : [

			"description",
			"""
			The metric used when performing adaptive
			subdivision as specified by the adaptive error.
			The flatness metric ensures that the subdivided
			surface doesn't deviate from the true surface
			by more than the error, and will tend to
			increase detail in areas of high curvature. The
			edge length metric ensures that the edge length
			of a polygon is never longer than the error,
			so will tend to subdivide evenly regardless of
			curvature - this can be useful when applying a
			displacement shader. The auto metric automatically
			uses the flatness metric when no displacement
			shader is applied, and the edge length metric when
			a displacement shader is applied.
			""",

			"layout:section", "Subdivision",
			"label", "Adaptive Metric",

		],


		"attributes.subdivAdaptiveMetric.value" : [

			"preset:Auto", "auto",
			"preset:Edge Length", "edge_length",
			"preset:Flatness", "flatness",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"attributes.subdivAdaptiveSpace" : [

			"description",
			"""
			The space in which the error is measured when
			performing adaptive subdivision. Raster space means
			that the subdivision adapts to size on screen,
			with subdivAdaptiveError being specified in pixels.
			Object space means that the error is measured in
			object space units and will not be sensitive to
			size on screen.
			""",

			"layout:section", "Subdivision",
			"label", "Adaptive Space",

		],


		"attributes.subdivAdaptiveSpace.value" : [

			"preset:Raster", "raster",
			"preset:Object", "object",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"attributes.subdivUVSmoothing" : [

			"label", "UV Smoothing",
			"description",
			"""
			Determines how UVs are subdivided.
			""",

			"layout:section", "Subdivision",

		],

		"attributes.subdivUVSmoothing.value" : [

			"preset:Pin Corners", "pin_corners",
			"preset:Pin Borders", "pin_borders",
			"preset:Linear", "linear",
			"preset:Smooth", "smooth",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"attributes.subdivSmoothDerivs" : [

			"layout:section", "Subdivision",
			"label", "Smooth Derivatives",

			"description",
			"""
			Computes smooth UV derivatives (dPdu and dPdv) per
			vertex. This can be needed to remove faceting
			from anisotropic specular and other shading effects
			that use the derivatives.
			""",

		],

		"attributes.subdividePolygons" : [

			"description",
			"""
			Causes polygon meshes to be rendered with Arnold's
			subdiv_type parameter set to "linear" rather than
			"none". This can be used to increase detail when
			using polygons with displacement shaders and/or mesh
			lights.

			> Caution : This is not equivalent to converting a polygon
			> mesh into a subdivision surface. To render with Arnold's
			> subdiv_type set to "catclark", you must use the MeshType
			> node to convert polygon meshes into subdivision surfaces.
			""",

			"layout:section", "Subdivision",
			"label", "Subdivide Polygons (Linear)",

		],

		# Curves

		"attributes.curvesMode" : [

			"description",
			"""
			How the curves are rendered. Ribbon mode treats
			the curves as flat ribbons facing the camera, and is
			most suited for rendering of thin curves with a
			dedicated hair shader. Thick mode treats the curves
			as tubes, and is suited for use with a regular
			surface shader.

			> Note : To render using Arnold's "oriented" mode, set
			> mode to "ribbon" and add per-vertex normals to the
			> curves as a primitive variable named "N".
			""",

			"layout:section", "Curves",
			"label", "Mode",

		],

		"attributes.curvesMode.value" : [

			"preset:Ribbon", "ribbon",
			"preset:Thick", "thick",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"attributes.curvesMinPixelWidth" : [

			"description",
			"""
			The minimum thickness of the curves, measured
			in pixels on the screen. When rendering very thin curves, a
			large number of AA samples are required
			to avoid aliasing. In these cases a minimum pixel
			width may be specified to artificially thicken the curves,
			meaning that fewer AA samples may be used. The additional width is
			compensated for automatically by lowering the opacity
			of the curves.
			""",

			"layout:section", "Curves",
			"label", "Min Pixel Width",

		],

		# Volume

		"attributes.volumeStepScale" : [

			"description",
			"""
			Raymarching step size is calculated using this value
			multiplied by the volume voxel size or volumeStepSize if set.
			""",

			"layout:section", "Volume",
			"label", "Volume Step Scale",

		],

		"attributes.volumeStepSize" : [

			"description",
			"""
			Override the step size taken when raymarching volumes.
			If this value is disabled or zero then value is calculated from the voxel size.
			""",

			"layout:section", "Volume",
			"label", "Volume Step Size",

		],

		"attributes.shapeStepScale" : [

			"description",
			"""
			Raymarching step size is calculated using this value
			multiplied by the shapeStepSize.
			""",

			"layout:section", "Volume",
			"label", "Shape Step Scale",

		],

		"attributes.shapeStepSize" : [

			"description",
			"""
			A non-zero value causes an object to be treated
			as a volume container, and a value of 0 causes
			an object to be treated as regular geometry.
			""",

			"layout:section", "Volume",
			"label", "Shape Step Size",

		],

		"attributes.volumePadding" : [

			"description",
			"""
			Allows a volume to be displaced outside its bounds.  When
			rendering a mesh as a volume, this enables displacement.
			""",

			"layout:section", "Volume",
			"label", "Padding",

		],

		"attributes.velocityScale" : [

			"description",
			"""
			Scales the vector used in VDB motion blur computation.
			""",

			"layout:section", "Volume",
			"label", "Velocity Scale",

		],

		"attributes.velocityFPS" : [

			"description",
			"""
			Sets the frame rate used in VDB motion blur computation.
			""",

			"layout:section", "Volume",
			"label", "Velocity FPS",

		],

		"attributes.velocityOutlierThreshold" : [

			"description",
			"""
			Sets the outlier threshold used in VDB motion blur computation.

			When rendering physics simulations resulting velocities are
			potentially noisy and require some filtering for faster rendering.
			""",

			"layout:section", "Volume",
			"label", "Velocity Outlier Threshold",

		],

		"attributes.toonId" : [

			"description",
			"""
			You can select in the toon shader to skip outlines between objects with the same toon id set.
			""",

			"layout:section", "Toon",
			"label", "Toon Id",

		],

	}

)
