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

import re
import functools
import six

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

		self.assertEqual( str( e.exception ), 'Syntax error in indicated part of SetExpression.\nsetA - (/group/group/sphere2\n     |---------------------|\n.' )

		# Sets that don't exist should be replaced with an empty PathMatcher
		expressionCheck( 'A', [] )

		# Test that changing set contents will result in an updated hash
		h = GafferScene.SetAlgo.setExpressionHash( "setA", group2["out"] )
		setA["paths"].setValue( IECore.StringVectorData( [ '/group/sphere1' ] ) )
		self.assertNotEqual( h, GafferScene.SetAlgo.setExpressionHash( "setA", group2["out"] ) )

	def testColonAndDotInSetAndObjectNames( self ):

		sphere1 = GafferScene.Sphere( "Sphere1" )
		sphere1["name"].setValue( 'MyObject:sphere1.model' )

		setA = GafferScene.Set( "SetA" )
		setA["name"].setValue( "MySets:setA.set" )
		setA["paths"].setValue( IECore.StringVectorData( [ "/MyObject:sphere1.model" ] ) )

		self.assertCorrectEvaluation( setA["out"], "MySets:setA.set", [ "/MyObject:sphere1.model" ] )
		self.assertCorrectEvaluation( setA["out"], "/MyObject:sphere1.model", [ "/MyObject:sphere1.model" ] )

	def testWildcardInSetName( self ) :

		sphereA = GafferScene.Sphere( "SphereA" )
		sphereA["sets"].setValue( 'sphereA' )
		sphereA["name"].setValue( 'sphereA' )

		sphereB = GafferScene.Sphere( "SphereB" )
		sphereB["sets"].setValue( 'sphereB' )
		sphereB["name"].setValue( 'sphereB' )

		sphereC = GafferScene.Sphere( "SphereC" )
		sphereC["sets"].setValue( 'sphereC' )
		sphereC["name"].setValue( 'sphereC' )

		sphereC2 = GafferScene.Sphere( "SphereC2" )
		sphereC2["sets"].setValue( 'sphereC' )
		sphereC2["name"].setValue( 'sphereC2' )

		# sphere that we don't want in the resulting set
		undesired = GafferScene.Sphere( "undesired" )
		undesired["sets"].setValue( 'undesired' )
		undesired["name"].setValue( 'undesired' )

		group = GafferScene.Group( "Group" )
		group["in"][0].setInput( sphereA["out"] )
		group["in"][1].setInput( sphereB["out"] )
		group["in"][2].setInput( sphereC["out"] )
		group["in"][3].setInput( sphereC2["out"] )
		group["in"][4].setInput( undesired["out"] )

		oldHash = GafferScene.SetAlgo.setExpressionHash( "sphere*", group["out"] )

		# Test different features of StringAlgo.
		# Note that '-' is reserved as a SetExpression operator and the
		# respective range related feature of StringAlgo isn't supported ("myFoo[A-Z]").

		self.assertCorrectEvaluation( group["out"], "sphere*", ["/group/sphereA", "/group/sphereB", "/group/sphereC", "/group/sphereC2"] )
		self.assertCorrectEvaluation( group["out"], "sphere* | undesired", ["/group/sphereA", "/group/sphereB", "/group/sphereC", "/group/sphereC2", "/group/undesired"] )
		self.assertCorrectEvaluation( group["out"], "sphere[AB]", ["/group/sphereA", "/group/sphereB"] )
		self.assertCorrectEvaluation( group["out"], "sphere[!AB]", ["/group/sphereC", "/group/sphereC2"] )
		self.assertCorrectEvaluation( group["out"], "sphere?", ["/group/sphereA", "/group/sphereB", "/group/sphereC", "/group/sphereC2"] )

		sphereC2["sets"].setValue( 'sphere?' )

		self.assertCorrectEvaluation( group["out"], r"sphere\?", ["/group/sphereC2"] )
		self.assertNotEqual( oldHash, GafferScene.SetAlgo.setExpressionHash( "sphere*", group["out"] ) )

	def testInterestingSetNames( self ) :

		sphere = GafferScene.Sphere()

		for setName in ( ":", "a:", "a:b", "!", "0", "]A" ) :
			sphere["sets"].setValue( setName )
			self.assertCorrectEvaluation( sphere["out"], setName, { "/sphere" } )

	def testInAndContaining( self ) :

		# /group
		#    /sphere
		#    /group
		#       /sphere
		#       /sphere1
		# /sphere

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "indubitablyASet containingThings" )

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][0].setInput( sphere["out"] )

		group2 = GafferScene.Group()
		group2["in"][0].setInput( sphere["out"] )
		group2["in"][1].setInput( group["out"] )

		parent = GafferScene.Parent()
		parent["in"].setInput( group2["out"] )
		parent["child"].setInput( sphere["out"] )

		setA = GafferScene.Set()
		setA["in"].setInput( parent["out"] )
		setA["name"].setValue( "A" )
		setA["paths"].setValue( IECore.StringVectorData( [
			"/group/group",
		] ) )

		setB = GafferScene.Set()
		setB["in"].setInput( setA["out"] )
		setB["name"].setValue( "B" )
		setB["paths"].setValue( IECore.StringVectorData( [
			"/group/group/sphere",
			"/group/sphere",
		] ) )

		self.assertSceneValid( setB["out"] )

		# Test basic operation of `in`

		self.assertCorrectEvaluation( setB["out"], "A in B", [] )
		self.assertCorrectEvaluation( setB["out"], "A in A", setA["paths"].getValue() )
		self.assertCorrectEvaluation( setB["out"], "B in A", [ "/group/group/sphere" ] )
		self.assertCorrectEvaluation( setB["out"], "B in B", setB["paths"].getValue() )
		self.assertCorrectEvaluation( setB["out"], "/group/group/sphere in /group", [ "/group/group/sphere" ] )
		self.assertCorrectEvaluation( setB["out"], "B in /group/group", [ "/group/group/sphere" ] )
		self.assertCorrectEvaluation( setB["out"], "B in ( /group/group /somewhereElse )", [ "/group/group/sphere" ] )

		# Test basic operation of `containing`

		self.assertCorrectEvaluation( setB["out"], "A containing B", [ "/group/group" ] )
		self.assertCorrectEvaluation( setB["out"], "A containing A", setA["paths"].getValue() )
		self.assertCorrectEvaluation( setB["out"], "B containing A", [] )
		self.assertCorrectEvaluation( setB["out"], "B containing B", setB["paths"].getValue() )
		self.assertCorrectEvaluation( setB["out"], "/group containing /group/sphere", [ "/group" ] )
		self.assertCorrectEvaluation( setB["out"], "A containing /group/group/sphere", [ "/group/group" ] )

		# Test various problematic parses

		self.assertCorrectEvaluation( setB["out"], "A in (A)", setA["paths"].getValue() )
		self.assertCorrectEvaluation( setB["out"], "A in(A)", setA["paths"].getValue() )
		self.assertCorrectEvaluation( setB["out"], "(A)in(A)", setA["paths"].getValue() )
		self.assertCorrectEvaluation( setB["out"], "indubitablyASet", setB["out"].set( "indubitablyASet" ).value.paths() )
		self.assertCorrectEvaluation( setB["out"], "A in indubitablyASet", [] )
		self.assertCorrectEvaluation( setB["out"], "B in indubitablyASet", setB["paths"].getValue() )
		self.assertCorrectEvaluation( setB["out"], "A in in?*", [] )
		self.assertCorrectEvaluation( setB["out"], "containingThings", setB["out"].set( "containingThings" ).value.paths() )
		self.assertCorrectEvaluation( setB["out"], "B in containing*", setB["paths"].getValue() )

	def testWildcardsInObjectNames( self ) :

		sphere = GafferScene.Sphere()

		for expression in [
			"/*",
			"/spher[ef]",
			"/spher?",
		] :
			with six.assertRaisesRegex( self, RuntimeError, 'Object name "{0}" contains wildcards'.format( re.escape( expression ) ) ) :
				GafferScene.SetAlgo.evaluateSetExpression( expression, sphere["out"] )

	def assertCorrectEvaluation( self, scenePlug, expression, expectedContents ) :

		result = set( GafferScene.SetAlgo.evaluateSetExpression( expression, scenePlug ).paths() )
		self.assertEqual( result, set( expectedContents ) )

if __name__ == "__main__":
	unittest.main()
