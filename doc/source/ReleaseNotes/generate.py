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
		versionIndex += ( "\n{}{}.md".format( " " * 4, m.group( 2 ) ) )
		versionFile = open( m.group( 2 ) + ".md", "w" )
		versionFile.write( m.group( 2 ) + "\n" )
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

	```eval_rst
	.. toctree::
	    :titlesonly:
	{0}
	```
	"""

).format( versionIndex ) )
