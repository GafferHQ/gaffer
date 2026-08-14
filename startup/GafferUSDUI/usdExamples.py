import GafferUI
import GafferScene
import GafferUSD

rendererLights = []
try :
	import GafferArnold
	rendererLights.append( GafferArnold.ArnoldLight )
except ImportError :
	pass

try :
	import GafferCycles
	rendererLights.append( GafferCycles.CyclesLight )
except ImportError :
	pass

try :
	import GafferRenderMan
	rendererLights.append( GafferRenderMan.RenderManLight )
except ImportError :
	pass

GafferUI.Examples.registerExample(
	"Lighting/Light Linking Basics",
	"$GAFFER_ROOT/resources/examples/lighting/lightLinkingBasics.gfr",
	description = "Demonstrates each of the basic permutations of linked lights.",
	notableNodes = [
		GafferScene.StandardAttributes,
		GafferUSD.USDLight
	] + rendererLights
)
