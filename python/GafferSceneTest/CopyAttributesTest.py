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

import unittest

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class CopyAttributesTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		plane = GafferScene.Plane()

		customAttributes = GafferScene.CustomAttributes()
		customAttributes["in"].setInput( plane["out"] )
		customAttributes["attributes"].addChild( Gaffer.NameValuePlug( "a", IECore.IntData( 1 ) ) )
		customAttributes["attributes"].addChild( Gaffer.NameValuePlug( "b", IECore.IntData( 2 ) ) )

		# Node should do nothing without a filter applied.

		copyAttributes = GafferScene.CopyAttributes()
		copyAttributes["in"].setInput( plane["out"] )
		copyAttributes["source"].setInput( customAttributes["out"] )

		self.assertScenesEqual( plane["out"], copyAttributes["out"] )
		self.assertSceneHashesEqual( plane["out"], copyAttributes["out"] )

		# Applying a filter should kick it into action.

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		copyAttributes["filter"].setInput( f["out"] )

		self.assertEqual( copyAttributes["out"].attributes( "/plane" ), customAttributes["out"].attributes( "/plane" ) )

		# We should be able to copy just some attributes.

		copyAttributes["attributes"].setValue( "a" )
		self.assertEqual( copyAttributes["out"].attributes( "/plane" ).keys(), [ "a" ] )
		self.assertEqual( copyAttributes["out"].attributes( "/plane" )["a"], customAttributes["out"].attributes( "/plane" )["a"] )

	def testDeleteExisting( self ) :

		plane = GafferScene.Plane()

		aAttributes = GafferScene.CustomAttributes()
		aAttributes["in"].setInput( plane["out"] )
		a = Gaffer.NameValuePlug( "a", IECore.IntData( 1 ) )
		aAttributes["attributes"].addChild( a )

		bAttributes = GafferScene.CustomAttributes()
		bAttributes["in"].setInput( plane["out"] )
		b = Gaffer.NameValuePlug( "b", IECore.IntData( 2 ) )
		bAttributes["attributes"].addChild( b )

		copyAttributes = GafferScene.CopyAttributes()
		copyAttributes["in"].setInput( aAttributes["out"] )
		copyAttributes["source"].setInput( bAttributes["out"] )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		copyAttributes["filter"].setInput( f["out"] )

		# Delete existing off.

		self.assertEqual(
			copyAttributes["out"].attributes( "/plane" ),
			IECore.CompoundObject( {
				"a" : aAttributes["out"].attributes( "/plane" )["a"],
				"b" : bAttributes["out"].attributes( "/plane" )["b"],
			} )
		)

		# Delete existing on.

		copyAttributes["deleteExisting"].setValue( True )
		self.assertEqual(
			copyAttributes["out"].attributes( "/plane" ),
			IECore.CompoundObject( {
				"b" : bAttributes["out"].attributes( "/plane" )["b"],
			} )
		)

		# We shouldn't even evaluate the incoming attributes if
		# we're going to delete them anyway.

		a["value"].setValue( 20 ) # Invalidate cache
		b["value"].setValue( 30 ) # Invalidate cache
		with Gaffer.PerformanceMonitor() as pm :
			copyAttributes["out"].attributes( "/plane" )

		self.assertIn( bAttributes["out"]["attributes"], pm.allStatistics() )
		self.assertNotIn( aAttributes["out"]["attributes"], pm.allStatistics() )

	def testSourceLocation( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		sphereAttributes = GafferScene.CustomAttributes()
		sphereAttributes["in"].setInput( sphere["out"] )
		sphereAttributes["attributes"].addChild( Gaffer.NameValuePlug( "a", IECore.IntData( 2 ) ) )

		parent = GafferScene.Parent()
		parent["parent"].setValue( "/" )
		parent["in"].setInput( plane["out"] )
		parent["children"][0].setInput( sphereAttributes["out"] )

		copyAttributes = GafferScene.CopyAttributes()
		copyAttributes["in"].setInput( parent["out"] )
		copyAttributes["source"].setInput( parent["out"] )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		copyAttributes["filter"].setInput( f["out"] )

		self.assertEqual(
			copyAttributes["out"].attributes( "/plane" ),
			parent["out"].attributes( "/plane" )
		)

		copyAttributes["sourceLocation"].setValue( "/sphere" )
		self.assertEqual(
			copyAttributes["out"].attributes( "/plane" ),
			parent["out"].attributes( "/sphere" )
		)

	def testRanges( self ) :

		script = Gaffer.ScriptNode()
		script["copy"] = GafferScene.CopyAttributes()
		script["box"] = Gaffer.Box()
		script["box"]["copy"] = GafferScene.CopyAttributes()

		self.assertEqual(
			list( GafferScene.CopyAttributes.Range( script ) ),
			[ script["copy"] ],
		)
		self.assertEqual(
			list( GafferScene.CopyAttributes.RecursiveRange( script ) ),
			[ script["copy"], script["box"]["copy"] ],
		)

	def testNonExistentSourceLocation( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ "/..." ] ) )

		sphereAttributes = GafferScene.CustomAttributes()
		sphereAttributes["in"].setInput( sphere["out"] )
		sphereAttributes["filter"].setInput( allFilter["out"] )
		sphereAttributes["attributes"].addChild( Gaffer.NameValuePlug( "test", 1 ) )

		copyAttributes = GafferScene.CopyAttributes()
		copyAttributes["in"].setInput( plane["out"] )
		copyAttributes["filter"].setInput( allFilter["out"] )
		copyAttributes["attributes"].setValue( "*" )

		# Default source location does not exist in source

		copyAttributes["source"].setInput( sphereAttributes["out"] )
		self.assertEqual( copyAttributes["out"].attributes( "/plane" ), IECore.CompoundObject() )

		# Custom source location does not exist in source

		copyAttributes["sourceLocation"].setValue( "/road/to/nowhere" )
		self.assertEqual( copyAttributes["out"].attributes( "/plane" ), IECore.CompoundObject() )

		# Valid source location

		copyAttributes["sourceLocation"].setValue( "/sphere" )
		self.assertEqual( copyAttributes["out"].attributes( "/plane" ), sphereAttributes["out"].attributes( "/sphere" ) )

	def testDeleteSourceLocation( self ) :

		sphere = GafferScene.Sphere()

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		sphereAttributes = GafferScene.CustomAttributes()
		sphereAttributes["in"].setInput( sphere["out"] )
		sphereAttributes["filter"].setInput( sphereFilter["out"] )
		sphereAttributes["attributes"].addChild( Gaffer.NameValuePlug( "test", 1 ) )

		prune = GafferScene.Prune()
		prune["in"].setInput( sphereAttributes["out"] )

		copy = GafferScene.CopyAttributes()
		copy["in"].setInput( sphere["out"] )
		copy["source"].setInput( prune["out"] )
		copy["filter"].setInput( sphereFilter["out"] )
		copy["attributes"].setValue( "*" )

		self.assertScenesEqual( copy["out"], sphereAttributes["out"] )
		prune["filter"].setInput( sphereFilter["out"] )
		self.assertScenesEqual( copy["out"], sphere["out"] )

if __name__ == "__main__":
	unittest.main()
