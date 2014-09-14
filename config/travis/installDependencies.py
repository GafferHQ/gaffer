import os
import re
import sys
import json
import urllib

# figure out where we'll be making the build

for line in open( "SConstruct" ).readlines() :
	if re.search( "gaffer[A-Za-z]*Version = ", line  ) :
		exec( line.strip() )

platform = "osx" if sys.platform == "darwin" else "linux"

buildDir = "build/gaffer-%d.%d.%d.%d-%s" % ( gafferMilestoneVersion, gafferMajorVersion, gafferMinorVersion, gafferPatchVersion, platform )

# get the prebuilt dependencies package and unpack it into the build directory

releases = json.load( urllib.urlopen( "https://api.github.com/repos/johnhaddon/gafferDependencies/releases" ) )
release = next( r for r in releases if len( r["assets"] ) )
 
asset = next( a for a in release["assets"] if platform in a["name"] )
tarFileName, headers = urllib.urlretrieve( asset["browser_download_url"] )

os.makedirs( buildDir )
os.system( "tar xf %s -C %s --strip-components=1" % ( tarFileName, buildDir ) )
