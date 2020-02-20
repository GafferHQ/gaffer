import IECore
import Gaffer
import GafferScene
import GafferUI
import GafferArnold

GafferUI.Examples.registerExample(
	"Rendering/Per-Location Shader Variation (Arnold)",
	"$GAFFER_ROOT/resources/examples/rendering/perLocationShaderVariationArnold.gfr",
	description = "Demonstrates how to use custom attributes to create per-location shading variation.",
	notableNodes = [
		Gaffer.Random,
		GafferScene.CustomAttributes,
		GafferScene.AttributeVisualiser,
		GafferArnold.ArnoldShader
	]
)

GafferUI.Examples.registerExample(
	"Rendering/Spherical Camera (Arnold)",
	"$GAFFER_ROOT/resources/examples/rendering/sphericalCameraSetupArnold.gfr",
	description = "Demonstrates how to set up a spherical camera in Arnold.",
	notableNodes = [
		GafferScene.CameraTweaks,
		GafferScene.Camera
	]
)

GafferUI.Examples.registerExample(
	"Lighting/Light Linking Basics (Arnold)",
	"$GAFFER_ROOT/resources/examples/lighting/lightLinkingBasicsArnold.gfr",
	description = "Demonstrates each of the basic permutations of linked lights.",
	notableNodes = [
		GafferScene.StandardAttributes,
		GafferArnold.ArnoldLight
	]
)

GafferUI.Examples.registerExample(
	"Lighting/Light Linking City Attack (Arnold)",
	"$GAFFER_ROOT/resources/examples/lighting/lightLinkingCityAttackArnold.gfr",
	description = "A scene in which light linking is required to achieve two hero highlights.",
	notableNodes = [
		GafferScene.StandardAttributes,
		GafferArnold.ArnoldLight
	]
)

GafferUI.Examples.registerExample(
	"Lighting/Blockers (Arnold)",
	"$GAFFER_ROOT/resources/examples/lighting/blockers.gfr",
	description = "Demonstrates how to set up blockers in Arnold.",
	notableNodes = [
		GafferArnold.ArnoldLightFilter,
	]
)

GafferUI.Examples.registerExample(
	"Rendering/Trace Sets (Arnold)",
	"$GAFFER_ROOT/resources/examples/rendering/traceSetsArnold.gfr",
	description = "Demonstrates how to set up trace sets in Arnold.",
	notableNodes = [
		GafferScene.Set,
		GafferArnold.ArnoldShader
	]
)
