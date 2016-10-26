import re

index = open( "./index.md", "w" )
index.write( "Release Notes\n" )
index.write( "=============\n\n" )

changes = open( "../../../Changes" )

versionFile = None

for line in changes :

	m = re.match( r"^(Gaffer )?(([0-9]+\.){2,3}[0-9]+)", line )
	if m :
		index.write( "- [{0}]({0}.md)\n".format( m.group( 2 ) ) )
		versionFile = open( m.group( 2 ) + ".md", "w" )
		versionFile.write( m.group( 2 ) + "\n" )
		continue

	if not versionFile :
		continue

	versionFile.write(
		re.sub( r"#([0-9]+)", r"[#\1](https://github.com/GafferHQ/gaffer/issues/\1)", line )
	)
