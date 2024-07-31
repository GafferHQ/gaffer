# BuildTarget: index.md
# UndeclaredBuildTargets

import Gaffer
import GafferUI

# GafferArnold isn't installed under the standard module path
# (so we can support multiple Arnold versions) so we must
# specify it explicitly.
try :
	import GafferArnold
	import GafferArnoldUI
	modules = [ GafferArnold ]
except ImportError :
	modules = []

GafferUI.DocumentationAlgo.exportNodeReference( "./", modules = modules, modulePath = "$GAFFER_ROOT/python" )
