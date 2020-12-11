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

import imath
import unittest
import six

import IECore

import Gaffer
import GafferTest

class SerialisationTest( GafferTest.TestCase ) :

	class SerialisationTestNode( Gaffer.Node ) :

		def __init__( self, name = "SerialisationTestNode", initArgument = 10 ) :

			Gaffer.Node.__init__( self, name )

			self.initArgument = initArgument
			self.needsAdditionalModules = False

			self["childNodeNeedingSerialisation"] = GafferTest.AddNode()
			self["childNodeNotNeedingSerialisation"] = GafferTest.AddNode()

	IECore.registerRunTimeTyped( SerialisationTestNode )

	def testCustomSerialiser( self ) :

		class CustomSerialiser( Gaffer.NodeSerialiser ) :

			def moduleDependencies( self, node, serialisation ) :

				return { "GafferTest" } | Gaffer.NodeSerialiser.moduleDependencies( self, node, serialisation )

			def constructor( self, node, serialisation ) :

				if node.needsAdditionalModules :
					serialisation.addModule( "ConstructorModule" )
				return ( "GafferTest.SerialisationTest.SerialisationTestNode( \"%s\", %d )" % ( node.getName(), node.initArgument ) )

			def postConstructor( self, node, identifier, serialisation ) :

				result = Gaffer.NodeSerialiser.postConstructor( self, node, identifier, serialisation )
				result += identifier + ".postConstructorWasHere = True\n"
				if node.needsAdditionalModules :
					serialisation.addModule( "PostConstructorModule" )
				return result

			def postHierarchy( self, node, identifier, serialisation ) :

				result = Gaffer.NodeSerialiser.postHierarchy( self, node, identifier, serialisation )
				result += identifier + ".postHierarchyWasHere = True\n"
				if node.needsAdditionalModules :
					serialisation.addModule( "PostHierarchyModule" )
				return result

			def postScript( self, node, identifier, serialisation ) :

				result = Gaffer.NodeSerialiser.postScript( self, node, identifier, serialisation )
				result += identifier + ".postScriptWasHere = True\n"
				if node.needsAdditionalModules :
					serialisation.addModule( "PostScriptModule" )
				return result

			def childNeedsSerialisation( self, child, serialisation ) :

				if isinstance( child, Gaffer.Node ) and child.getName() == "childNodeNeedingSerialisation" :
					return True

				return Gaffer.NodeSerialiser.childNeedsSerialisation( self, child, serialisation )

			def childNeedsConstruction( self, child, serialisation ) :

				if isinstance( child, Gaffer.Node ) :
					return False

				return Gaffer.NodeSerialiser.childNeedsConstruction( self, child, serialisation )

		customSerialiser = CustomSerialiser()
		Gaffer.Serialisation.registerSerialiser( self.SerialisationTestNode, customSerialiser )

		s = Gaffer.ScriptNode()
		s["n"] = self.SerialisationTestNode( "a", initArgument=20 )
		s["n"]["childNodeNeedingSerialisation"]["op1"].setValue( 101 )
		s["n"]["childNodeNotNeedingSerialisation"]["op1"].setValue( 101 )
		s["n"]["dynamicPlug"] = Gaffer.FloatPlug( defaultValue = 10, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		self.assertTrue( Gaffer.Serialisation.acquireSerialiser( s["n"] ).isSame( customSerialiser ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( isinstance( s2["n"], self.SerialisationTestNode ) )
		self.assertEqual( s["n"].keys(), s2["n"].keys() )

		self.assertEqual( s2["n"].initArgument, 20 )
		self.assertEqual( s2["n"]["childNodeNeedingSerialisation"]["op1"].getValue(), 101 )
		self.assertEqual( s2["n"]["childNodeNotNeedingSerialisation"]["op1"].getValue(), 0 )
		self.assertEqual( s2["n"]["dynamicPlug"].getValue(), 10 )
		self.assertEqual( s2["n"].postConstructorWasHere, True )
		self.assertEqual( s2["n"].postHierarchyWasHere, True )
		self.assertEqual( s2["n"].postScriptWasHere, True )

		# Test calls to `Serialisation.addModule()`

		s["n"].needsAdditionalModules = True
		ss = s.serialise()
		self.assertIn( "import ConstructorModule", ss )
		self.assertIn( "import PostConstructorModule", ss )
		self.assertIn( "import PostHierarchyModule", ss )
		self.assertIn( "import PostScriptModule", ss )

	def testParentAccessor( self ) :

		n = Gaffer.Node()
		s = Gaffer.Serialisation( n )
		self.assertTrue( s.parent().isSame( n ) )

	def testClassPath( self ) :

		self.assertEqual( Gaffer.Serialisation.classPath( Gaffer.Node() ), "Gaffer.Node" )
		self.assertEqual( Gaffer.Serialisation.classPath( Gaffer.Node ), "Gaffer.Node" )

		self.assertEqual( Gaffer.Serialisation.classPath( GafferTest.AddNode() ), "GafferTest.AddNode" )
		self.assertEqual( Gaffer.Serialisation.classPath( GafferTest.AddNode ), "GafferTest.AddNode" )

	def testModulePath( self ) :

		self.assertEqual( Gaffer.Serialisation.modulePath( Gaffer.Node() ), "Gaffer" )
		self.assertEqual( Gaffer.Serialisation.modulePath( Gaffer.Node ), "Gaffer" )

		self.assertEqual( Gaffer.Serialisation.modulePath( GafferTest.AddNode() ), "GafferTest" )
		self.assertEqual( Gaffer.Serialisation.modulePath( GafferTest.AddNode ), "GafferTest" )

	def testIncludeParentMetadataWhenExcludingChildren( self ) :

		n1 = Gaffer.Node()
		Gaffer.Metadata.registerValue( n1, "test", imath.Color3f( 1, 2, 3 ) )

		with Gaffer.Context() as c :
			c["serialiser:includeParentMetadata"] = IECore.BoolData( True )
			s = Gaffer.Serialisation( n1, filter = Gaffer.StandardSet() )

		scope = { "parent" : Gaffer.Node() }
		exec( s.result(), scope, scope )

		self.assertEqual( Gaffer.Metadata.value( scope["parent"], "test" ), imath.Color3f( 1, 2, 3 ) )

	class Outer( object ) :

			class Inner( object ) :

					# Emulate feature coming in Python 3.
					# See https://www.python.org/dev/peps/pep-3155/
					__qualname__ = "Outer.Inner"

	def testClassPathForNestedClasses( self ) :

		self.assertEqual( Gaffer.Serialisation.classPath( self.Outer.Inner ), "GafferTest.SerialisationTest.Outer.Inner" )

	def testVersionMetadata( self ) :

		n = Gaffer.Node()
		serialisationWithMetadata = Gaffer.Serialisation( n ).result()

		with Gaffer.Context() as c :
			c["serialiser:includeVersionMetadata"] = IECore.BoolData( False )
			serialisationWithoutMetadata = Gaffer.Serialisation( n ).result()

		scope = { "parent" : Gaffer.Node() }
		exec( serialisationWithMetadata, scope, scope )

		self.assertEqual( Gaffer.Metadata.value( scope["parent"], "serialiser:milestoneVersion" ), Gaffer.About.milestoneVersion() )
		self.assertEqual( Gaffer.Metadata.value( scope["parent"], "serialiser:majorVersion" ), Gaffer.About.majorVersion() )
		self.assertEqual( Gaffer.Metadata.value( scope["parent"], "serialiser:minorVersion" ), Gaffer.About.minorVersion() )
		self.assertEqual( Gaffer.Metadata.value( scope["parent"], "serialiser:patchVersion" ), Gaffer.About.patchVersion() )

		scope = { "parent" : Gaffer.Node() }
		exec( serialisationWithoutMetadata, scope, scope )

		self.assertEqual( Gaffer.Metadata.value( scope["parent"], "serialiser:milestoneVersion" ), None )
		self.assertEqual( Gaffer.Metadata.value( scope["parent"], "serialiser:majorVersion" ), None )
		self.assertEqual( Gaffer.Metadata.value( scope["parent"], "serialiser:minorVersion" ), None )
		self.assertEqual( Gaffer.Metadata.value( scope["parent"], "serialiser:patchVersion" ), None )

	def testProtectParentNamespace( self ) :

		n = Gaffer.Node()
		n["a"] = GafferTest.AddNode()
		n["b"] = GafferTest.AddNode()
		n["b"]["op1"].setInput( n["a"]["sum"] )

		serialisationWithProtection = Gaffer.Serialisation( n ).result()

		with Gaffer.Context() as c :
			c["serialiser:protectParentNamespace"] = IECore.BoolData( False )
			serialisationWithoutProtection = Gaffer.Serialisation( n ).result()

		scope = { "parent" : Gaffer.Node() }
		scope["parent"]["a"] = Gaffer.StringPlug()
		exec( serialisationWithProtection, scope, scope )

		self.assertIsInstance( scope["parent"]["a"], Gaffer.StringPlug )
		self.assertIn( "a1", scope["parent"] )
		self.assertEqual( scope["parent"]["b"]["op1"].getInput(), scope["parent"]["a1"]["sum"] )

		scope = { "parent" : Gaffer.Node() }
		scope["parent"]["a"] = Gaffer.StringPlug()
		exec( serialisationWithoutProtection, scope, scope )

		self.assertIsInstance( scope["parent"]["a"], GafferTest.AddNode )
		self.assertNotIn( "a1", scope["parent"] )
		self.assertEqual( scope["parent"]["b"]["op1"].getInput(), scope["parent"]["a"]["sum"] )

	def testChildIdentifier( self ) :

		node = Gaffer.Node()
		node["a"] = GafferTest.AddNode()
		node["b"] = GafferTest.AddNode()

		filter = Gaffer.StandardSet( [ node["a"] ] )
		serialisation = Gaffer.Serialisation( node, filter = filter )

		aIdentifier = serialisation.identifier( node["a"] )
		self.assertEqual(
			serialisation.identifier( node["a"]["op1"] ),
			serialisation.childIdentifier( aIdentifier, node["a"]["op1"] )
		)

		bIdentifier = serialisation.identifier( node["b"] )
		self.assertEqual( bIdentifier, "" )
		self.assertEqual( serialisation.childIdentifier( bIdentifier, node["b"]["op1"] ), "" )

	def testBase64ObjectConversions( self ) :

		# Test StringData with all possible byte values (except 0,
		# because we can't construct a StringData with a null at the start).
		allBytes = bytes().join( [ six.int2byte( i ) for i in range( 1, 256 ) ] )
		for i in range( 0, len( allBytes ) ) :
			o = IECore.StringData( allBytes[:i] )
			b = Gaffer.Serialisation.objectToBase64( o )
			self.assertEqual(
				Gaffer.Serialisation.objectFromBase64( b ),
				o
			)

		# Test CompoundData
		o = IECore.CompoundData( {
			"a" : 10,
			"b" : 20,
			"c" : IECore.CompoundData( {
				"d" : imath.V3f( 1, 2, 3 )
			} )
		} )
		b = Gaffer.Serialisation.objectToBase64( o )
		self.assertEqual(
			Gaffer.Serialisation.objectFromBase64( b ),
			o
		)

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testSwitchPerformance( self ) :

		script = Gaffer.ScriptNode()

		def build( maxDepth, upstreamNode = None, depth = 0 ) :

			node = Gaffer.Switch()
			node.setup( Gaffer.V3iPlug() )
			if upstreamNode is not None :
				node["in"][0].setInput( upstreamNode["out"] )

			script.addChild( node )

			if depth < maxDepth :
				build( maxDepth, node, depth + 1 )
				build( maxDepth, node, depth + 1 )

		with Gaffer.DirtyPropagationScope() :
			build( 13 )

		with GafferTest.TestRunner.PerformanceScope() :
			script.serialise()

	def testAddModule( self ) :

		node = Gaffer.Node()
		serialisation = Gaffer.Serialisation( node )
		serialisation.addModule( "MyModule" )
		serialisation.addModule( "MyModule" )

		self.assertEqual( serialisation.result().count( "import MyModule" ), 1 )

if __name__ == "__main__":
	unittest.main()
