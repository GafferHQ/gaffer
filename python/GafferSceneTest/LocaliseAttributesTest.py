##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
import GafferTest
import GafferScene
import GafferSceneTest

class LocaliseAttributesTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		# Hierarchy             Attributes
		# ---------             ----------
		#
		# /outerGroup                            b : outerGroupB, c : outerGroupC
		#    /innerGroup        a : innerGroupA, b : innerGroupB
		#        /plane         a : planeA
		#

		plane = GafferScene.Plane()

		innerGroup = GafferScene.Group()
		innerGroup["name"].setValue( "innerGroup" )
		innerGroup["in"][0].setInput( plane["out"] )

		outerGroup = GafferScene.Group()
		outerGroup["name"].setValue( "outerGroup" )
		outerGroup["in"][0].setInput( innerGroup["out"] )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/outerGroup/innerGroup/plane" ] ) )

		innerGroupFilter = GafferScene.PathFilter()
		innerGroupFilter["paths"].setValue( IECore.StringVectorData( [ "/outerGroup/innerGroup" ] ) )

		outerGroupFilter = GafferScene.PathFilter()
		outerGroupFilter["paths"].setValue( IECore.StringVectorData( [ "/outerGroup" ] ) )

		planeAttributes = GafferScene.CustomAttributes()
		planeAttributes["in"].setInput( outerGroup["out"] )
		planeAttributes["filter"].setInput( planeFilter["out"] )
		planeAttributes["attributes"].addChild( Gaffer.NameValuePlug( "a", "planeA" ) )

		innerGroupAttributes = GafferScene.CustomAttributes()
		innerGroupAttributes["in"].setInput( planeAttributes["out"] )
		innerGroupAttributes["filter"].setInput( innerGroupFilter["out"] )
		innerGroupAttributes["attributes"].addChild( Gaffer.NameValuePlug( "a", "innerGroupA" ) )
		innerGroupAttributes["attributes"].addChild( Gaffer.NameValuePlug( "b", "innerGroupB" ) )

		outerGroupAttributes = GafferScene.CustomAttributes()
		outerGroupAttributes["in"].setInput( innerGroupAttributes["out"] )
		outerGroupAttributes["filter"].setInput( outerGroupFilter["out"] )
		outerGroupAttributes["attributes"].addChild( Gaffer.NameValuePlug( "b", "outerGroupB" ) )
		outerGroupAttributes["attributes"].addChild( Gaffer.NameValuePlug( "c", "outerGroupC" ) )

		# No filter, shouldn't do anything.

		localiseAttributes = GafferScene.LocaliseAttributes()
		localiseAttributes["in"].setInput( outerGroupAttributes["out"] )

		self.assertScenesEqual( localiseAttributes["out"], localiseAttributes["in"] )
		self.assertSceneHashesEqual( localiseAttributes["out"], localiseAttributes["in"] )

		# Filter, but no attributes specified. Still no effect on scenes.

		localiseAttributes["filter"].setInput( planeFilter["out"] )
		localiseAttributes["attributes"].setValue( "" )
		self.assertScenesEqual( localiseAttributes["out"], localiseAttributes["in"] )

		# Localise everything, but only for the plane.

		localiseAttributes["attributes"].setValue( "*" )
		self.assertEqual(
			localiseAttributes["out"].attributes( "/outerGroup" ),
			localiseAttributes["in"].attributes( "/outerGroup" )
		)
		self.assertEqual(
			localiseAttributes["out"].attributes( "/outerGroup/innerGroup" ),
			localiseAttributes["in"].attributes( "/outerGroup/innerGroup" )
		)
		self.assertEqual(
			localiseAttributes["out"].attributes( "/outerGroup/innerGroup/plane" ),
			localiseAttributes["in"].fullAttributes( "/outerGroup/innerGroup/plane" )
		)

		# Localise a subset of the attributes.

		localiseAttributes["attributes"].setValue( "b" )
		self.assertEqual(
			localiseAttributes["out"].attributes( "/outerGroup/innerGroup/plane" ),
			IECore.CompoundObject( {
				"a" : IECore.StringData( "planeA" ),
				"b" : IECore.StringData( "innerGroupB" ),
			} )
		)

		# Localise a different subset of the attributes.

		localiseAttributes["attributes"].setValue( "c" )
		self.assertEqual(
			localiseAttributes["out"].attributes( "/outerGroup/innerGroup/plane" ),
			IECore.CompoundObject( {
				"a" : IECore.StringData( "planeA" ),
				"c" : IECore.StringData( "outerGroupC" ),
			} )
		)

	def testDirtyPropagation( self ) :

		standardAttributes = GafferScene.StandardAttributes()
		localiseAttributes = GafferScene.LocaliseAttributes()
		localiseAttributes["in"].setInput( standardAttributes["out"] )

		cs = GafferTest.CapturingSlot( localiseAttributes.plugDirtiedSignal() )

		standardAttributes["attributes"]["visibility"]["enabled"].setValue( True )
		self.assertIn( localiseAttributes["out"]["attributes"], { x[0] for x in cs } )

		del cs[:]
		localiseAttributes["attributes"].setValue( "x" )
		self.assertIn( localiseAttributes["out"]["attributes"], { x[0] for x in cs } )

if __name__ == "__main__":
	unittest.main()
