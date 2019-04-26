import Gaffer
import GafferUI
import GafferDispatch
import GafferImage
import GafferScene

GafferUI.Examples.registerExample(
	"Rendering/Wedge Tests",
	"$GAFFER_ROOT/resources/examples/rendering/wedgeTests.gfr",
	description = "Demonstrates how to use the Wedge node to render Shader wedge tests",
	notableNodes = [
		GafferDispatch.Wedge,
		GafferDispatch.SystemCommand,
		GafferImage.Text,
		GafferScene.Outputs,
		Gaffer.ContextVariables,
		Gaffer.Expression
	]
)

GafferUI.Examples.registerExample(
	"Rendering/Anamorphic Cameras",
	"$GAFFER_ROOT/resources/examples/rendering/anamorphicCameraSetup.gfr",
	description = "Demonstrates how to set up a Camera with a non-square pixel aspect ratio.",
	notableNodes = [
		GafferScene.Camera,
		GafferScene.StandardOptions
	]
)

GafferUI.Examples.registerExample(
	"Compositing/Contact Sheet Generation",
	"$GAFFER_ROOT/resources/examples/compositing/contactSheet.gfr",
	description = "Demonstrates how to use the Loop node to build a Contact Sheet of Shader variations",
	notableNodes = [
		Gaffer.Loop,
		GafferImage.ImageTransform,
		Gaffer.Expression
	]
)

