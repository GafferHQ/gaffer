##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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
import GafferScene
import GafferSceneTest

class CopyPrimitiveVariablesTest( GafferSceneTest.SceneTestCase ) :

	def testConstantVariables( self ) :

		sphere = GafferScene.Sphere()
		sphere["name"].setValue( "object" )

		cube = GafferScene.Cube()
		cube["name"].setValue( "object" )

		cubeVariables = GafferScene.PrimitiveVariables()
		cubeVariables["in"].setInput( cube["out"] )
		cubeVariables["primitiveVariables"].addChild( Gaffer.NameValuePlug( "ten", IECore.IntData( 10 ) ) )
		cubeVariables["primitiveVariables"].addChild( Gaffer.NameValuePlug( "twenty", IECore.IntData( 20 ) ) )

		copy = GafferScene.CopyPrimitiveVariables()
		copy["in"].setInput( sphere["out"] )
		copy["source"].setInput( cubeVariables["out"] )

		# Not filtered to anything, so should be a perfect pass through.

		self.assertScenesEqual( sphere["out"], copy["out"] )
		self.assertSceneHashesEqual( sphere["out"], copy["out"] )

		# Add a filter, should still be a pass through because we haven't
		# asked for any variables to be copied.

		objectFilter = GafferScene.PathFilter()
		objectFilter["paths"].setValue( IECore.StringVectorData( [ "/object" ] ) )
		copy["filter"].setInput( objectFilter["out"] )

		self.assertScenesEqual( sphere["out"], copy["out"] )

		# Copy something that doesn't exist. This isn't an error, because the
		# variables are treated as match patterns.

		copy["primitiveVariables"].setValue( "these don't exist" )
		self.assertScenesEqual( sphere["out"], copy["out"] )

		# Copy things that do exist, and check that it has worked.

		copy["primitiveVariables"].setValue( "ten twenty" )
		self.assertEqual(
			set( copy["out"].object( "/object" ).keys() ),
			set( sphere["out"].object( "/object" ).keys() ) | { "ten", "twenty" },
		)

		self.assertEqual(
			copy["out"].object( "/object" )["ten"],
			cubeVariables["out"].object( "/object" )["ten"],
		)

		self.assertEqual(
			copy["out"].object( "/object" )["twenty"],
			cubeVariables["out"].object( "/object" )["twenty"],
		)

		# Check that wildcards work

		copy["primitiveVariables"].setValue( "twen*" )
		self.assertEqual(
			set( copy["out"].object( "/object" ).keys() ),
			set( sphere["out"].object( "/object" ).keys() ) | { "twenty" },
		)

	def testInterpolatedVariables( self ) :

		littleSphere = GafferScene.Sphere()

		bigSphere = GafferScene.Sphere()
		bigSphere["radius"].setValue( 10 )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		copy = GafferScene.CopyPrimitiveVariables()
		copy["in"].setInput( littleSphere["out"] )
		copy["source"].setInput( bigSphere["out"] )
		copy["filter"].setInput( sphereFilter["out"] )

		self.assertScenesEqual( copy["out"], littleSphere["out"] )

		copy["primitiveVariables"].setValue( "*" )

		self.assertScenesEqual( copy["out"], bigSphere["out"] )

		# If the spheres have differing topologies, then we can't copy
		# and should get an error.

		bigSphere["divisions"][0].setValue( 100 )

		with self.assertRaisesRegex( RuntimeError, 'Cannot copy .* from "/sphere" to "/sphere" because source and destination primitives have different topology' ) :
			copy["out"].object( "/sphere" )

	def testMismatchedHierarchy( self ) :

		sphere = GafferScene.Sphere()
		cube = GafferScene.Cube()

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		copy = GafferScene.CopyPrimitiveVariables()
		copy["in"].setInput( sphere["out"] )
		copy["source"].setInput( cube["out"] )
		copy["filter"].setInput( sphereFilter["out"] )
		copy["primitiveVariables"].setValue( "*" )

		self.assertEqual( copy["out"].object( "/sphere" ), copy["in"].object( "/sphere" ) )

	def testSourceLocation( self ) :

		sphere1 = GafferScene.Sphere()

		sphere2 = GafferScene.Sphere()
		sphere2["radius"].setValue( 2 )

		sphere3 = GafferScene.Sphere()
		sphere3["radius"].setValue( 3 )

		group = GafferScene.Group()
		group["in"][0].setInput( sphere2["out"] )
		group["in"][1].setInput( sphere3["out"] )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		copy = GafferScene.CopyPrimitiveVariables()
		copy["in"].setInput( sphere1["out"] )
		copy["source"].setInput( group["out"] )
		copy["filter"].setInput( sphereFilter["out"] )
		copy["primitiveVariables"].setValue( "P" )

		copy["sourceLocation"].setValue( "/group/sphere" )
		self.assertEqual( copy["out"].object( "/sphere" )["P"], group["out"].object( "/group/sphere" )["P"] )

		copy["sourceLocation"].setValue( "/group/sphere1" )
		self.assertEqual( copy["out"].object( "/sphere" )["P"], group["out"].object( "/group/sphere1" )["P"] )

		# Copying from a non-existing location should be a no-op

		copy["sourceLocation"].setValue( "/road/to/nowhere" )
		self.assertScenesEqual( copy["out"], sphere1["out"] )

	def testBoundUpdate( self ) :

		sphere1 = GafferScene.Sphere()
		sphere2 = GafferScene.Sphere()
		sphere2["radius"].setValue( 2 )

		group = GafferScene.Group()
		group["in"][0].setInput( sphere1["out"] )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )

		copy = GafferScene.CopyPrimitiveVariables()
		copy["in"].setInput( group["out"] )
		copy["source"].setInput( sphere2["out"] )
		copy["filter"].setInput( sphereFilter["out"] )
		copy["sourceLocation"].setValue( "/sphere" )
		copy["primitiveVariables"].setValue( "P" )

		# We're copying "P", so the bounds need updating.

		self.assertEqual( copy["out"].object( "/group/sphere" )["P"], sphere2["out"].object( "/sphere" )["P"] )
		self.assertSceneValid( copy["out"] )
		self.assertEqual( copy["out"].bound( "/" ), sphere2["out"].bound( "/" ) )
		self.assertEqual( copy["out"].bound( "/group" ), sphere2["out"].bound( "/" ) )
		self.assertEqual( copy["out"].bound( "/group/sphere" ), sphere2["out"].bound( "/" ) )

		# If we turn off "adjustBounds", we want a perfect pass through of the input
		# bounds.

		copy["adjustBounds"].setValue( False )
		self.assertScenesEqual( copy["out"], group["out"], checks = { "bound" } )
		self.assertSceneHashesEqual( copy["out"], group["out"], checks = { "bound" } )

		# If "adjustBounds" is on, but "P" isn't being copied, we also want
		# a perfect pass through of the input bounds. We don't want to pay for
		# unnecessary bounds propagation.

		copy["adjustBounds"].setValue( True )
		copy["primitiveVariables"].setValue( "uv" )
		self.assertScenesEqual( copy["out"], group["out"], checks = { "bound" } )
		self.assertSceneHashesEqual( copy["out"], group["out"], checks = { "bound" } )

	def testDeleteSourceLocation( self ) :

		sphere1 = GafferScene.Sphere()
		sphere2 = GafferScene.Sphere()
		sphere2["radius"].setValue( 2 )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		prune = GafferScene.Prune()
		prune["in"].setInput( sphere2["out"] )

		copy = GafferScene.CopyPrimitiveVariables()
		copy["in"].setInput( sphere1["out"] )
		copy["source"].setInput( prune["out"] )
		copy["filter"].setInput( sphereFilter["out"] )
		copy["primitiveVariables"].setValue( "*" )

		self.assertScenesEqual( copy["out"], sphere2["out"] )
		prune["filter"].setInput( sphereFilter["out"] )
		self.assertScenesEqual( copy["out"], sphere1["out"] )

	def testPrefix( self ) :

		sphere1 = GafferScene.Sphere()
		sphere2 = GafferScene.Sphere()
		sphere2["radius"].setValue( 2 )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		copy = GafferScene.CopyPrimitiveVariables()
		copy["in"].setInput( sphere1["out"] )
		copy["source"].setInput( sphere2["out"] )
		copy["filter"].setInput( sphereFilter["out"] )
		copy["primitiveVariables"].setValue( "*" )

		# Unprefixed

		self.assertScenesEqual( copy["out"], sphere2["out"] )

		# Prefixed

		copy["prefix"].setValue( "copied:" )

		self.assertEqual(
			copy["out"].object( "/sphere")["P"],
			sphere1["out"].object( "/sphere")["P"],
		)

		self.assertEqual(
			copy["out"].object( "/sphere")["copied:P"],
			sphere2["out"].object( "/sphere")["P"],
		)

		for location in ( "/", "/sphere" ) :

			self.assertEqual(
				copy["out"].bound( location ),
				sphere1["out"].bound( location )
			)

			self.assertEqual(
				copy["out"].boundHash( location ),
				sphere1["out"].boundHash( location )
			)

if __name__ == "__main__":
	unittest.main()
