##########################################################################
#
#  Copyright (c) 2019, Don Boogert. All rights reserved.
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
#      * Neither the name of Don Boogert nor the names of
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

import unittest

import IECore
import IECoreScene
import IECoreVDB

import Gaffer
import GafferTest
import GafferScene
import GafferVDB
import GafferVDBTest
import GafferOSL


class OSLVDBTest( GafferVDBTest.VDBTestCase ) :

	def setUp( self ) :

		GafferVDBTest.VDBTestCase.setUp( self )
		self.sourcePath = os.path.join( self.dataDir, "smoke.vdb" )

	def testCanReadAndWriteScalarGrid( self ) :

		sceneReader = GafferScene.SceneReader( "SceneReader" )
		sceneReader["fileName"].setValue( self.sourcePath )

		inFloat = GafferOSL.OSLShader( "InFloat" )
		inFloat.loadShader( "ObjectProcessing/InFloat" )
		inFloat["parameters"]["name"].setValue( 'density' )

		oslCode =  GafferOSL.OSLCode( "OSLCode" )
		oslCode["code"].setValue( 'outT = inT * 2.0;' )
		oslCode["parameters"].addChild( Gaffer.FloatPlug( "inT", defaultValue = 0.0 ) )
		oslCode["out"].addChild( Gaffer.FloatPlug( "outT", direction = Gaffer.Plug.Direction.Out, defaultValue = 0.0) )

		outFloat = GafferOSL.OSLShader( "OutFloat" )
		outFloat.loadShader( "ObjectProcessing/OutFloat" )
		outFloat["parameters"]["name"].setValue( 'density' )

		outObject = GafferOSL.OSLShader( "OutObject" )
		outObject.loadShader( "ObjectProcessing/OutObject" )

		oslVdb = GafferOSL.OSLVDB( "OSLVDB" )
		oslVdb["in"].setInput( sceneReader["out"] )
		oslVdb["grid"].setValue( 'density' )

		filter =  GafferScene.PathFilter( "PathFilter" )
		filter["paths"].setValue( IECore.StringVectorData( [ '/vdb' ] ) )

		oslVdb["in"].setInput( sceneReader["out"] )

		oslVdb["filter"].setInput( filter["out"] )
		oslVdb["shader"].setInput( outObject["out"] )

		outObject["parameters"]["in0"].setInput( outFloat["out"]["primitiveVariable"] )
		outFloat["parameters"]["value"].setInput( oslCode["out"]["outT"] )

		oslCode["parameters"]["inT"].setInput( inFloat["out"]["value"] )

		originalVDB = sceneReader["out"].object( "/vdb" )
		originalGrid = originalVDB.findGrid( "density" )

		updatedVDB = oslVdb["out"].object( "/vdb" )
		updatedGrid = updatedVDB.findGrid( "density" )

		def gridValues(grid, numElements = 10) :

			values = []
			i = 0
			for c in grid.iterOnValues():

				values.append( c['value'] )
				if i == numElements:
					break

				i += 1

			return values

		for a,b in zip( gridValues( originalGrid ) , gridValues( updatedGrid ) ):
			self.assertAlmostEqual( a * 2.0, b)


if __name__ == "__main__":
	unittest.main()
