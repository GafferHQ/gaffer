##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import traceback
import sys
import six

import IECore
import Gaffer

class python( Gaffer.Application ) :

	def __init__( self ) :

		Gaffer.Application.__init__(
			self,
			"""
			Runs python scripts in an environment where all the
			Gaffer modules are available.

			> Caution : This application is deprecated.
			> Use `gaffer env python` instead.
			"""
		)

		self.parameters().addParameters(

			[

				IECore.FileNameParameter(
					name = "file",
					description = "The python script to execute",
					defaultValue = "",
					allowEmptyString = False,
					check = IECore.FileNameParameter.CheckType.MustExist,
				),

				IECore.StringVectorParameter(
					name = "arguments",
					description = "An arbitrary list of arguments which will be provided to "
						"the python script in a variable called argv.",
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
				"flagless" : IECore.StringVectorData( [ "file", "arguments" ] )
			}
		)

	def _run( self, args ) :

		# trying to set the sys.argv to the same values as we would expect from a python call
		#
		# the gaffer python command line syntax is expected to be:
		# gaffer python -file <script path> [-arguments <arguments>]
		#
		# given the limitations of the gaffer python app command line syntax, we can assume that the equivalent python command syntax would be:
		# python <script path> [<arguments>]
		#
		# python removes the "python" command from the start of the sys.argv list, making the first argument the script path
		# sys.argv should therefore be:
		# [<script path>] + [<arguments>]
		#
		# sys.argv is assumed to be the source of information for python argument parsing methods (argparse, getopt, ...)
		#
		# NOTE: this is not thread-safe
		# we could make it thread safe by using a mechanism similar to the one used by gaffer/python/Gaffer/OutputRedirection.py
		# but using that method, a generic python code could break if it was actually trying to alter a global sys.argv from a thread
		# however, since changing sys.argv is quite rare, and calling "gaffer python app" from a Thread is also a very unlikely scenario
		# we'll just leave it thread-unsafe for the moment

		origSysArgv = sys.argv
		try:
			sys.argv = [ args[ "file" ].value ] + list( args[ "arguments" ] )
			try :
				with open( args["file"].value ) as f :
					six.exec_(
						compile( f.read(), args["file"].value, "exec" ),
						{
							"argv" : args["arguments"],
							"__name__" : "__main__",
						}
					)
				return 0
			except SystemExit as e :
				# don't print traceback when a sys.exit was called, but return the exit code as the result
				return e.code
			except :
				traceback.print_exc()
				return 1
		finally:
			# restore sys.argv
			sys.argv = origSysArgv

IECore.registerRunTimeTyped( python )
