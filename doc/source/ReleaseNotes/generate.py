# BuildTarget: index.md
# UndeclaredBuildTargets

import re
import inspect

changes = open( "../../../Changes.md" )
# remove me

versionFile = None

versionIndex = ""

for line in changes :

	m = re.match( r"^(Gaffer )?(([0-9]+\.){2,3}[0-9]+)", line )
	if m :
		versionString = m.group( 2 )
		if versionString.startswith( "0." ) or versionString.count( "." ) != 3 :
			# Ignore versions prior to 1.0.0.0
			versionFile = None
		else :
			versionIndex += ( f"\n    {versionString}.md" )
			versionFile = open( f"{versionString}.md", "w" )
			versionFile.write( f"{versionString}\n" )
		continue

	if not versionFile :
		continue

	versionFile.write(
		re.sub( r"#([0-9]+)", r"[#\1](https://github.com/GafferHQ/gaffer/issues/\1)", line )
	)

index = open( "./index.md", "w" )

index.write( inspect.cleandoc(

	"""
	<!-- !NO_SCROLLSPY -->

	# Release Notes #

	```{{eval-rst}}
	.. toctree::
	    :titlesonly:
	{0}
	```
	"""

).format( versionIndex ) )
