##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

import imath

import IECore

import Gaffer
import GafferScene
import GafferSceneTest
import GafferUITest
import GafferSceneUI

class SourceSetTest( GafferUITest.TestCase ) :

	def testAccessors( self ) :

		s = Gaffer.StandardSet()
		c = Gaffer.Context()

		h = GafferSceneUI.SourceSet( c, s )

		self.assertEqual( h.getContext(), c )
		self.assertEqual( h.getNodeSet(), s )

		self.assertEqual( h.size(), 0 )

		s2 = Gaffer.StandardSet()
		c2 = Gaffer.Context()

		h.setContext( c2 )
		self.assertEqual( h.getContext(), c2 )
		self.assertEqual( h.getNodeSet(), s )

		h.setNodeSet( s2 )
		self.assertEqual( h.getContext(), c2 )
		self.assertEqual( h.getNodeSet(), s2 )

	def testSource( self ) :

		s = Gaffer.ScriptNode()

		s["pA"] = GafferScene.Plane()
		s["pA"]["name"].setValue( "planeA" )
		s["pB"] = GafferScene.Plane()
		s["pB"]["name"].setValue( "planeB" )
		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["pA"]["out"] )
		s["g"]["in"][1].setInput( s["pB"]["out"] )

		s["s"] = GafferSceneTest.TestShader()
		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )

		s["s2"] = GafferSceneTest.TestShader()
		s["a2"] = GafferScene.ShaderAssignment()
		s["a2"]["in"].setInput( s["a"]["out"] )
		s["a2"]["shader"].setInput( s["s2"]["out"] )

		s["g2"] = GafferScene.Group()
		s["g2"]["in"][0].setInput( s["a2"]["out"] )

		s["o"] = GafferScene.SceneWriter()
		s["o"]["in"].setInput( s["g2"]["out"] )

		n = Gaffer.StandardSet()
		c = Gaffer.Context()

		self.assertEqual( len(GafferSceneUI.ContextAlgo.getSelectedPaths( c ).paths()), 0 )

		h = GafferSceneUI.SourceSet( c, n )
		self.assertEqual( h.size(), 0 )

		a = "/group/group/planeA"
		b = "/group/group/planeB"

		n.add( s["o"] )

		# Test scene selection changed

		GafferSceneUI.ContextAlgo.setSelectedPaths( c, IECore.PathMatcher( [ a	 ] ) )
		self.assertEqual( set(h), { s["pA"] } )

		GafferSceneUI.ContextAlgo.setSelectedPaths( c, IECore.PathMatcher( [ a, b ] ) )

		self.assertEqual( set(h), { s["pA"] } )

		# Test defaulting to last input node if no valid plug or path
		GafferSceneUI.ContextAlgo.setSelectedPaths( c, IECore.PathMatcher() )
		self.assertEqual( set(h), { s["o"] } )

		# Test nodes changed

		n.clear()
		self.assertEqual( h.size(), 0 )

		n.add( s["g2" ] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( c, IECore.PathMatcher( [ a ] ) )
		self.assertEqual( set(h), { s["pA"] } )

		n.remove( s["g2"] )
		n.add( s["g"] )
		self.assertEqual( set(h), { s["g"] } )

		GafferSceneUI.ContextAlgo.setSelectedPaths( c, IECore.PathMatcher( [ "/group/planeA" ] ) )
		self.assertEqual( set(h), { s["pA"] } )

		GafferSceneUI.ContextAlgo.setSelectedPaths( c, IECore.PathMatcher( [ "/group" ] ) )
		n.clear()
		n.add( s["g2"] )
		self.assertEqual( set(h), { s["g2"] } )

		# Test incoming scene dirtied

		GafferSceneUI.ContextAlgo.setSelectedPaths( c, IECore.PathMatcher( [ b ] ) )
		self.assertEqual( set(h), { s["pB"] } )

		s["pB"]["name"].setValue( "notPlaneB" )
		self.assertEqual( set(h), { s["g2"] } )

		# Test multiple non-scene nodes
		n.clear()
		n.add( s["s"] )
		self.assertEqual( set(h), { s["s"] } )
		n.add( s["s2"] )
		self.assertEqual( set(h), { s["s2"] } )
		n.remove( s["s2"] )
		self.assertEqual( set(h), { s["s"] } )

	def testReadOnlyNodeHierarchies( self ) :

		class TestShaderBall( GafferScene.ShaderBall ) :
			def __init__( self, name = "TestShaderBall" ) :
				GafferScene.ShaderBall.__init__( self, name )

		# Test to make sure we don't surface internal nodes

		s = Gaffer.StandardSet()
		c = Gaffer.Context()
		h = GafferSceneUI.SourceSet( c, s )

		b = TestShaderBall()
		s.add( b )
		self.assertEqual( set(h), set( [ b, ] ) )

		GafferSceneUI.ContextAlgo.setSelectedPaths( c, IECore.PathMatcher( [ "/sphere" ] ) )
		self.assertEqual( set(h), set( [ b, ] ) )

	def testSignals( self ) :

		s = Gaffer.ScriptNode()

		s["pA"] = GafferScene.Plane()
		s["pA"]["name"].setValue( "planeA" )
		s["pB"] = GafferScene.Plane()
		s["pB"]["name"].setValue( "planeB" )
		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["pA"]["out"] )
		s["g"]["in"][1].setInput( s["pB"]["out"] )

		s["g2"] = GafferScene.Group()
		s["g2"]["in"][0].setInput( s["g"]["out"] )

		mirror = set()

		def added( _, member ) :
			mirror.add( member )

		def removed( _, member ) :
			mirror.remove( member )

		n = Gaffer.StandardSet()
		c = Gaffer.Context()

		h = GafferSceneUI.SourceSet( c, n )
		ca = h.memberAddedSignal().connect( added )
		cr = h.memberRemovedSignal().connect( removed )

		self.assertEqual( h.size(), 0 )
		self.assertEqual( len(mirror), 0 )

		a = "/group/group/planeA"
		b = "/group/group/planeB"

		n.add( s["g2"] )

		GafferSceneUI.ContextAlgo.setSelectedPaths( c, IECore.PathMatcher( [ a ] ) )
		self.assertEqual( set(h), mirror )

		GafferSceneUI.ContextAlgo.setSelectedPaths( c, IECore.PathMatcher( [ b ] ) )
		self.assertEqual( set(h), mirror )

		GafferSceneUI.ContextAlgo.setSelectedPaths( c, IECore.PathMatcher( [ a, b ] ) )
		self.assertEqual( set(h), mirror )

	def testSignalOrder( self ) :

		s = Gaffer.ScriptNode()

		s["p1"] = GafferScene.Plane()
		s["p2"] = GafferScene.Plane()

		n = Gaffer.StandardSet()
		c = Gaffer.Context()
		h = GafferSceneUI.SourceSet( c, n )

		callbackFailures = { "added" : 0, "removed" : 0 }

		# Check we have no members when one is removed as we're
		# defined as only ever containing one node. We can't assert
		# here as the exception gets eaten and the test passes anyway
		def removed( _, member ) :
			if set(h) != set() :
				callbackFailures["removed"] += 1

		cr = h.memberRemovedSignal().connect( removed )

		n.add( s["p1"] )
		n.add( s["p2"] )
		n.remove( s["p1"] )
		n.remove( s["p2"] )

		self.assertEqual( callbackFailures["removed"], 0 )

		# Check member is added before signal, same deal re: asserts
		def added( _, member ) :
			if set(h) != { s["p1"] } :
				callbackFailures["added"] += 1

		ca = h.memberAddedSignal().connect( added )

		n.add( s["p1"] )
		self.assertEqual( callbackFailures["added"], 0 )

	def testGILManagement( self ) :

		script = Gaffer.ScriptNode()

		# Build a contrived scene that will cause `childNames` queries to spawn
		# a threaded compute that will execute a Python expression.

		script["plane"] = GafferScene.Plane()
		script["plane"]["divisions"].setValue( imath.V2i( 50 ) )

		script["planeFilter"] = GafferScene.PathFilter()
		script["planeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		script["sphere"] = GafferScene.Sphere()

		script["instancer"] = GafferScene.Instancer()
		script["instancer"]["in"].setInput( script["plane"]["out"] )
		script["instancer"]["prototypes"].setInput( script["sphere"]["out"] )
		script["instancer"]["filter"].setInput( script["planeFilter"]["out"] )

		script["instanceFilter"] = GafferScene.PathFilter()
		script["instanceFilter"]["paths"].setValue( IECore.StringVectorData( [ "/plane/instances/*/*" ] ) )

		script["cube"] = GafferScene.Cube()

		script["parent"] = GafferScene.Parent()
		script["parent"]["in"].setInput( script["instancer"]["out"] )
		script["parent"]["children"][0].setInput( script["cube"]["out"] )
		script["parent"]["filter"].setInput( script["instanceFilter"]["out"] )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( 'parent["sphere"]["name"] = context["sphereName"]' )

		# Test that the `SourceSet` constructor releases the GIL so that the compute
		# doesn't hang. If we're lucky, the expression executes on the main
		# thread anyway, so loop to give it plenty of chances to fail.

		for i in range( 0, 100 ) :

			context = Gaffer.Context()
			context["sphereName"] = "sphere{}".format( i )
			GafferSceneUI.ContextAlgo.setSelectedPaths(
				context,
				IECore.PathMatcher( [
					"/plane/instances/{}/2410/cube".format( context["sphereName"] )
				] )
			)

			sourceSet = GafferSceneUI.SourceSet( context, Gaffer.StandardSet( [ script["parent"] ] ) )

	def testNullConstructorArguments( self ) :

		sphere =  GafferScene.Sphere()
		context = Gaffer.Context()

		with self.assertRaises( Exception ) :
			GafferSceneUI.SourceSet( None, Gaffer.StandardSet( [ sphere ] ) )

		with self.assertRaises( Exception ) :
			GafferSceneUI.SourceSet( context, None )

		with self.assertRaises( Exception ) :
			GafferSceneUI.SourceSet( None, None )

if __name__ == "__main__":
	unittest.main()
