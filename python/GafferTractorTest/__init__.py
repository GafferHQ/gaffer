##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

__mockAPI = None

# Testing replacement for `GafferTractor.tractorAPI()`. This returns
# the same `tractor.api.author` module if it is available, but otherwise
# returns a mock module sufficient for running the unit tests without
# Tractor present.
def tractorAPI() :

	import types
	import IECore

	# Use the real API if it is available.

	with IECore.IgnoredExceptions( ImportError ) :
		from tractor.api.author import author
		return author

	# Otherwise build mock version. The goal here is not to emulate the whole
	# Tractor API, but to provide the bare minimum needed to run the unit tests.

	global __mockAPI
	if __mockAPI is not None :
		return __mockAPI

	class TaskBased :

		def __init__( self, **kw ) :

			for key, value in kw.items() :
				setattr( self, key, value )

			self.subtasks = []

		def addChild( self, task ) :

			if task.parent is None :
				self.subtasks.append( task )
				task.parent = self
			else :
				self.subtasks.append( Instance( title = task.title ) )

	class Job( TaskBased ) :

		__slots__ = [ "title", "service", "envkey" ]

		def asTcl( self ) :

			return "# Mock serialisation"

		def spool( self, block = False ) :

			pass

	class Task( TaskBased ) :

		__slots__ = [ "title", "service", "envkey", "parent" ]

		def __init__( self, **kw ) :

			TaskBased.__init__( self, **kw )
			self.cmds = []
			self.parent = None

		def addCommand( self, command ) :

			self.cmds.append( command )

	class Instance :

		__slots__ = [ "title" ]

		def __init__( self, title ) :

			self.title = title

	class Command :

		__slots__ = [ "argv", "service", "tags" ]

		def __init__( self, **kw ) :

			for key, value in kw.items() :
				setattr( self, key, value )

	__mockAPI = types.ModuleType( "author" )
	__mockAPI.Job = Job
	__mockAPI.Task = Task
	__mockAPI.Instance = Instance
	__mockAPI.Command = Command

	return __mockAPI

from .TractorDispatcherTest import TractorDispatcherTest
from .ModuleTest import ModuleTest

if __name__ == "__main__":
	import unittest
	unittest.main()
