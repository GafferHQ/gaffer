##########################################################################
#
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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
import GafferTest
import GafferScene
import GafferSceneTest

class AimConstraintTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		targetTranslate = imath.V3f( 1, 2, 3 )
		constrainedTranslate = imath.V3f( 10, 11, 12 )

		plane1 = GafferScene.Plane()
		plane1["transform"]["translate"].setValue( targetTranslate )
		plane1["name"].setValue( "target" )

		plane2 = GafferScene.Plane()
		plane2["transform"]["translate"].setValue( constrainedTranslate )
		plane2["name"].setValue( "constrained" )

		group = GafferScene.Group()
		group["in"][0].setInput( plane1["out"] )
		group["in"][1].setInput( plane2["out"] )

		self.assertSceneValid( group["out"] )

		aim = GafferScene.AimConstraint()
		aim["target"].setValue( "/group/target" )
		aim["in"].setInput( group["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/constrained" ] ) )
		aim["filter"].setInput( filter["out"] )

		self.assertSceneValid( aim["out"] )

		self.assertEqual( group["out"].fullTransform( "/group/target" ), aim["out"].fullTransform( "/group/target" ) )
		self.assertEqual( group["out"].fullTransform( "/group/constrained" ).translation(), aim["out"].fullTransform( "/group/constrained" ).translation() )

		direction = aim["out"].fullTransform( "/group/constrained" ).multDirMatrix( aim["aim"].getValue() )
		self.assertAlmostEqual( (targetTranslate - constrainedTranslate).normalized().dot( direction.normalized() ), 1, 6 )


		# Test behaviour for missing target
		plane1["name"].setValue( "targetX" )
		with self.assertRaisesRegex( RuntimeError, 'AimConstraint.__constrainedTransform : Constraint target does not exist: "/group/target"' ):
			aim["out"].fullTransform( "/group/constrained" )

		aim["ignoreMissingTarget"].setValue( True )
		self.assertEqual( aim["out"].fullTransform( "/group/constrained" ), aim["in"].fullTransform( "/group/constrained" ) )

		# Constrain to root
		aim["target"].setValue( "/" )
		direction = aim["out"].fullTransform( "/group/constrained" ).multDirMatrix( aim["aim"].getValue() )
		self.assertAlmostEqual( (-constrainedTranslate).normalized().dot( direction.normalized() ), 1, 6 )

		# No op
		aim["target"].setValue( "" )
		self.assertEqual( aim["out"].fullTransform( "/group/constrained" ), aim["in"].fullTransform( "/group/constrained" ) )

	def testConstrainedWithExistingRotation( self ) :

		targetTranslate = imath.V3f( 1, 2, 3 )
		constrainedTranslate = imath.V3f( 10, 11, 12 )

		plane1 = GafferScene.Plane()
		plane1["transform"]["translate"].setValue( targetTranslate )
		plane1["name"].setValue( "target" )

		plane2 = GafferScene.Plane()
		plane2["transform"]["translate"].setValue( constrainedTranslate )
		plane2["transform"]["rotate"].setValue( imath.V3f( 90, 0, 0 ) )
		plane2["name"].setValue( "constrained" )

		group = GafferScene.Group()
		group["in"][0].setInput( plane1["out"] )
		group["in"][1].setInput( plane2["out"] )

		self.assertSceneValid( group["out"] )

		aim = GafferScene.AimConstraint()
		aim["target"].setValue( "/group/target" )
		aim["in"].setInput( group["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/constrained" ] ) )
		aim["filter"].setInput( filter["out"] )

		self.assertSceneValid( aim["out"] )

		self.assertEqual( group["out"].fullTransform( "/group/target" ), aim["out"].fullTransform( "/group/target" ) )
		self.assertEqual( group["out"].fullTransform( "/group/constrained" ).translation(), aim["out"].fullTransform( "/group/constrained" ).translation() )

		direction = aim["out"].fullTransform( "/group/constrained" ).multDirMatrix( aim["aim"].getValue() )
		self.assertAlmostEqual( (targetTranslate - constrainedTranslate).normalized().dot( direction.normalized() ), 1, 6 )

	def testTargetMode( self ) :

		targetTranslate = imath.V3f( 1, 2, 3 )
		constrainedTranslate = imath.V3f( 10, 11, 12 )

		plane1 = GafferScene.Plane()
		plane1["transform"]["translate"].setValue( targetTranslate )
		plane1["name"].setValue( "target" )

		plane2 = GafferScene.Plane()
		plane2["transform"]["translate"].setValue( constrainedTranslate )
		plane2["name"].setValue( "constrained" )

		group = GafferScene.Group()
		group["in"][0].setInput( plane1["out"] )
		group["in"][1].setInput( plane2["out"] )

		self.assertSceneValid( group["out"] )

		aim = GafferScene.AimConstraint()
		aim["target"].setValue( "/group/target" )
		aim["in"].setInput( group["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/constrained" ] ) )
		aim["filter"].setInput( filter["out"] )

		self.assertSceneValid( aim["out"] )

		self.assertEqual( group["out"].fullTransform( "/group/target" ), aim["out"].fullTransform( "/group/target" ) )
		self.assertEqual( group["out"].fullTransform( "/group/constrained" ).translation(), aim["out"].fullTransform( "/group/constrained" ).translation() )

		direction = aim["out"].fullTransform( "/group/constrained" ).multDirMatrix( aim["aim"].getValue() )
		expectedDirection = targetTranslate - constrainedTranslate
		self.assertAlmostEqual( direction.normalized().dot( expectedDirection.normalized() ), 1, 6 )

		aim["targetMode"].setValue( aim.TargetMode.BoundMin )

		direction = aim["out"].fullTransform( "/group/constrained" ).multDirMatrix( aim["aim"].getValue() )
		expectedDirection = plane1["out"].bound( "/plane" ).min() + targetTranslate - constrainedTranslate
		self.assertAlmostEqual( direction.normalized().dot( expectedDirection.normalized() ), 1, 6 )

		aim["targetMode"].setValue( aim.TargetMode.BoundMax )

		direction = aim["out"].fullTransform( "/group/constrained" ).multDirMatrix( aim["aim"].getValue() )
		expectedDirection = plane1["out"].bound( "/plane" ).max() + targetTranslate - constrainedTranslate
		self.assertAlmostEqual( direction.normalized().dot( expectedDirection.normalized() ), 1, 6 )

	def testTargetOffset( self ) :

		targetTranslate = imath.V3f( 1, 2, 3 )
		constrainedTranslate = imath.V3f( 10, 11, 12 )

		plane1 = GafferScene.Plane()
		plane1["transform"]["translate"].setValue( targetTranslate )
		plane1["name"].setValue( "target" )

		plane2 = GafferScene.Plane()
		plane2["transform"]["translate"].setValue( constrainedTranslate )
		plane2["name"].setValue( "constrained" )

		group = GafferScene.Group()
		group["in"][0].setInput( plane1["out"] )
		group["in"][1].setInput( plane2["out"] )

		self.assertSceneValid( group["out"] )

		aim = GafferScene.AimConstraint()
		aim["target"].setValue( "/group/target" )
		aim["in"].setInput( group["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/constrained" ] ) )
		aim["filter"].setInput( filter["out"] )

		self.assertSceneValid( aim["out"] )

		self.assertEqual( group["out"].fullTransform( "/group/target" ), aim["out"].fullTransform( "/group/target" ) )
		self.assertEqual( group["out"].fullTransform( "/group/constrained" ).translation(), aim["out"].fullTransform( "/group/constrained" ).translation() )

		direction = aim["out"].fullTransform( "/group/constrained" ).multDirMatrix( aim["aim"].getValue() )
		expectedDirection = targetTranslate - constrainedTranslate
		self.assertAlmostEqual( direction.normalized().dot( expectedDirection.normalized() ), 1, 6 )

		aim["targetOffset"].setValue( imath.V3f( 1, 2, 3 ) )

		direction = aim["out"].fullTransform( "/group/constrained" ).multDirMatrix( aim["aim"].getValue() )
		expectedDirection = aim["targetOffset"].getValue() + targetTranslate - constrainedTranslate
		self.assertAlmostEqual( direction.normalized().dot( expectedDirection.normalized() ), 1, 6 )

if __name__ == "__main__":
	unittest.main()
