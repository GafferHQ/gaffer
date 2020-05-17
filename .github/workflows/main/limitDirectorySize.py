#!/usr/bin/env python

##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of Image Engine Design nor the names of any
#       other contributors to this software may be used to endorse or
#       promote products derived from this software without specific prior
#       written permission.
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

import os
import sys
import argparse
import collections

parser = argparse.ArgumentParser()

parser.add_argument(
	"--directory",
	help = "The directory to remove files from.",
	default = "",
	required = True,
)

parser.add_argument(
	"--megabytes",
	help = "The size limit for all files in the directory.",
	default = 400,
	type = int,
)

parser.add_argument(
	"--verbose",
	help = "Prints out information about what is being removed.",
	default = False,
	action = "store_true",
)

args = parser.parse_args()

def printVerbose( message ) :

	if args.verbose :
		print( message )

def formatSize( bytes ) :

	return "{:.3f}Mb".format( bytes / ( 1024 * 1024. ) )

# Find all files and get their total size.

CacheEntry = collections.namedtuple( "CacheEntry", [ "file", "size", "mtime" ] )

totalSize = 0
cacheEntries = []

for root, dirs, files in os.walk( args.directory ) :
	for file in files :
		fileName = os.path.join( root, file )
		size = os.path.getsize( fileName )
		totalSize += size
		cacheEntries.append(
			CacheEntry(
				fileName,
				size,
				os.path.getmtime( fileName ),
			)
		)

printVerbose(
	"Found {} files with a total size of {}".format(
		len( cacheEntries ), formatSize( totalSize )
	)
)

# Remove files, oldest first, until we're under the limit.

sizeLimit = args.megabytes * 1024 * 1024
if totalSize <= sizeLimit :
	printVerbose( "No deletions required" )
	sys.exit( 0 )

cacheEntries = sorted( cacheEntries, key = lambda x : x.mtime )
for c in cacheEntries :
	if totalSize < sizeLimit :
		break
	os.remove( c.file )
	printVerbose( "Removed {}".format( c.file ) )
	totalSize -= c.size

printVerbose( "Reduced directory size to {}".format( formatSize( totalSize ) ) )

