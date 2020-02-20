import Gaffer
import GafferUI
import GafferDispatch
import GafferImage
import GafferScene
import GafferOSL

GafferUI.Examples.registerExample(
	"Rendering/Wedge Tests",
	"$GAFFER_ROOT/resources/examples/rendering/wedgeTests.gfr",
	description = "Demonstrates how to use the Wedge node to render shader wedge tests.",
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
	"Compositing/Contact Sheet Generation",
	"$GAFFER_ROOT/resources/examples/compositing/contactSheet.gfr",
	description = "Demonstrates how to use the Loop node to build a contact sheet of shader variations.",
	notableNodes = [
		Gaffer.Loop,
		GafferImage.ImageTransform,
		Gaffer.Expression
	]
)

