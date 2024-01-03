#!/usr/bin/env python
##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import argparse
import os
import sys
import tarfile
import zipfile

# A script to validate a Gaffer release archive

parser = argparse.ArgumentParser()

parser.add_argument(
	"--archive",
	dest = "archive",
	required = True,
	help = "The path to the build archive to publish."
)

parser.add_argument(
	"--skipDocs",
	action = 'store_true',
	help = "If set, validation will not check for documentation in the archive"
)

parser.add_argument(
	"--skipPaths",
	nargs = '+',
	default = [],
	help = "A list of paths to skip the checks for."
)

args = parser.parse_args()

if not os.path.exists( args.archive ) :
	parser.exit( 1, "The specified archive '%s' does not exist." % args.archive )


print( "Validating %s..." % args.archive )
# We often see the exit printout before the above on Azure, which overlaps
# lines and confuses one. Make sure this gets printed early on.
sys.stdout.flush()

# Validate the release contains our mandatory components

requiredPaths = [
	os.path.join( "resources", "examples" ),
	"arnold",
]

if args.skipDocs :
	sys.stderr.write( "WARNING: --skipDocs is set, not checking documentation\n" )
else :
	requiredPaths.append( os.path.join( "doc", "gaffer", "html", "index.html" ) )

for module in (
	"Gaffer", "GafferDelight",
	"GafferDispatch", "GafferImage", "GafferOSL", "GafferScene",
	"GafferTractor", "GafferVDB"
) :
	requiredPaths.append( os.path.join( "python", module ) )
	requiredPaths.append( os.path.join( "python", "%sUI" % module ) )

if os.name != "nt" :
	requiredPaths.append( os.path.join( "python", "GafferAppleseed" ) )
	requiredPaths.append( os.path.join( "python", "%sUI" % "GafferAppleseed" ) )

for path in args.skipPaths :
	if path in requiredPaths :
		requiredPaths.remove( path )

rawMembers = []

if args.archive.endswith( ".tar.gz" ) :

	with tarfile.open( args.archive, "r:gz" ) as a:

		# getmember still reads the whole archive, so might as well grab them all
		# as we go. We need to strip the first directory from all paths as that
		# contains the release name.

		for m in a.getmembers() :
			rawMembers.append( m.name )

elif args.archive.endswith( ".zip" ) :

	with zipfile.ZipFile( args.archive, "r" ) as a :

		rawMembers = a.namelist()

archivePaths = set()

for m in rawMembers :
	# ignore anything not under the release directory
	if "/" not in m :
		continue
	# Strip the release dir and any empty components at the end
	relPath = os.path.join( *m.split( "/" )[1:] )
	archivePaths.add( os.path.normpath( relPath ) )

missing = [ p for p in requiredPaths if p not in archivePaths ]
if missing :
	sys.stderr.write(
		"Validation failed\n%s\n"
			% "\n".join( [ "ERROR: %s is missing from the archive" % m for m in missing ] )
	)
	sys.exit( 1 )

	# We've seen sporadic validation failures in CI, temp hack to debug
	print( "\n------------------------" )
	print( "Considered archive paths" )
	print( "------------------------" )
	print( "\n".join( sorted(archivePaths) ) )
	print( "\n------------------------" )
	print( "All archive paths" )
	print( "------------------------" )
	print( "\n".join( [ m.name for m in rawMembers ] ) )

	sys.exit( 1 )

print( "Archive appears OK" )
