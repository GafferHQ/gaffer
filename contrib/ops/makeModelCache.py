##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import glob

import IECore

class makeModelCache( IECore.Op ) :

	def __init__( self ) :
	
		IECore.Op.__init__( self, "Makes model caches out of arbitrary lists of geometry files.", IECore.FileNameParameter( "result", "" ) )
		
		self.parameters().addParameters(
			
			[
				IECore.PathVectorParameter(
					"inputPaths",
					"A list of files and/or directories containing geometry to be merged into the model cache.",
					defaultValue = IECore.StringVectorData(),
				),
				IECore.FileNameParameter(
					"outputFile",
					"The filename of the model cache to be written",
					defaultValue = "",
					allowEmptyString = False,
				),
			],
			
		)

	def doOperation( self, args ) :
	
		files = []
		for path in args["inputPaths"] :
		
			if os.path.isfile( path ) :
				files.append( path )
			elif os.path.isdir( path ) :
				files.extend( glob.glob( path + "/*.cob" ) )
				
		if not files :
			raise Exception( "No valid files found" )
			
		outFile = IECore.ModelCache( args["outputFile"].value, IECore.IndexedIOOpenMode.Write )
		
		for f in files :
		
			reader = None
			with IECore.IgnoredExceptions( RuntimeError ) :
				reader = IECore.Reader.create( f )
			
			if reader is None :
				continue
				
			o = None
			with IECore.IgnoredExceptions( RuntimeError ) :
				o = reader.read()
				
			if not isinstance( o, IECore.Primitive ) :
				continue
			
			name = os.path.splitext( os.path.basename( f ) )[0]
			
			child = outFile.writableChild( name )
			child.writeObject( o )
	
		return args["outputFile"].value
			
IECore.registerRunTimeTyped( makeModelCache )