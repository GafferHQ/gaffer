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
import IECoreAlembic

class abcToMDC( IECore.Op ) :

	def __init__( self ) :
	
		IECore.Op.__init__( self, "Makes model caches out of alembic caches.", IECore.FileNameParameter( "result", "" ) )
		
		self.parameters().addParameters(
			
			[
				IECore.FileNameParameter(
					"inputFile",
					"The alembic file to be converted.",
					defaultValue = "",
					allowEmptyString = False,
					check = IECore.FileNameParameter.CheckType.MustExist,
					extensions = "abc",
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
	
		inFile = IECoreAlembic.AlembicInput( args["inputFile"].value )
		outFile = IECore.FileIndexedIO( args["outputFile"].value, "/", IECore.IndexedIOOpenMode.Write )
		
		header = IECore.HeaderGenerator.header()
		header.save( outFile, "header" )
		
		outFile.mkdir( "root" )
		outFile.chdir( "root" )
		
		def walk( a ) :
		
			b = a.bound()
			outFile.write(
				"bound",
				IECore.FloatVectorData( [
					b.min.x, b.min.y, b.min.z,
					b.max.x, b.max.y, b.max.z,
				] )
			)
			
			o = a.convert( IECore.Primitive.staticTypeId() )
			if o is not None :
				## \todo Rename "geometry" to "object"
				o.save( outFile, "geometry" )
				
			t = a.transform()
			outFile.write(
				"transform",
				IECore.FloatVectorData( [
					t[0,0], t[0,1], t[0,2], t[0,3],
					t[1,0], t[1,1], t[1,2], t[1,3],
					t[2,0], t[2,1], t[2,2], t[2,3],
					t[3,0], t[3,1], t[3,2], t[3,3],
				] )
			)
			
			numChildren = a.numChildren()
			if numChildren :
				outFile.mkdir( "children" )
				outFile.chdir( "children" )
				for i in range( 0, numChildren ) :
					child = a.child( i )
					outFile.mkdir( child.name() )
					outFile.chdir( child.name() )
					walk( child )
					outFile.chdir( ".." )
				outFile.chdir( ".." )
					
		walk( inFile )	
		
		return args["outputFile"].value
			
IECore.registerRunTimeTyped( abcToMDC )