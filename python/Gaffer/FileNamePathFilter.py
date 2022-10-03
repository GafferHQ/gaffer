##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

import fnmatch
import re

import IECore

import Gaffer

## A PathFilter which filters based on filename.
## \deprecated Use MatchPatternPathFilter instead.
class FileNamePathFilter( Gaffer.PathFilter ) :

	## Matchers is a list of compiled regular expressions and/or
	# shell style pattern strings. The latter will be compiled
	# into regular expressions using fnmatch.translate().
	# The resulting filter will pass through any path whose
	# name matches one or more of the regular expressions. If filterLeafOnly
	# is True then directories will always be passed through.
	def __init__( self, matchers, leafOnly=True, userData={} ) :

		assert( isinstance( matchers, ( list, tuple ) ) )

		Gaffer.PathFilter.__init__( self, userData )

		self.__matchers = []
		for m in matchers :

			if isinstance( m, str ) :
				self.__matchers.append( re.compile( fnmatch.translate( m ) ) )
			else :
				assert( type( m ) is type( re.compile( "" ) ) )
				self.__matchers.append( m )

		self.__leafOnly = leafOnly

	def _filter( self, paths, canceller ) :

		result = []
		for p in paths :
			if len( p ) :
				if self.__leafOnly and not p.isLeaf() :
					result.append( p )
				else :
					for m in self.__matchers :
						if m.match( p[-1] ) :
							result.append( p )
							break

		return result

IECore.registerRunTimeTyped( FileNamePathFilter, typeName = "Gaffer::FileNamePathFilter" )
