import Gaffer
import GafferUI
import GafferImage
GafferUI.Examples.registerExample(
	"Compositing/Contact Sheet Generation",
	"$GAFFER_ROOT/resources/examples/compositing/contactSheet.gfr",
	description = "Demonstrates how to use the Loop node to build a contact sheet of shader variations.",
	notableNodes = [
		Gaffer.Loop,
		GafferDispatch.Wedge,
		GafferImage.ImageTransform,
		GafferImage.ImageWriter,
		Gaffer.ContextQuery,
		Gaffer.Expression
	]
)

