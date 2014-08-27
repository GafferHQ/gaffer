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

import unittest

import IECore

import GafferScene
import GafferSceneTest

class SceneAlgoTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		sphere = GafferScene.Sphere()
		plane = GafferScene.Plane()
		group = GafferScene.Group()
		group["in"].setInput( sphere["out"] )
		group["in1"].setInput( plane["out"] )

		plane2 = GafferScene.Plane()
		plane2["divisions"].setValue( IECore.V2i( 99, 99 ) ) # 10000 instances

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane2["out"] )
		instancer["parent"].setValue( "/plane" )
		instancer["instance"].setInput( group["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane/instances/*1/group/plane" ] ) )

		matchingPaths = GafferScene.PathMatcher()
		GafferScene.matchingPaths( filter, instancer["out"], matchingPaths )

		self.assertEqual( len( matchingPaths.paths() ), 1000 )
		self.assertEqual( matchingPaths.match( "/plane/instances/1/group/plane" ), GafferScene.Filter.Result.ExactMatch )
		self.assertEqual( matchingPaths.match( "/plane/instances/1121/group/plane" ), GafferScene.Filter.Result.ExactMatch )
		self.assertEqual( matchingPaths.match( "/plane/instances/1121/group/sphere" ), GafferScene.Filter.Result.NoMatch )

	def testExists( self ) :

		sphere = GafferScene.Sphere()
		plane = GafferScene.Plane()
		group = GafferScene.Group()
		group["in"].setInput( sphere["out"] )
		group["in1"].setInput( plane["out"] )

		self.assertTrue( GafferScene.exists( group["out"], "/" ) )
		self.assertTrue( GafferScene.exists( group["out"], "/group" ) )
		self.assertTrue( GafferScene.exists( group["out"], "/group/sphere" ) )
		self.assertTrue( GafferScene.exists( group["out"], "/group/plane" ) )

		self.assertFalse( GafferScene.exists( group["out"], "/a" ) )
		self.assertFalse( GafferScene.exists( group["out"], "/group2" ) )
		self.assertFalse( GafferScene.exists( group["out"], "/group/sphere2" ) )
		self.assertFalse( GafferScene.exists( group["out"], "/group/plane/child" ) )

if __name__ == "__main__":
	unittest.main()

