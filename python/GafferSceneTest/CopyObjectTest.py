##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

import imath

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class CopyObjectTest( GafferSceneTest.SceneTestCase ) :

	def testCopy( self ) :

		sphere = GafferScene.Sphere()
		sphere["name"].setValue( "object" )

		cube = GafferScene.Cube()
		cube["name"].setValue( "object" )

		copy = GafferScene.CopyObject()
		copy["in"].setInput( sphere["out"] )
		copy["source"].setInput( cube["out"] )

		# Not filtered to anything, so should be a perfect pass through.

		self.assertScenesEqual( copy["out"], sphere["out"]  )
		self.assertSceneHashesEqual( copy["out"], sphere["out"] )

		# Add a filter, and we should get the object copied.

		objectFilter = GafferScene.PathFilter()
		objectFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )
		copy["filter"].setInput( objectFilter["out"] )

		self.assertEqual( copy["out"].object( "/object" ), cube["out"].object( "/object" ) )
		self.assertSceneValid( copy["out"] )

		# Request to copy from a location that doesn't exist, and
		# we should get a pass-through again.

		copy["sourceLocation"].setValue( "/cube" )
		self.assertScenesEqual( copy["out"], sphere["out"]  )
		self.assertSceneHashesEqual( copy["out"], sphere["out"] )

		# Make the path valid, and the object should be copied again.

		cube["name"].setValue( "cube" )
		self.assertEqual( copy["out"].object( "/object" ), cube["out"].object( "/cube" ) )
		self.assertSceneValid( copy["out"] )

	def testInputObjectNotComputed( self ) :

		sphere = GafferScene.Sphere()
		cube = GafferScene.Cube()

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		copy = GafferScene.CopyObject()
		copy["in"].setInput( sphere["out"] )
		copy["source"].setInput( cube["out"] )
		copy["filter"].setInput( sphereFilter["out"] )
		copy["sourceLocation"].setValue( "/cube" )

		with Gaffer.PerformanceMonitor() as pm :
			copy["out"].object( "/sphere" )

		# The `copy` node will have done a compute, triggering a compute on the
		# `cube` node.

		self.assertEqual( pm.plugStatistics( copy["out"]["object"] ).hashCount, 1 )
		self.assertEqual( pm.plugStatistics( copy["out"]["object"] ).computeCount, 1 )
		self.assertEqual( pm.plugStatistics( cube["out"]["object"] ).hashCount, 1 )
		self.assertEqual( pm.plugStatistics( cube["out"]["object"] ).computeCount, 1 )

		# But there should be no compute triggered for the input `sphere` scene, since
		# the object is being replaced completely.

		self.assertEqual( pm.plugStatistics( sphere["out"]["object"] ).hashCount, 0 )
		self.assertEqual( pm.plugStatistics( sphere["out"]["object"] ).computeCount, 0 )

	def testBoundsUpdate( self ) :

		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )

		cube = GafferScene.Cube()
		cube["dimensions"].setValue( imath.V3f( 10, 11, 12 ) )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )

		copy = GafferScene.CopyObject()
		copy["in"].setInput( group["out"] )
		copy["source"].setInput( cube["out"] )
		copy["filter"].setInput( sphereFilter["out"] )
		copy["sourceLocation"].setValue( "/cube" )

		self.assertEqual( copy["out"].bound( "/" ), copy["in"].bound( "/" ) )

		copy["adjustBounds"].setValue( True )
		self.assertEqual( copy["out"].bound( "/" ), cube["out"].bound( "/" ) )
		self.assertEqual( copy["out"].bound( "/group" ), cube["out"].bound( "/" ) )
		self.assertEqual( copy["out"].bound( "/group/sphere" ), cube["out"].bound( "/" ) )

if __name__ == "__main__":
	unittest.main()
