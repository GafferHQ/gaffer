import GafferUI
import GafferOSL

GafferUI.Examples.registerExample(
	"Compositing/OSL Image Processing",
	"$GAFFER_ROOT/resources/examples/compositing/OSLImageProcessing.gfr",
	description = "Demonstrates the use of OSL networks and the OSLImage node for image processing and pattern generation.",
	notableNodes = [
		GafferOSL.OSLImage
	]
)

GafferUI.Examples.registerExample(
	"Scene Processing/OSL Mesh Manipulation",
	"$GAFFER_ROOT/resources/examples/sceneProcessing/OSLMeshManipulation.gfr",
	description = "Demonstrates the use of OSL networks and the OSLObject node for mesh manipulation.",
	notableNodes = [
		GafferOSL.OSLObject
	]
)

GafferUI.Examples.registerExample(
	"Scene Processing/OSL PointCloud Lookups",
	"$GAFFER_ROOT/resources/examples/sceneProcessing/oslPointClouds.gfr",
	description = "Demonstrates the use of OSL's `pointcloud_search()` and `pointcloud_get()` functions to query scene geometry.",
	notableNodes = [
		GafferOSL.OSLObject
	]
)
