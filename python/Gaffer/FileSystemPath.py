##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

import os
import re
import pwd
import grp

import Gaffer

class FileSystemPath( Gaffer.Path ) :

	def __init__( self, path=None, root="/", filter=None ) :

		Gaffer.Path.__init__( self, path, root, filter )

	def isValid( self ) :

		return Gaffer.Path.isValid( self ) and os.path.lexists( str( self ) )

	def isLeaf( self ) :

		return self.isValid() and not os.path.isdir( str( self ) )

	def info( self ) :

		result = Gaffer.Path.info( self )
		if result is None :
			return None

		pathString = str( self )
		try :
			# if s is a symlink, this gets the information from
			# the pointed-to file, failing if it doesn't exist.
			s = os.stat( pathString )
		except OSError :
			# if a symlink was broken then we fall back to
			# getting information from the link itself.
			s = os.lstat( pathString )
		try :
			p = pwd.getpwuid( s.st_uid )
		except :
			p = None
		try :
			g = grp.getgrgid( s.st_gid )
		except :
			g = None

		result["fileSystem:owner"] = p.pw_name if p is not None else ""
		result["fileSystem:group"] = g.gr_name if g is not None else ""
		result["fileSystem:modificationTime"] = s.st_mtime
		result["fileSystem:accessTime"] = s.st_atime
		result["fileSystem:size"] = s.st_size

		return result

	def _children( self ) :

		try :
			c = os.listdir( str( self ) )
		except :
			return []

		return [ FileSystemPath( self[:] + [ x ], self.root() ) for x in c ]

	@staticmethod
	def createStandardFilter( extensions=[], extensionsLabel=None ) :

		result = Gaffer.CompoundPathFilter()

		if extensions :
			extensions = [ e.lower() for e in extensions ]
			if extensionsLabel is None :
				extensionsLabel = "Show only " + ", ".join( [ "." + e for e in extensions ] ) + " files"
			extensions += [ e.upper() for e in extensions ]
			extensions = [ "*." + e for e in extensions ]
			# the form below is for file sequences, where the frame range will
			# come after the extension
			extensions += [ "*.%s *" % e for e in extensions ]
			result.addFilter(
				Gaffer.FileNamePathFilter(
					extensions,
					userData = {
						"UI" : {
							"label" : extensionsLabel,
						}
					}
				)
			)

		result.addFilter(
			Gaffer.FileNamePathFilter(
				[ re.compile( "^[^.].*" ) ],
				leafOnly=False,
				userData = {
					"UI" : {
						"label" : "Show hidden files",
						"invertEnabled" : True,
					}
				}
			)
		)

		result.addFilter(
			Gaffer.InfoPathFilter(
				infoKey = "name",
				matcher = None, # the ui will fill this in
				leafOnly = False,
			)
		)

		return result
