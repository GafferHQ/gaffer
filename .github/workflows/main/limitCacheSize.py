import os
import collections

# GitHub has a limit of 5G for all caches in a repository. Because we both read
# from and write to `.sconsCache`, it would quickly grow to exceed this limit if
# left unchecked. This script limits the cache size to avoid unbounded growth.

# 2.5G. This is roughly the right size to hold a single debug build, which is
# extremely bloated compared to a regular release build. In practice, the actual
# GitHub quota used is much lower, because GitHub compresses all files into a
# single archive before uploading them.
sizeLimit = 2.5 * 1024 * 1024 * 1024

CacheEntry = collections.namedtuple( "CacheEntry", [ "file", "size", "mtime" ] )

totalSize = 0
cacheEntries = []

for root, dirs, files in os.walk( "./sconsCache" ) :
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

cacheEntries = sorted( cacheEntries, key = lambda x : x.mtime )
for c in cacheEntries :
	if totalSize < sizeLimit :
		break
	os.remove( c.file )
	print( "REMOVING", c.file )
	totalSize -= c.size
