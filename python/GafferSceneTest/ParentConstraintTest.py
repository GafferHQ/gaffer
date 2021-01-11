##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import six

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class ParentConstraintTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		plane1 = GafferScene.Plane()
		plane1["transform"]["translate"].setValue( imath.V3f( 1, 2, 3 ) )
		plane1["transform"]["scale"].setValue( imath.V3f( 1, 2, 3 ) )
		plane1["transform"]["rotate"].setValue( imath.V3f( 1000, 20, 39 ) )
		plane1["name"].setValue( "target" )

		plane2 = GafferScene.Plane()
		plane2["name"].setValue( "constrained" )

		group = GafferScene.Group()
		group["in"][0].setInput( plane1["out"] )
		group["in"][1].setInput( plane2["out"] )

		self.assertSceneValid( group["out"] )

		constraint = GafferScene.ParentConstraint()
		constraint["target"].setValue( "/group/target" )
		constraint["in"].setInput( group["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/constrained" ] ) )
		constraint["filter"].setInput( filter["out"] )

		self.assertSceneValid( constraint["out"] )

		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ), group["out"].fullTransform( "/group/target" ) )

		# Test behaviour for missing target
		plane1["name"].setValue( "targetX" )
		with six.assertRaisesRegex( self, RuntimeError, 'ParentConstraint.out.transform : Constraint target does not exist: "/group/target"' ):
			constraint["out"].fullTransform( "/group/constrained" )

		constraint["ignoreMissingTarget"].setValue( True )
		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ), constraint["in"].fullTransform( "/group/constrained" ) )

		# Constrain to root and no-op empty constraint ( these are identical for a ParentConstraint )
		constraint["target"].setValue( "/" )
		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ), constraint["in"].fullTransform( "/group/constrained" ) )
		constraint["target"].setValue( "" )
		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ), constraint["in"].fullTransform( "/group/constrained" ) )


	def testRelativeTransform( self ) :

		plane1 = GafferScene.Plane()
		plane1["transform"]["translate"].setValue( imath.V3f( 1, 2, 3 ) )
		plane1["transform"]["rotate"].setValue( imath.V3f( 0, 90, 0 ) )
		plane1["name"].setValue( "target" )

		plane2 = GafferScene.Plane()
		plane2["name"].setValue( "constrained" )

		group = GafferScene.Group()
		group["in"][0].setInput( plane1["out"] )
		group["in"][1].setInput( plane2["out"] )

		self.assertSceneValid( group["out"] )

		constraint = GafferScene.ParentConstraint()
		constraint["target"].setValue( "/group/target" )
		constraint["in"].setInput( group["out"] )
		constraint["relativeTransform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/constrained" ] ) )
		constraint["filter"].setInput( filter["out"] )

		self.assertSceneValid( constraint["out"] )

		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) * group["out"].fullTransform( "/group/target" ) )

	def testDirtyPropagation( self ) :

		plane1 = GafferScene.Plane()
		plane2 = GafferScene.Plane()

		group = GafferScene.Group()
		group["in"][0].setInput( plane1["out"] )
		group["in"][1].setInput( plane2["out"] )

		constraint = GafferScene.ParentConstraint()
		constraint["target"].setValue( "/group/target" )
		constraint["in"].setInput( group["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/constrained" ] ) )
		constraint["filter"].setInput( filter["out"] )

		cs = GafferTest.CapturingSlot( constraint.plugDirtiedSignal() )

		constraint["relativeTransform"]["translate"]["x"].setValue( 10 )

		plugs = { x[0] for x in cs if not x[0].getName().startswith( "__" ) }
		self.assertEqual(
			plugs,
			{
				constraint["relativeTransform"]["translate"]["x"],
				constraint["relativeTransform"]["translate"],
				constraint["relativeTransform"],
				constraint["out"]["bound"],
				constraint["out"]["childBounds"],
				constraint["out"]["transform"],
				constraint["out"]
			}
		)

	def testParentNodeEquivalence( self ) :

		plane1 = GafferScene.Plane()
		plane1["name"].setValue( "target" )

		plane2 = GafferScene.Plane()
		plane2["name"].setValue( "constrained" )

		plane1["transform"]["rotate"]["y"].setValue( 45 )
		plane2["transform"]["translate"]["x"].setValue( 1 )

		parent = GafferScene.Parent()
		parent["in"].setInput( plane1["out"] )
		parent["parent"].setValue( "/target" )
		parent["children"][0].setInput( plane2["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( plane1["out"] )
		group["in"][1].setInput( plane2["out"] )

		constraint = GafferScene.ParentConstraint()
		constraint["in"].setInput( group["out"] )
		constraint["target"].setValue( "/group/target" )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/constrained" ] ) )
		constraint["filter"].setInput( filter["out"] )

		self.assertEqual( parent["out"].fullTransform( "/target/constrained" ), constraint["out"].fullTransform( "/group/constrained" ) )

	def testTargetScene( self ) :

		cube = GafferScene.Cube()
		sphere1 = GafferScene.Sphere()
		sphere1["transform"]["translate"]["x"].setValue( 1 )
		parent = GafferScene.Parent()
		parent["parent"].setValue( "/" )
		parent["in"].setInput( cube["out"] )
		parent["child"][0].setInput( sphere1["out"] )

		sphere2 = GafferScene.Sphere()
		sphere2["transform"]["translate"]["y"].setValue( 1 )

		cubeFilter = GafferScene.PathFilter()
		cubeFilter["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		constraint = GafferScene.ParentConstraint()
		constraint["in"].setInput( parent["out"] )
		constraint["filter"].setInput( cubeFilter["out"] )
		constraint["target"].setValue( "/sphere" )
		self.assertEqual( constraint["out"].fullTransform( "/cube" ), parent["out"].fullTransform( "/sphere" ) )

		constraint["targetScene"].setInput( sphere2["out"] )
		self.assertEqual( constraint["out"].fullTransform( "/cube" ), sphere2["out"].fullTransform( "/sphere" ) )

		sphere2["name"].setValue( "ball" )
		constraint["ignoreMissingTarget"].setValue( True )
		self.assertEqual( constraint["out"].fullTransform( "/cube" ), constraint["in"].fullTransform( "/cube" ) )

if __name__ == "__main__":
	unittest.main()
