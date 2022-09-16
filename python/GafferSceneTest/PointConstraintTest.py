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

class PointConstraintTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		targetTranslate = imath.V3f( 1, 2, 3 )
		constrainedTranslate = imath.V3f( 10, 11, 12 )
		constrainedScale = imath.V3f( 1, 2, 3 )
		constrainedRotate = imath.V3f( 15, 45, 19 )

		plane1 = GafferScene.Plane()
		plane1["transform"]["translate"].setValue( targetTranslate )
		plane1["transform"]["scale"].setValue( imath.V3f( 1, 2, 3 ) )
		plane1["transform"]["rotate"].setValue( imath.V3f( 1000, 20, 39 ) ) # shouldn't affect the result
		plane1["name"].setValue( "target" )

		plane2 = GafferScene.Plane()
		plane2["transform"]["translate"].setValue( constrainedTranslate )
		plane2["transform"]["scale"].setValue( constrainedScale )
		plane2["transform"]["rotate"].setValue( constrainedRotate )
		plane2["name"].setValue( "constrained" )

		group = GafferScene.Group()
		group["in"][0].setInput( plane1["out"] )
		group["in"][1].setInput( plane2["out"] )

		self.assertSceneValid( group["out"] )

		constraint = GafferScene.PointConstraint()
		constraint["target"].setValue( "/group/target" )
		constraint["in"].setInput( group["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/constrained" ] ) )
		constraint["filter"].setInput( filter["out"] )

		self.assertSceneValid( constraint["out"] )

		self.assertEqual( group["out"].fullTransform( "/group/target" ).translation(), targetTranslate )
		self.assertEqual( group["out"].fullTransform( "/group/constrained" ).translation(), constrainedTranslate )

		self.assertEqual( constraint["out"].fullTransform( "/group/target" ).translation(), targetTranslate )
		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ).translation(), targetTranslate )

		beforeS, beforeH, beforeR, beforeT = imath.V3f(), imath.V3f(), imath.V3f(), imath.V3f()
		group["out"].fullTransform( "/group/constrained" ).extractSHRT( beforeS, beforeH, beforeR, beforeT )

		afterS, afterH, afterR, afterT = imath.V3f(), imath.V3f(), imath.V3f(), imath.V3f()
		constraint["out"].fullTransform( "/group/constrained" ).extractSHRT( afterS, afterH, afterR, afterT )

		self.assertEqual( beforeS, afterS )
		self.assertEqual( beforeH, afterH )
		self.assertEqual( beforeR, afterR )

		constraint["xEnabled"].setValue( False )

		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ).translation().x, constrainedTranslate.x )
		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ).translation().y, targetTranslate.y )
		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ).translation().z, targetTranslate.z )

		constraint["yEnabled"].setValue( False )

		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ).translation().x, constrainedTranslate.x )
		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ).translation().y, constrainedTranslate.y )
		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ).translation().z, targetTranslate.z )

		constraint["zEnabled"].setValue( False )

		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ).translation().x, constrainedTranslate.x )
		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ).translation().y, constrainedTranslate.y )
		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ).translation().z, constrainedTranslate.z )

		# Test behaviour for missing target
		plane1["name"].setValue( "targetX" )
		constraint["xEnabled"].setValue( True )
		constraint["yEnabled"].setValue( True )
		constraint["zEnabled"].setValue( True )
		with six.assertRaisesRegex( self, RuntimeError, 'PointConstraint.__constrainedTransform : Constraint target does not exist: "/group/target"' ):
			constraint["out"].fullTransform( "/group/constrained" )

		constraint["ignoreMissingTarget"].setValue( True )
		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ), constraint["in"].fullTransform( "/group/constrained" ) )

		# Constrain to root
		constraint["target"].setValue( "/" )
		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ).translation(), imath.V3f(0) )

		# No op
		constraint["target"].setValue( "" )
		self.assertEqual( constraint["out"].fullTransform( "/group/constrained" ), constraint["in"].fullTransform( "/group/constrained" ) )

if __name__ == "__main__":
	unittest.main()
