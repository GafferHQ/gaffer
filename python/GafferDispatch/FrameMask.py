##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferDispatch

class FrameMask( GafferDispatch.TaskNode ) :

	def __init__( self, name = "FrameMask" ) :

		GafferDispatch.TaskNode.__init__( self, name )
		self["mask"] = Gaffer.StringPlug()

	def preTasks( self, context ) :

		frames = _frameListCache.get( self["mask"].getValue() )
		if ( not frames ) or ( context.getFrame() in frames ) :
			return GafferDispatch.TaskNode.preTasks( self, context )
		else :
			return []

	def hash( self, context ) :

		return IECore.MurmurHash()

	def execute( self ) :

		pass

IECore.registerRunTimeTyped( FrameMask, typeName = "GafferDispatch::FrameMask" )

# We cache the results of `FrameList.asList()` as a set, to avoid regenerating
# it on every frame, and to avoid linear search in `FrameMask.preTasks()`. This
# gives substantial performance improvements when dispatching large frame
# ranges.
def __frameListCacheGetter( frameExpression ) :

	frames = IECore.FrameList.parse( frameExpression ).asList()
	return set( frames ), len( frames )

# Enough for approximately an hour's worth of frames, at a cost of < 10Mb.
_frameListCache = IECore.LRUCache( __frameListCacheGetter, 100000 )
