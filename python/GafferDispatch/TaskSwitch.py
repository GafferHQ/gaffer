##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

## \deprecated Use `Gaffer.Switch` instead.
# \todo Move to a compatibility config, perhaps reimplemented
# as a Switch node embedded inside a TaskNode.
class TaskSwitch( GafferDispatch.TaskNode ) :

	def __init__( self, name = "TaskSwitch" ) :

		GafferDispatch.TaskNode.__init__( self, name )

		self["index"] = Gaffer.IntPlug( minValue = 0 )

	def preTasks( self, context ) :

		index = self["index"].getValue()
		index = index % ( len( self["preTasks"] ) - 1 )
		return [ self.Task( self["preTasks"][index], context ) ]

	def hash( self, context ) :

		# Our hash is empty to signify that we don't do
		# anything in execute().
		return IECore.MurmurHash()

	def execute( self ) :

		# We don't need to do anything here because our
		# sole purpose is to determine which upstream
		# node is executed.
		pass

IECore.registerRunTimeTyped( TaskSwitch, typeName = "GafferDispatch::TaskSwitch" )
