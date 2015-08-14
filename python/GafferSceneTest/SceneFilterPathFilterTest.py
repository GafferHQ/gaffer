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

import unittest

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class SceneFilterPathFilterTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		camera = GafferScene.Camera()
		plane = GafferScene.Plane()
		group = GafferScene.Group()
		group["in"][0].setInput( camera["out"] )
		group["in"][1].setInput( plane["out"] )

		path = GafferScene.ScenePath( group["out"], Gaffer.Context(), "/group" )
		self.assertEqual( set( [ str( c ) for c in path.children() ] ), { "/group/camera", "/group/plane" } )

		setFilter = GafferScene.SetFilter()
		setFilter["set"].setValue( "__cameras" )
		pathFilter = GafferScene.SceneFilterPathFilter( setFilter )

		path.setFilter( pathFilter )
		self.assertEqual( set( [ str( c ) for c in path.children() ] ), { "/group/camera" } )

		cs = GafferTest.CapturingSlot( pathFilter.changedSignal() )

		setFilter["set"].setValue( "" )
		self.assertEqual( len( cs ), 1 )
		self.assertEqual( path.children(), [] )

	def testManyPaths( self ) :

		plane = GafferScene.Plane()
		plane["divisions"].setValue( IECore.V2i( 500 ) )

		sphere = GafferScene.Sphere()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["parent"].setValue( "/plane" )
		instancer["instance"].setInput( sphere["out"] )

		scenePathFilter = GafferScene.PathFilter()
		scenePathFilter["paths"].setValue( IECore.StringVectorData( [ "/plane/instances/*" ] ) )

		path = GafferScene.ScenePath(
			instancer["out"],
			Gaffer.Context(),
			"/plane/instances",
			GafferScene.SceneFilterPathFilter( scenePathFilter )
		)

		t = IECore.Timer()
		self.assertEqual( len( path.children() ), 251001 )

		# This test can be useful when benchmarking SceneFilterPathFilter
		# performance. Uncomment to get timing information.
		# print t.stop()

if __name__ == "__main__":
	unittest.main()
