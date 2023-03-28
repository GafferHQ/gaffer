import Gaffer
import GafferUI
import GafferScene
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
