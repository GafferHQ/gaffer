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

import imath
import inspect

import IECore
import IECoreScene

import Gaffer
import GafferScene

def __renderPassShaderAssignment( usage ):

	processor = GafferScene.SceneProcessor()

	processor["renderer"] = Gaffer.StringPlug()

	processor["defaultShader"] = Gaffer.ObjectPlug( defaultValue = IECore.NullObject() )
	processor["defaultArnoldShader"] = Gaffer.ObjectPlug( defaultValue = IECore.NullObject() )
	processor["defaultCyclesShader"] = Gaffer.ObjectPlug( defaultValue = IECore.NullObject() )
	processor["defaultDelightShader"] = Gaffer.ObjectPlug( defaultValue = IECore.NullObject() )

	processor["__optionQuery"] = GafferScene.OptionQuery()
	processor["__optionQuery"]["scene"].setInput( processor["in"] )
	processor["__optionQuery"].addQuery( Gaffer.ObjectPlug( defaultValue = IECore.NullObject() ) )
	processor["__optionQuery"].addQuery( Gaffer.ObjectPlug( defaultValue = IECore.NullObject() ) )
	processor["__optionQuery"]["queries"][0]["name"].setValue( "renderPass:shader:{}:*".format( usage ) )

	processor["__rendererExpression"] = Gaffer.Expression()
	processor["__rendererExpression"].setExpression(
		inspect.cleandoc(
			"""
			renderer = "3Delight" if parent["renderer"].startswith( "3Delight" ) else parent["renderer"]
			parent["__optionQuery"]["queries"]["query1"]["name"] = "renderPass:shader:{}:{{}}".format( renderer )
			""".format( usage )
		)
	)

	processor["__deleteAttributes"] = GafferScene.DeleteAttributes()
	processor["__deleteAttributes"]["in"].setInput( processor["in"] )
	processor["__deleteAttributes"]["names"].setValue( "*:surface surface" )

	processor["__shaderAttributes"] = GafferScene.CustomAttributes()
	processor["__shaderAttributes"]["in"].setInput( processor["__deleteAttributes"]["out"] )
	Gaffer.PlugAlgo.promote( processor["__shaderAttributes"]["filter"] )

	processor["__descendants"] = GafferScene.PathFilter()
	processor["__descendants"]["roots"].setInput( processor["filter"] )
	processor["__descendants"]["paths"].setValue( IECore.StringVectorData( [ "..." ] ) )
	processor["__deleteAttributes"]["filter"].setInput( processor["__descendants"]["out"] )

	processor["__shaderAssignmentExpression"] = Gaffer.Expression()
	processor["__shaderAssignmentExpression"].setExpression(
		inspect.cleandoc(
			"""
			import IECoreScene

			def validShaderNetwork( shader, fallback ) :

				return shader if isinstance( shader, IECoreScene.ShaderNetwork ) and shader.outputShader() else fallback

			renderer = parent["renderer"]
			shader = parent["defaultShader"]
			shaderType = "surface"

			if renderer == "Arnold" :
				shader = validShaderNetwork( parent["defaultArnoldShader"], shader )
				shaderType = "ai:surface"
			elif renderer == "Cycles" :
				shader = validShaderNetwork( parent["defaultCyclesShader"], shader )
				shaderType = "cycles:surface"
			elif renderer.startswith( "3Delight" ) :
				shader = validShaderNetwork( parent["defaultDelightShader"], shader )
				shaderType = "osl:surface"

			# A renderer specific shader registered in the options takes precedence
			# over a shader registered to "All" renderers.
			if parent["__optionQuery"]["out"]["out1"]["exists"] :
				shader = validShaderNetwork( parent["__optionQuery"]["out"]["out1"]["value"], shader )
			elif parent["__optionQuery"]["out"]["out0"]["exists"] :
				shader = validShaderNetwork( parent["__optionQuery"]["out"]["out0"]["value"], shader )

			shaders = {}
			if isinstance( shader, IECoreScene.ShaderNetwork ) and shader.outputShader() :
				shaders[shaderType] = shader

			parent["__shaderAttributes"]["extraAttributes"] = IECore.CompoundObject( shaders )
			"""
		)
	)

	processor["out"].setInput( processor["__shaderAttributes"]["out"] )

	return processor

def __catcherAndCasterFilter() :

	processor = Gaffer.SubGraph()

	processor["in"] = GafferScene.ScenePlug()

	processor["__optionQuery"] = GafferScene.OptionQuery()
	processor["__optionQuery"]["scene"].setInput( processor["in"] )
	processor["__optionQuery"].addQuery( Gaffer.StringPlug() )
	processor["__optionQuery"].addQuery( Gaffer.StringPlug() )
	processor["__optionQuery"]["queries"][0]["name"].setValue( "render:cameraInclusions" )
	processor["__optionQuery"]["queries"][1]["name"].setValue( "render:cameraExclusions" )

	processor["__catchersFilter"] = GafferScene.SetFilter()
	processor["__catchersExpression"] = Gaffer.Expression()
	processor["__catchersExpression"].setExpression(
		inspect.cleandoc(
			"""
			cameraInclusions = parent["__optionQuery"]["out"]["out0"]["value"]
			cameraExclusions = parent["__optionQuery"]["out"]["out1"]["value"]
			parent["__catchersFilter"]["setExpression"] = "({}) - ({})".format( cameraInclusions, cameraExclusions ) if ( cameraInclusions and cameraExclusions ) else cameraInclusions
			"""
		)
	)

	processor["__castersFilter"] = GafferScene.SetFilter()
	processor["__castersFilter"]["setExpression"].setInput( processor["__optionQuery"]["out"]["out1"]["value"] )

	Gaffer.PlugAlgo.promoteWithName( processor["__catchersFilter"]["out"], "catchers" )
	Gaffer.PlugAlgo.promoteWithName( processor["__castersFilter"]["out"], "casters" )

	return processor

def __shadowCatcherProcessor() :

	processor = GafferScene.SceneProcessor()

	processor["renderer"] = Gaffer.StringPlug()

	processor["__attributeSpreadsheet"] = Gaffer.Spreadsheet()
	processor["__attributeSpreadsheet"]["selector"].setInput( processor["renderer"] )
	processor["__attributeSpreadsheet"]["rows"].addColumn( Gaffer.StringPlug( "name" ) )
	for renderer, attributeName in (
		( "Arnold", "ai:visibility:shadow" ),
		( "Cycles", "cycles:visibility:shadow" ),
		( "3Delight*", "dl:visibility.shadow" )
	) :
		row = processor["__attributeSpreadsheet"]["rows"].addRow()
		row["name"].setValue( renderer )
		row["cells"]["name"]["value"].setValue( attributeName )

	processor["__catcherAndCasterFilter"] = __catcherAndCasterFilter()
	processor["__catcherAndCasterFilter"]["in"].setInput( processor["in"] )

	processor["__filterQuery"] = GafferScene.FilterQuery()
	processor["__filterQuery"]["scene"].setInput( processor["in"] )
	processor["__filterQuery"]["filter"].setInput( processor["__catcherAndCasterFilter"]["casters"] )
	processor["__filterQuery"]["location"].setValue( "/" )

	processor["__allShadowExcluded"] = GafferScene.CustomAttributes()
	processor["__allShadowExcluded"]["in"].setInput( processor["in"] )
	processor["__allShadowExcluded"]["attributes"].addChild( Gaffer.NameValuePlug( "", Gaffer.BoolPlug() ) )
	processor["__allShadowExcluded"]["attributes"][0]["name"].setInput( processor["__attributeSpreadsheet"]["out"]["name"] )
	processor["__allShadowExcluded"]["global"].setValue( True )

	# __allShadowExcluded is only required when shadow casters do not include the root of the scene.
	processor["__allShadowExcludedExpression"] = Gaffer.Expression()
	processor["__allShadowExcludedExpression"].setExpression(
		"""parent["__allShadowExcluded"]["enabled"] = not parent["__filterQuery"]["exactMatch"]"""
	)

	processor["__shadowInclusions"] = GafferScene.AttributeTweaks()
	processor["__shadowInclusions"]["in"].setInput( processor["__allShadowExcluded"]["out"] )
	processor["__shadowInclusions"]["tweaks"].addChild( Gaffer.TweakPlug( "", Gaffer.BoolPlug( defaultValue = True ), mode = Gaffer.TweakPlug.Mode.CreateIfMissing ) )
	processor["__shadowInclusions"]["tweaks"][0]["name"].setInput( processor["__attributeSpreadsheet"]["out"]["name"] )
	processor["__shadowInclusions"]["filter"].setInput( processor["__catcherAndCasterFilter"]["casters"] )

	processor["__shadowExclusions"] = GafferScene.AttributeTweaks()
	processor["__shadowExclusions"]["in"].setInput( processor["__shadowInclusions"]["out"] )
	processor["__shadowExclusions"]["tweaks"].addChild( Gaffer.TweakPlug( "", Gaffer.BoolPlug( defaultValue = False ), mode = Gaffer.TweakPlug.Mode.CreateIfMissing ) )
	processor["__shadowExclusions"]["tweaks"][0]["name"].setInput( processor["__attributeSpreadsheet"]["out"]["name"] )
	processor["__shadowExclusions"]["filter"].setInput( processor["__catcherAndCasterFilter"]["catchers"] )

	processor["__shaderAssignment"] = __renderPassShaderAssignment( "shadowCatcher" )
	processor["__shaderAssignment"]["renderer"].setInput( processor["renderer"] )
	processor["__shaderAssignment"]["in"].setInput( processor["__shadowExclusions"]["out"] )
	processor["__shaderAssignment"]["filter"].setInput( processor["__catcherAndCasterFilter"]["catchers"] )

	processor["__shaderAssignment"]["defaultArnoldShader"].setValue(
		IECoreScene.ShaderNetwork(
			shaders = {
				"shadowCatcher" : IECoreScene.Shader( "shadow_matte", "ai:surface", {
					"shadow_color" : imath.Color3f( 1 ),
					"background_color" : imath.Color3f( 0 ),
					"background" : "background_color"
				} ),
			},
			output = "shadowCatcher",
		)
	)

	processor["__shaderAssignment"]["defaultCyclesShader"].setValue(
		IECoreScene.ShaderNetwork(
			shaders = {
				"shadowCatcher" : IECoreScene.Shader( "principled_bsdf", "cycles:surface", {} ),
			},
			output = "shadowCatcher",
		)
	)

	processor["__shaderAssignment"]["defaultDelightShader"].setValue(
		IECoreScene.ShaderNetwork(
			shaders = {
				"shadowCatcher" : IECoreScene.Shader( "dlShadowMatte", "osl:surface", { "shadow_color" : imath.Color3f( 1 ) } ),
			},
			output = "shadowCatcher",
		)
	)

	# Localise and copy original shaders back to shadow casters in case they were
	# deleted as a result of being a descendant of a shadow catcher location.
	processor["__localiseAttributes"] = GafferScene.LocaliseAttributes()
	processor["__localiseAttributes"]["in"].setInput( processor["in"] )
	processor["__localiseAttributes"]["attributes"].setValue( "*:surface surface" )
	processor["__localiseAttributes"]["filter"].setInput( processor["__catcherAndCasterFilter"]["casters"] )

	processor["__copyAttributes"] = GafferScene.CopyAttributes()
	processor["__copyAttributes"]["source"].setInput( processor["__localiseAttributes"]["out"] )
	processor["__copyAttributes"]["in"].setInput( processor["__shaderAssignment"]["out"] )
	processor["__copyAttributes"]["filter"].setInput( processor["__catcherAndCasterFilter"]["casters"] )
	processor["__copyAttributes"]["attributes"].setValue( "*:surface surface" )

	# Cycles specifies shadow catchers with the `cycles:is_shadow_catcher` attribute.
	processor["__cyclesCatcherAttributes"] = GafferScene.CustomAttributes()
	processor["__cyclesCatcherAttributes"]["in"].setInput( processor["__copyAttributes"]["out"] )
	processor["__cyclesCatcherAttributes"]["attributes"].addChild( Gaffer.NameValuePlug( "cycles:is_shadow_catcher", Gaffer.BoolPlug( defaultValue = True ) ) )
	processor["__cyclesCatcherAttributes"]["filter"].setInput( processor["__catcherAndCasterFilter"]["catchers"] )

	# On shadow casters we override `cycles:is_shadow_catcher` off to ensure
	# casters that are descendants of catchers do not inherit the attribute.
	processor["__cyclesCasterAttributes"] = GafferScene.CustomAttributes()
	processor["__cyclesCasterAttributes"]["in"].setInput( processor["__cyclesCatcherAttributes"]["out"] )
	processor["__cyclesCasterAttributes"]["attributes"].addChild( Gaffer.NameValuePlug( "cycles:is_shadow_catcher", Gaffer.BoolPlug( defaultValue = False ) ) )
	processor["__cyclesCasterAttributes"]["filter"].setInput( processor["__catcherAndCasterFilter"]["casters"] )

	processor["__lightsSet"] = GafferScene.SetFilter()
	processor["__lightsSet"]["setExpression"].setValue( "__lights" )

	# Disabling shadow visibility on lights in 3Delight cause them to not cast shadows, so we must override
	# the `__allShadowExcluded` global shadow visibility attribute if it is enabled.
	processor["__lightShadowVisibility"] = GafferScene.AttributeTweaks()
	processor["__lightShadowVisibility"]["in"].setInput( processor["__copyAttributes"]["out"] )
	processor["__lightShadowVisibility"]["enabled"].setInput( processor["__allShadowExcluded"]["enabled"] )
	processor["__lightShadowVisibility"]["tweaks"].addChild( Gaffer.TweakPlug( "", Gaffer.BoolPlug( defaultValue = True ), mode = Gaffer.TweakPlug.Mode.CreateIfMissing ) )
	processor["__lightShadowVisibility"]["tweaks"][0]["name"].setValue( "dl:visibility.shadow" )
	processor["__lightShadowVisibility"]["filter"].setInput( processor["__lightsSet"]["out"] )

	processor["__rendererSwitch"] = Gaffer.NameSwitch()
	processor["__rendererSwitch"].setup( GafferScene.ScenePlug() )
	processor["__rendererSwitch"]["selector"].setInput( processor["renderer"] )
	processor["__rendererSwitch"]["in"].resize( 3 )
	processor["__rendererSwitch"]["in"]["in0"]["value"].setInput( processor["__copyAttributes"]["out"] )

	processor["__rendererSwitch"]["in"]["in1"]["name"].setValue( "Cycles" )
	processor["__rendererSwitch"]["in"]["in1"]["value"].setInput( processor["__cyclesCasterAttributes"]["out"] )

	processor["__rendererSwitch"]["in"]["in2"]["name"].setValue( "3Delight*" )
	processor["__rendererSwitch"]["in"]["in2"]["value"].setInput( processor["__lightShadowVisibility"]["out"] )

	# Redirect the Cycles "shadow_catcher" AOV to beauty to more closely match
	# Arnold and 3Delight behaviour.
	processor["__redirectOutputExpression"] = Gaffer.Expression()
	processor["__redirectOutputExpression"].setExpression(
		inspect.cleandoc(
			"""
			options = parent["__cyclesCasterAttributes"]["out"]["globals"]
			for o in options.keys() :
				if o.startswith( "output:" ) :
					if options[o].getType() != "ieDisplay" and options[o].getData() == "rgba" :
						options[o].setData( "shadow_catcher" )

			parent["__rendererSwitch"]["in"]["in1"]["value"]["globals"] = options
			"""
		)
	)

	processor["out"].setInput( processor["__rendererSwitch"]["out"]["value"] )

	return processor

def __reflectionCatcherProcessor() :

	processor = GafferScene.SceneProcessor()

	processor["renderer"] = Gaffer.StringPlug()

	processor["__attributeSpreadsheet"] = Gaffer.Spreadsheet()
	processor["__attributeSpreadsheet"]["selector"].setInput( processor["renderer"] )
	processor["__attributeSpreadsheet"]["rows"].addColumn( Gaffer.StringPlug( "name" ) )
	for renderer, attributeName in (
		( "Arnold", "ai:visibility:specular_reflect" ),
		( "Cycles", "cycles:visibility:glossy" ),
		( "3Delight*", "dl:visibility.reflection" )
	) :
		row = processor["__attributeSpreadsheet"]["rows"].addRow()
		row["name"].setValue( renderer )
		row["cells"]["name"]["value"].setValue( attributeName )

	processor["__catcherAndCasterFilter"] = __catcherAndCasterFilter()
	processor["__catcherAndCasterFilter"]["in"].setInput( processor["in"] )

	processor["__filterQuery"] = GafferScene.FilterQuery()
	processor["__filterQuery"]["scene"].setInput( processor["in"] )
	processor["__filterQuery"]["filter"].setInput( processor["__catcherAndCasterFilter"]["casters"] )
	processor["__filterQuery"]["location"].setValue( "/" )

	processor["__allReflectionExcluded"] = GafferScene.CustomAttributes()
	processor["__allReflectionExcluded"]["in"].setInput( processor["in"] )
	processor["__allReflectionExcluded"]["attributes"].addChild( Gaffer.NameValuePlug( "", Gaffer.BoolPlug() ) )
	processor["__allReflectionExcluded"]["attributes"][0]["name"].setInput( processor["__attributeSpreadsheet"]["out"]["name"] )
	processor["__allReflectionExcluded"]["global"].setValue( True )

	# __allReflectionExcluded is only required when reflection casters do not include the root of the scene.
	processor["__allReflectionExcludedExpression"] = Gaffer.Expression()
	processor["__allReflectionExcludedExpression"].setExpression(
		"""parent["__allReflectionExcluded"]["enabled"] = not parent["__filterQuery"]["exactMatch"]"""
	)

	processor["__reflectionInclusions"] = GafferScene.AttributeTweaks()
	processor["__reflectionInclusions"]["in"].setInput( processor["__allReflectionExcluded"]["out"] )
	processor["__reflectionInclusions"]["tweaks"].addChild( Gaffer.TweakPlug( "", Gaffer.BoolPlug( defaultValue = True ), mode = Gaffer.TweakPlug.Mode.CreateIfMissing ) )
	processor["__reflectionInclusions"]["tweaks"][0]["name"].setInput( processor["__attributeSpreadsheet"]["out"]["name"] )
	processor["__reflectionInclusions"]["filter"].setInput( processor["__catcherAndCasterFilter"]["casters"] )

	processor["__reflectionExclusions"] = GafferScene.AttributeTweaks()
	processor["__reflectionExclusions"]["in"].setInput( processor["__reflectionInclusions"]["out"] )
	processor["__reflectionExclusions"]["tweaks"].addChild( Gaffer.TweakPlug( "", Gaffer.BoolPlug( defaultValue = False ), mode = Gaffer.TweakPlug.Mode.CreateIfMissing ) )
	processor["__reflectionExclusions"]["tweaks"][0]["name"].setInput( processor["__attributeSpreadsheet"]["out"]["name"] )
	processor["__reflectionExclusions"]["filter"].setInput( processor["__catcherAndCasterFilter"]["catchers"] )

	# Cycles doesn't support fallback values in its `attribute` shader so we provide a fallback attribute.
	processor["__fallbackAttributes"] = GafferScene.AttributeTweaks()
	processor["__fallbackAttributes"]["in"].setInput( processor["__reflectionExclusions"]["out"] )
	processor["__fallbackAttributes"]["filter"].setInput( processor["__catcherAndCasterFilter"]["catchers"] )
	processor["__fallbackAttributes"]["localise"].setValue( True )
	processor["__fallbackAttributes"]["tweaks"].addChild( Gaffer.TweakPlug( "user:reflectionCatcher:roughness", Gaffer.FloatPlug( defaultValue = 0.15 ), mode = Gaffer.TweakPlug.Mode.CreateIfMissing ) )

	processor["__shaderAssignment"] = __renderPassShaderAssignment( "reflectionCatcher" )
	processor["__shaderAssignment"]["renderer"].setInput( processor["renderer"] )
	processor["__shaderAssignment"]["in"].setInput( processor["__fallbackAttributes"]["out"] )
	processor["__shaderAssignment"]["filter"].setInput( processor["__catcherAndCasterFilter"]["catchers"] )

	processor["__shaderAssignment"]["defaultShader"].setValue(
		IECoreScene.ShaderNetwork(
			shaders = {
				"reflectionCatcher" :
				IECoreScene.Shader( "UsdPreviewSurface", "surface",
					{
						"diffuseColor" : imath.Color3f( 1 ),
						"metallic" : 1.0,
					}
				),
				"roughnessReader" :
				IECoreScene.Shader( "UsdPrimvarReader_float", "surface",
					{
						"varname" : "user:reflectionCatcher:roughness",
					}
				)
			},
			connections = [
				( ( "roughnessReader", "result" ), ( "reflectionCatcher", "roughness" ) )
			],
			output = "reflectionCatcher",
		)
	)

	processor["__descendants"] = GafferScene.PathFilter()
	processor["__descendants"]["roots"].setInput( processor["__catcherAndCasterFilter"]["catchers"] )
	processor["__descendants"]["paths"].setValue( IECore.StringVectorData( [ "..." ] ) )

	processor["__deleteAttributes"] = GafferScene.DeleteAttributes()
	processor["__deleteAttributes"]["in"].setInput( processor["__shaderAssignment"]["out"] )
	processor["__deleteAttributes"]["names"].setValue( "linkedLights" )
	processor["__deleteAttributes"]["filter"].setInput( processor["__descendants"]["out"] )

	processor["__standardAttributes"] = GafferScene.StandardAttributes()
	processor["__standardAttributes"]["in"].setInput( processor["__deleteAttributes"]["out"] )
	processor["__standardAttributes"]["attributes"]["linkedLights"]["enabled"].setValue( True )
	processor["__standardAttributes"]["filter"].setInput( processor["__catcherAndCasterFilter"]["catchers"] )

	processor["__localiseAttributes"] = GafferScene.LocaliseAttributes()
	processor["__localiseAttributes"]["in"].setInput( processor["in"] )
	processor["__localiseAttributes"]["attributes"].setValue( "*:surface surface linkedLights" )
	processor["__localiseAttributes"]["filter"].setInput( processor["__catcherAndCasterFilter"]["casters"] )

	processor["__copyAttributes"] = GafferScene.CopyAttributes()
	processor["__copyAttributes"]["source"].setInput( processor["__localiseAttributes"]["out"] )
	processor["__copyAttributes"]["in"].setInput( processor["__standardAttributes"]["out"] )
	processor["__copyAttributes"]["filter"].setInput( processor["__catcherAndCasterFilter"]["casters"] )
	processor["__copyAttributes"]["attributes"].setValue( "*:surface surface linkedLights" )

	processor["out"].setInput( processor["__copyAttributes"]["out"] )

	return processor

def __reflectionAlphaCasterProcessor() :

	processor = GafferScene.SceneProcessor()

	processor["renderer"] = Gaffer.StringPlug()

	processor["__optionQuery"] = GafferScene.OptionQuery()
	processor["__optionQuery"]["scene"].setInput( processor["in"] )
	processor["__optionQuery"].addQuery( Gaffer.StringPlug() )
	processor["__optionQuery"]["queries"][0]["name"].setValue( "render:cameraExclusions" )

	processor["__reflectionCastersFilter"] = GafferScene.SetFilter()
	processor["__reflectionCastersFilter"]["setExpression"].setInput( processor["__optionQuery"]["out"]["out0"]["value"] )

	# Cycles doesn't support fallback values in its `attribute` shader so we provide a fallback attribute.
	processor["__fallbackAttributes"] = GafferScene.AttributeTweaks()
	processor["__fallbackAttributes"]["in"].setInput( processor["in"] )
	processor["__fallbackAttributes"]["filter"].setInput( processor["__reflectionCastersFilter"]["out"] )
	processor["__fallbackAttributes"]["localise"].setValue( True )
	processor["__fallbackAttributes"]["tweaks"].addChild( Gaffer.TweakPlug( "user:reflectionCaster:color", Gaffer.Color3fPlug( defaultValue = imath.Color3f( 1 ) ), mode = Gaffer.TweakPlug.Mode.CreateIfMissing ) )

	processor["__shaderAssignment"] = __renderPassShaderAssignment( "reflectionCaster" )
	processor["__shaderAssignment"]["renderer"].setInput( processor["renderer"] )
	processor["__shaderAssignment"]["in"].setInput( processor["__fallbackAttributes"]["out"] )
	processor["__shaderAssignment"]["filter"].setInput( processor["__reflectionCastersFilter"]["out"] )

	processor["__shaderAssignment"]["defaultShader"].setValue(
		IECoreScene.ShaderNetwork(
			shaders = {
				"reflectionCaster" :
				IECoreScene.Shader( "UsdPreviewSurface", "surface",
					{
						"diffuseColor" : imath.Color3f( 0 ),
						"roughness" : 1.0,
						"useSpecularWorkflow" : True,
					}
				),
				"colorReader" :
				IECoreScene.Shader( "UsdPrimvarReader_float3", "surface",
					{
						"varname" : "user:reflectionCaster:color",
					}
				)
			},
			connections = [
				( ( "colorReader", "result" ), ( "reflectionCaster", "emissiveColor" ) )
			],
			output = "reflectionCaster",
		)
	)

	processor["__lightsFilter"] = GafferScene.SetFilter()
	processor["__lightsFilter"]["setExpression"].setValue( "__lights" )

	processor["__prune"] = GafferScene.Prune()
	processor["__prune"]["in"].setInput( processor["__shaderAssignment"]["out"] )
	processor["__prune"]["filter"].setInput( processor["__lightsFilter"]["out"] )

	processor["out"].setInput( processor["__prune"]["out"] )

	return processor

def __deleteOutputsProcessor() :

	processor = GafferScene.SceneProcessor()

	processor["__deleteOutputs"] = GafferScene.DeleteOutputs()
	processor["__deleteOutputs"]["in"].setInput( processor["in"] )
	processor["__deleteOutputs"]["invertNames"].setValue( True )
	processor["__deleteOutputs"]["names"].setValue( "*/[Bb]eauty [Bb]eauty" )

	processor["out"].setInput( processor["__deleteOutputs"]["out"] )

	return processor

GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "shadow", "catcher", __shadowCatcherProcessor )
GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "shadow", "deleteOutputs", __deleteOutputsProcessor )

GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "reflection", "catcher", __reflectionCatcherProcessor )
GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "reflection", "deleteOutputs", __deleteOutputsProcessor )

GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "reflectionAlpha", "catcher", __reflectionCatcherProcessor )
GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "reflectionAlpha", "caster", __reflectionAlphaCasterProcessor )
GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "reflectionAlpha", "deleteOutputs", __deleteOutputsProcessor )

GafferScene.SceneAlgo.registerRenderAdaptor( "RenderPassTypeAdaptor", GafferScene.RenderPassTypeAdaptor, client = "*", renderer = "*" )
