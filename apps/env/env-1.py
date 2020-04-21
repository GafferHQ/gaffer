##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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
import sys
import subprocess

import IECore

import Gaffer

class env( Gaffer.Application ) :

	def __init__( self ) :

		Gaffer.Application.__init__(
			self,
			"""
			Runs shell commands in the Gaffer environment
			(after the Gaffer wrapper has been run), so they have access
			to all the libraries and modules available within Gaffer.

			This is useful for running the binary utilities supplied with Gaffer,
			or for running python scripts which need to import Gaffer's python
			modules.

			Usage :

			```
			gaffer env [name=value ...] [utility [argument ...]]
			```

			Examples :

			```
			gaffer env maketx input.exr
			gaffer env python script.py
			```
			"""
		)

		self.parameters().addParameters(

			[
				IECore.StringVectorParameter(
					name = "arguments",
					description = "A series of optional name=value environment variable specifications, followed by the command to execute.",
					defaultValue = IECore.StringVectorData(),
					userData = {
						"parser" : {
							"acceptFlags" : IECore.BoolData( True ),
						},
					},
				),
			]

		)

		self.parameters().userData()["parser"] = IECore.CompoundObject(
			{
				"flagless" : IECore.StringVectorData( [ "arguments" ] )
			}
		)

	def _run( self, args ) :

		# get environment

		env = os.environ.copy()
		i = 0
		while i < len( args["arguments"] ) :
			s = args["arguments"][i].split( "=" )
			if len( s ) > 1 :
				env[s[0]] = "=".join( s[1:] )
				i += 1
			else :
				break

		# run command or print env if no command

		command = list( args["arguments"][i:] )
		if command :
			try :
				return subprocess.call( command, env=env )
			except OSError as e :
				sys.stderr.write( "gaffer env : %s : %s\n" % ( " ".join( command ), e.strerror ) )
				return 1
		else :
			for key in sorted( env.keys() ) :
				sys.stdout.write( "%s=%s\n" % ( key, env[key] ) )
			return 0

IECore.registerRunTimeTyped( env )
