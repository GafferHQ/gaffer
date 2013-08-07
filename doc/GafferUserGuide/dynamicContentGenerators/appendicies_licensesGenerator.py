import IECore
from Gaffer import About

import sys,os

#print dir(About)
#print About.copyright()
#print About.license()


#open file ready to write asciidoc formatted data into
targetDoc = open('./chapters/appendices_licenses_dynamicContent.txt', 'w')

targetDoc.write( '==== Gaffer\n' )

licensePath = About.license().replace( '$GAFFER_ROOT', os.environ['GAFFER_ROOT']  )
if os.path.exists( licensePath ):
	with open( licensePath, 'r' ) as fh:
		license = fh.read()
		targetDoc.write( '%s' % (license) )

targetDoc.write( '==== Dependencies\n' )
targetDoc.write( About.dependenciesPreamble() )

#write out the dependencies info in asciidoc format
for dependency in About.dependencies():
	targetDoc.write( '\n\n===== %s' % (dependency['name']) )
	if 'credit' in dependency:
		targetDoc.write( '\n%s\n' % (dependency['credit']) )
	if 'url' in dependency:
		targetDoc.write( '\n%s' % (dependency['url']) )
	if 'license' in dependency:
		licensePath = dependency['license'].replace( '$GAFFER_ROOT', os.environ['GAFFER_ROOT']  )
		if os.path.exists( licensePath ):
			with open( licensePath, 'r' ) as fh:
				license = fh.read()
				targetDoc.write( '\n\n%s' % (license) )
	
