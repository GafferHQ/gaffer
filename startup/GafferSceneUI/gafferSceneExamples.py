import Gaffer
import GafferUI
import GafferScene

GafferUI.Examples.registerExample(
	"Scene Processing/Per-location Transform Spreadsheet",
	"$GAFFER_ROOT/resources/examples/sceneProcessing/perLocationTransformSpreadsheet.gfr",
	description = """
	Demonstrates how to use the Spreadsheet node to vary transform
	values per location.
	""",
	notableNodes = [
		Gaffer.Spreadsheet,
		GafferScene.Transform
	]
)

GafferUI.Examples.registerExample(
	"Scene Processing/Shader Tweaks",
	"$GAFFER_ROOT/resources/examples/sceneProcessing/shaderTweaks.gfr",
	description = """
	Demonstrates using ShaderTweaks for modifying shader networks.
	""",
	notableNodes = [
		GafferScene.ShaderTweaks,
		GafferScene.ShaderTweakProxy
	]
)
