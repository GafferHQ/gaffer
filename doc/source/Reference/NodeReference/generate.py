# BuildTarget: index.md
# UndeclaredBuildTargets

import Gaffer
import GafferUI

modules = []

# GafferArnold isn't installed under the standard module path
# (so we can support multiple Arnold versions) so we must
# specify it explicitly.
try :
	import GafferArnold
	import GafferArnoldUI
	modules.append( GafferArnold )
except ImportError :
	pass

# GafferRenderMan isn't installed under the standard module path
# so we must specify it explicitly.
try :
	import GafferRenderMan
	import GafferRenderManUI
	modules.append( GafferRenderMan )
except ImportError :
	pass

GafferUI.DocumentationAlgo.exportNodeReference( "./", modules = modules, modulePath = "$GAFFER_ROOT/python" )
