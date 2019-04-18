import IECore
import Gaffer
import GafferScene
import GafferUI
import GafferArnold

GafferUI.Examples.registerExample(
	"Rendering/Per-Location Shader Variation (Arnold)",
	"$GAFFER_ROOT/resources/examples/rendering/perLocationShaderVariationArnold.gfr",
	description = "Demonstrates how to use Custom Attributes to create per-location shading variation.",
	notableNodes = [
		Gaffer.Random,
		GafferScene.CustomAttributes,
		GafferScene.AttributeVisualiser,
		GafferArnold.ArnoldShader
	]
)

GafferUI.Examples.registerExample(
	"Rendering/Spherical Cameras (Arnold)",
	"$GAFFER_ROOT/resources/examples/rendering/sphericalCameraSetupArnold.gfr",
	description = "Demonstrates how to set up a Spherical camera in Arnold",
	notableNodes = [
		GafferScene.CameraTweaks,
		GafferScene.Camera
	]
)

