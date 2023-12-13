##########################################################################
#
#  Copyright (c) 2023, John Haddon. All rights reserved.
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

import Gaffer
import GafferImage

class __ChannelPlug( Gaffer.ShufflePlug ) :

	def __init__( self, *args, **kw ) :

		if (
			len( kw ) == 0 and len( args ) == 2
			and isinstance( args[0], str ) and isinstance( args[1], str )
		) :
			Gaffer.ShufflePlug.__init__( self, args[1], args[0] )
		else :
			Gaffer.ShufflePlug.__init__( self, *args, **kw )

GafferImage.Shuffle.ChannelPlug = __ChannelPlug

def __shufflePlugGetItem( originalGetItem ) :

	def getItem( self, key ) :

		if key == "in" :
			key = "source"
		elif key == "out" :
			key = "destination"

		return originalGetItem( self, key )

	return getItem

Gaffer.ShufflePlug.__getitem__ = __shufflePlugGetItem( Gaffer.ShufflePlug.__getitem__ )

def __shuffleGetItem( originalGetItem ) :

	def getItem( self, key ) :

		if key == "channels" :
			key = "shuffles"

		return originalGetItem( self, key )

	return getItem

GafferImage.Shuffle.__getitem__ = __shuffleGetItem( GafferImage.Shuffle.__getitem__ )
