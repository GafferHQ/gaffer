##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

import functools

import IECore

import GafferScene
import GafferSceneTest

class SetAlgoTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		sphere1 = GafferScene.Sphere( "Sphere1" )
		sphere1["name"].setValue( 'sphere1' )
		sphere2 = GafferScene.Sphere( "Sphere2" )
		sphere2["name"].setValue( 'sphere2' )
		sphere3 = GafferScene.Sphere( "Sphere3" )
		sphere3["name"].setValue( 'sphere3' )

		group1 = GafferScene.Group( "Group1" )
		group1["in"].addChild( GafferScene.ScenePlug( "in1" ) )
		group1["in"].addChild( GafferScene.ScenePlug( "in2" ) )

		group1["in"]["in0"].setInput( sphere1["out"] )
		group1["in"]["in1"].setInput( sphere2["out"] )

		setA = GafferScene.Set( "SetA" )
		setA["name"].setValue( 'setA' )
		setA["paths"].setValue( IECore.StringVectorData( [ '/group/sphere1', '/group/sphere2' ] ) )

		setB = GafferScene.Set( "SetB" )
		setB["name"].setValue( 'setB' )
		setB["paths"].setValue( IECore.StringVectorData( [ '/group/sphere2' ] ) )

		setC = GafferScene.Set( "SetC" )
		setC["name"].setValue( 'setC' )
		setC["paths"].setValue( IECore.StringVectorData( [ '/sphere3' ] ) )

		setD = GafferScene.Set( "SetD" )
		setD["name"].setValue( 'setD' )
		setD["paths"].setValue( IECore.StringVectorData( [] ) )

		group2 = GafferScene.Group( "Group2" )
		group2["in"].addChild( GafferScene.ScenePlug( "in1" ) )
		group2["in"].addChild( GafferScene.ScenePlug( "in2" ) )
		group2["in"].addChild( GafferScene.ScenePlug( "in3" ) )

		setA["in"].setInput( group1["out"] )
		setB["in"].setInput( setA["out"] )
		setC["in"].setInput( sphere3["out"] )
		setD["in"].setInput( setC["out"] )

		group2["in"]["in0"].setInput( setB["out"] )
		group2["in"]["in2"].setInput( setD["out"] )

		# Set memberships:
		# A: ( /group/group/sphere1, /group/group/sphere2 )
		# B: ( /group/group/sphere2 )
		# C: ( /group/sphere3 )
		# D: ( )

		expressionCheck = functools.partial( self.assertCorrectEvaluation, group2["out"] )

		expressionCheck( '', [] )

		expressionCheck( 'setA', [ '/group/group/sphere1', '/group/group/sphere2' ] )
		expressionCheck( '/group/sphere3', [ '/group/sphere3' ] )

		# Test expressions that contain only sets and have a clearly defined evaluation order
		expressionCheck( '(setA | setC)', [ '/group/group/sphere1', '/group/group/sphere2', '/group/sphere3' ] )
		expressionCheck( '(setA | setB)', [ '/group/group/sphere1', '/group/group/sphere2' ] )
		expressionCheck( '(setA & setB)', [ '/group/group/sphere2' ] )
		expressionCheck( '(setA & setC)', [] )
		expressionCheck( '(setA | setB) & setD', [] )
		expressionCheck( '(setA & setB) | setD', [ '/group/group/sphere2' ] )
		expressionCheck( '(setA - setB)', [ '/group/group/sphere1' ] )
		expressionCheck( '(setA - setC)', [ '/group/group/sphere1', '/group/group/sphere2'] )
		expressionCheck( '(setB - setC)', [ '/group/group/sphere2' ] )

		# Test expressions that omit the explicit grouping and rely on operator precedence
		expressionCheck( 'setA setC', [ '/group/group/sphere1', '/group/group/sphere2', '/group/sphere3' ] )
		expressionCheck( 'setA | setB | setC', [ '/group/group/sphere1', '/group/group/sphere2', '/group/sphere3' ] )
		expressionCheck( 'setA | setB & setC', [ '/group/group/sphere1', '/group/group/sphere2' ] )
		expressionCheck( 'setA & setB | setC', [ '/group/group/sphere2', '/group/sphere3' ] )
		expressionCheck( 'setA & setB - setC', [ '/group/group/sphere2' ] )
		expressionCheck( 'setA - setB | setC', [ '/group/group/sphere1', '/group/sphere3' ] )

		# Test more complex expressions that contain explicit object names and lists thereof
		expressionCheck( '/group/light1 /group/light2', [ '/group/light1', '/group/light2' ] )
		expressionCheck( '(/group/light1 /group/light2)', [ '/group/light1', '/group/light2' ] )
		expressionCheck( '/group/light1 /group/light2 setA', [ '/group/light1', '/group/light2', '/group/group/sphere1', '/group/group/sphere2' ] )
		expressionCheck( '(/group/light1 /group/light2) | setA', [ '/group/light1', '/group/light2', '/group/group/sphere1', '/group/group/sphere2' ] )
		expressionCheck( 'setA & (/group/group/sphere1 /group/group/sphere42)', [ '/group/group/sphere1' ] )
		expressionCheck( 'setA - /group/group/sphere2', [ '/group/group/sphere1' ] )
		expressionCheck( '(setA - /group/group/sphere2)', [ '/group/group/sphere1' ] )
		expressionCheck( 'setA - ((setC /group/group/sphere2) & setB)', [ '/group/group/sphere1' ] )
		expressionCheck( '(setA - ((setC /group/group/sphere2) & setB))', [ '/group/group/sphere1' ] )
		expressionCheck( 'setA - (/group/group/sphere1 /group/group/sphere2) | (setA setB setC) & setC', [ '/group/sphere3' ] )

		# Test if proper exception is thrown for invalid expression
		with self.assertRaises( RuntimeError ) as e :
			# note the missing )
			GafferScene.SetAlgo.evaluateSetExpression( 'setA - (/group/group/sphere2', group2["out"] )

		self.assertEqual( str( e.exception ), 'Exception : Syntax error in indicated part of SetExpression.\nsetA - (/group/group/sphere2\n     |---------------------|\n.' )

		# Sets that don't exist should be replaced with an empty PathMatcher
		expressionCheck( 'A', [] )

		# Test that changing set contents will result in an updated hash
		h = GafferScene.SetAlgo.setExpressionHash( "setA", group2["out"] )
		setA["paths"].setValue( IECore.StringVectorData( [ '/group/sphere1' ] ) )
		self.assertNotEqual( h, GafferScene.SetAlgo.setExpressionHash( "setA", group2["out"] ) )

	def assertCorrectEvaluation( self, scenePlug, expression, expectedContents ) :

		result = set( GafferScene.SetAlgo.evaluateSetExpression( expression, scenePlug ).paths() )
		self.assertEqual( result, set( expectedContents ) )
