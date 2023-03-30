import GafferUI
import GafferScene

GafferUI.Examples.registerExample(
	"Rendering/Anamorphic Camera",
	"$GAFFER_ROOT/resources/examples/rendering/anamorphicCameraSetup.gfr",
	description = "Demonstrates how to set up a Camera with a non-square pixel aspect ratio.",
	notableNodes = [
		GafferScene.Camera,
		GafferScene.StandardOptions
	]
)
