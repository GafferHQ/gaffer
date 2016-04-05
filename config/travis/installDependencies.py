import os
import re
import sys
import urllib

# figure out where we'll be making the build

for line in open( "SConstruct" ).readlines() :
	if re.search( "gaffer[A-Za-z]*Version = ", line  ) :
		exec( line.strip() )

platform = "osx" if sys.platform == "darwin" else "linux"

buildDir = "build/gaffer-%d.%d.%d.%d-%s" % ( gafferMilestoneVersion, gafferMajorVersion, gafferMinorVersion, gafferPatchVersion, platform )

# get the prebuilt dependencies package and unpack it into the build directory

downloadURL = "https://github.com/johnhaddon/gafferDependencies/releases/download/0.23.2.0/gafferDependencies-0.23.2.0-linux.tar.gz"

sys.stderr.write( "Downloading dependencies \"%s\"" % downloadURL )
tarFileName, headers = urllib.urlretrieve( downloadURL )

os.makedirs( buildDir )
os.system( "tar xf %s -C %s --strip-components=1" % ( tarFileName, buildDir ) )
