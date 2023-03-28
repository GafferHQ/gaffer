import Gaffer
import GafferUI
import GafferScene
import GafferOSL
import GafferAppleseed

GafferUI.Examples.registerExample(
	"Rendering/Anamorphic Camera",
	"$GAFFER_ROOT/resources/examples/rendering/anamorphicCameraSetup.gfr",
	description = "Demonstrates how to set up a Camera with a non-square pixel aspect ratio.",
	notableNodes = [
		GafferScene.Camera,
		GafferScene.StandardOptions
	]
)

GafferUI.Examples.registerExample(
	"Rendering/Macbeth Chart",
	"$GAFFER_ROOT/resources/examples/rendering/macbethChart.gfr",
	description = "Demonstrates how to create and assign a procedural OSL texture.",
	notableNodes = [
		GafferOSL.OSLCode,
		GafferOSL.OSLShader,
		Gaffer.Reference
	]
)

GafferUI.Examples.registerExample(
	"Rendering/Multi-shot Render Spreadsheet",
	"$GAFFER_ROOT/resources/examples/rendering/multiShotRenderSpreadsheet.gfr",
	description = """
	Demonstrates how to use the Spreadsheet node to vary renderer
	settings per shot.
	""",
	notableNodes = [
		Gaffer.Spreadsheet,
		GafferAppleseed.AppleseedOptions
	]
)

GafferUI.Examples.registerExample(
	"Rendering/Per-location Light Tweak Spreadsheet",
	"$GAFFER_ROOT/resources/examples/rendering/perLocationLightTweakSpreadsheet.gfr",
	description = """
	Demonstrates how to use the Spreadsheet node to vary light tweaks
	per location.
	""",
	notableNodes = [
		Gaffer.Spreadsheet,
		GafferScene.ShaderTweaks
	]
)