##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

import sys
import os

import IECore

import Gaffer

class license( Gaffer.Application ) :

	def __init__( self ) :
	
		Gaffer.Application.__init__( self )
		
		self.parameters().addParameter(
		
			IECore.BoolParameter(
				name = "withDependencies",
				description = "Display the copyright and licensing information for the dependencies.",
				defaultValue = True
			)		
		
		)
		
	def doRun( self, args ) :

		sys.stderr.write( Gaffer.About.name() + " " + Gaffer.About.versionString() + "\n" )
		sys.stderr.write( Gaffer.About.copyright() + "\n" )
		sys.stderr.write( Gaffer.About.url() + "\n" )
		
		if args["withDependencies"].value :
			sys.stderr.write( "\n" + Gaffer.About.dependenciesPreamble() + "\n" )
			for d in Gaffer.About.dependencies() :
		
				sys.stderr.write( "\n" + d["name"] + "\n" )
				sys.stderr.write( "-" * len( d["name"] ) + "\n\n" )

				if "credit" in d :
					sys.stderr.write( d["credit"] + "\n" )
				if "url" in d :
					sys.stderr.write( "Project URL : " + d["url"] + "\n" )
				if "license" in d :
					sys.stderr.write( "License : %s\n" % os.path.expandvars( d["license"] ) )
				if "source" in d :
					sys.stderr.write( "Source : %s\n" % os.path.expandvars( d["source"] ) )
			
		return 0

IECore.registerRunTimeTyped( license )
