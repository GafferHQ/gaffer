# Ideally, we'd `import Gaffer` in sphinx's `config.py` to work out versions/etc. During the Python
# 2/3 transition, this adds complexity as it requires sphinx (and associated modules) to be installed
# in the host environment for all versions of Python supported by Gaffer builds.
#
# To keep this simple, we run the built gaffer and extract versioning information there.

import json

import Gaffer

about = {
	"name" : Gaffer.About.name(),
	"copyright" : Gaffer.About.copyright(),
	"versionString" : Gaffer.About.versionString(),
	"milestoneVersion" : Gaffer.About.milestoneVersion(),
	"majorVersion" : Gaffer.About.majorVersion(),
	"minorVersion" : Gaffer.About.minorVersion(),
	"patchVersion" : Gaffer.About.patchVersion()
}

with open( "./gafferVars.json", 'w' ) as f :
	json.dump( about, f )
