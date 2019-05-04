##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import inspect
import unittest
import imath

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class CollectTransformsTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		# Make a few input scenes

		script = Gaffer.ScriptNode()

		script["Cube"] = GafferScene.Cube( "Cube" )
		script["Group"] = GafferScene.Group( "Group" )
		script["Group"]["in"][0].setInput( script["Cube"]["out"] )
		script["Group"]["transform"]["translate"].setValue( imath.V3f( 30 ) )
		script["PathFilter"] = GafferScene.PathFilter( "PathFilter" )
		script["PathFilter"]["paths"].setValue( IECore.StringVectorData( [ '/group/cube' ] ) )
		script["Transform"] = GafferScene.Transform( "Transform" )
		script["Transform"]["in"].setInput( script["Group"]["out"] )
		script["Transform"]["filter"].setInput( script["PathFilter"]["out"] )
		script["CustomAttributes"] = GafferScene.CustomAttributes( "CustomAttributes" )
		script["CustomAttributes"]["in"].setInput( script["Transform"]["out"] )
		script["CustomAttributes"]["filter"].setInput( script["PathFilter"]["out"] )
		script['CustomAttributes']['attributes'].addChild( Gaffer.NameValuePlug( "existingAttr", IECore.StringData( "test" ) ) )
		script["CollectTransforms"] = GafferScene.CollectTransforms( "CollectTransforms" )
		script["CollectTransforms"]["in"].setInput( script["CustomAttributes"]["out"] )
		script["CollectTransforms"]["filter"].setInput( script["PathFilter"]["out"] )
		script["Expression1"] = Gaffer.Expression( "Expression1" )
		script["Expression1"].setExpression( """
s = context.get( "collect:transformName", "attr0" )
i = int( s[4] )
parent["Transform"]["transform"]["translate"] = imath.V3f( i )
""", "python" )

		ref = IECore.CompoundObject()
		ref["existingAttr"] = IECore.StringData( "test" )

		self.assertEqual( script["CollectTransforms"]["out"].attributes( "/group/cube" ), ref )

		script["CollectTransforms"]["attributes"].setValue( IECore.StringVectorData( [ 'attr1', 'attr2' ] ) )

		ref["attr1"] = IECore.M44fData( imath.M44f().translate( imath.V3f( 1 ) ) )
		ref["attr2"] = IECore.M44fData( imath.M44f().translate( imath.V3f( 2 ) ) )
		self.assertEqual( script["CollectTransforms"]["out"].attributes( "/group/cube" ), ref )


		# Switch to writing custom variable, which expression doesn't use, so we don't get
		# special transforms
		script["CollectTransforms"]["attributeContextVariable"].setValue( "collect:customVar" )

		ref["attr1"] = IECore.M44fData( imath.M44f().translate( imath.V3f( 0 ) ) )
		ref["attr2"] = IECore.M44fData( imath.M44f().translate( imath.V3f( 0 ) ) )
		self.assertEqual( script["CollectTransforms"]["out"].attributes( "/group/cube" ), ref )

		# Test requireVariation
		script["CollectTransforms"]["requireVariation"].setValue( True )
		del ref["attr1"]
		del ref["attr2"]
		self.assertEqual( script["CollectTransforms"]["out"].attributes( "/group/cube" ), ref )

		# Test reading custom variable
		script["Expression1"].setExpression( """
s =  context.get( "collect:customVar", "attr0" )
i = int( s[4] )
parent["Transform"]["transform"]["translate"] = imath.V3f( i )
""", "python" )

		ref["attr1"] = IECore.M44fData( imath.M44f().translate( imath.V3f( 1 ) ) )
		ref["attr2"] = IECore.M44fData( imath.M44f().translate( imath.V3f( 2 ) ) )
		self.assertEqual( script["CollectTransforms"]["out"].attributes( "/group/cube" ), ref )

		# Test space
		script["CollectTransforms"]["space"].setValue( GafferScene.Transform.Space.World )
		ref["attr1"] = IECore.M44fData( imath.M44f().translate( imath.V3f( 31 ) ) )
		ref["attr2"] = IECore.M44fData( imath.M44f().translate( imath.V3f( 32 ) ) )
		self.assertEqual( script["CollectTransforms"]["out"].attributes( "/group/cube" ), ref )

		script["CollectTransforms"]["attributeContextVariable"].setValue( "collect:bogus" )
		del ref["attr1"]
		del ref["attr2"]
		self.assertEqual( script["CollectTransforms"]["out"].attributes( "/group/cube" ), ref )

		script["CollectTransforms"]["requireVariation"].setValue( False )
		ref["attr1"] = IECore.M44fData( imath.M44f().translate( imath.V3f( 30 ) ) )
		ref["attr2"] = IECore.M44fData( imath.M44f().translate( imath.V3f( 30 ) ) )
		self.assertEqual( script["CollectTransforms"]["out"].attributes( "/group/cube" ), ref )

		script["CollectTransforms"]["space"].setValue( GafferScene.Transform.Space.Local )

		# Test overwriting existing attribute
		script["Expression1"].setExpression( "", "python" )
		script["CollectTransforms"]["requireVariation"].setValue( False )
		script["CollectTransforms"]["attributes"].setValue( IECore.StringVectorData( [ 'existingAttr' ] ) )
		ref = IECore.CompoundObject()
		ref["existingAttr"] = IECore.M44fData( imath.M44f().translate( imath.V3f( 0 ) ) )
		self.assertEqual( script["CollectTransforms"]["out"].attributes( "/group/cube" ), ref )

		# Test naughtily pulling directly on the "transforms" plug
		self.assertEqual( script["CollectTransforms"]["transforms"].getValue(), IECore.CompoundObject() )

		context = Gaffer.Context()
		context.set( "scene:path", IECore.InternedStringVectorData([ "group", "cube" ]) )
		with context:
			self.assertEqual( script["CollectTransforms"]["transforms"].getValue(), ref )


if __name__ == "__main__":
	unittest.main()
