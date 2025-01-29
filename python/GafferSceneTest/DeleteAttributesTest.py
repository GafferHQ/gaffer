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

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class DeleteAttributesTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		p = GafferScene.Plane()

		a = GafferScene.StandardAttributes()
		a["attributes"]["doubleSided"]["enabled"].setValue( True )
		a["attributes"]["visibility"]["enabled"].setValue( True )
		a["in"].setInput( p["out"] )

		d = GafferScene.DeleteAttributes()
		d["in"].setInput( a["out"] )

		self.assertScenesEqual( a["out"], d["out"] )
		self.assertSceneHashesEqual( a["out"], d["out"] )
		self.assertIn( "scene:visible", d["out"].attributes( "/plane" ) )
		self.assertIn( "doubleSided", d["out"].attributes( "/plane" ) )

		d["names"].setValue( "doubleSided" )

		self.assertSceneHashesNotEqual( a["out"], d["out"], checks = { "attributes" } )
		self.assertSceneHashesEqual( a["out"], d["out"], checks = self.allSceneChecks - { "attributes" } )

		self.assertIn( "scene:visible", d["out"].attributes( "/plane" ) )
		self.assertNotIn( "doubleSided", d["out"].attributes( "/plane" ) )

	def testWildcards( self ) :

		p = GafferScene.Plane()
		a = GafferScene.CustomAttributes()
		a["in"].setInput( p["out"] )

		a["attributes"].addChild( Gaffer.NameValuePlug( "a1", 1 ) )
		a["attributes"].addChild( Gaffer.NameValuePlug( "a2", 2 ) )
		a["attributes"].addChild( Gaffer.NameValuePlug( "b1", 1 ) )
		a["attributes"].addChild( Gaffer.NameValuePlug( "b2", 1 ) )

		d = GafferScene.DeleteAttributes()
		d["in"].setInput( a["out"] )
		self.assertEqual( set( d["out"].attributes( "/plane" ).keys() ), set( [ "a1", "a2", "b1", "b2" ] ) )

		d["names"].setValue( "a*" )
		self.assertEqual( set( d["out"].attributes( "/plane" ).keys() ), set( [ "b1", "b2" ] ) )

		d["names"].setValue( "*1" )
		self.assertEqual( set( d["out"].attributes( "/plane" ).keys() ), set( [ "a2", "b2" ] ) )

		d["names"].setValue( "*1 b2" )
		self.assertEqual( set( d["out"].attributes( "/plane" ).keys() ), set( [ "a2" ] ) )

		d["names"].setValue( "b2 a*" )
		self.assertEqual( set( d["out"].attributes( "/plane" ).keys() ), set( [ "b1" ] ) )

	def testDeleteAll( self ) :

		plane = GafferScene.Plane()
		deleteAttributes = GafferScene.DeleteAttributes()
		deleteAttributes["in"].setInput( plane["out"] )

		with Gaffer.PerformanceMonitor() as monitor :
			deleteAttributes["out"].attributes( "/plane" )
		self.assertEqual( monitor.plugStatistics( plane["out"]["attributes"] ).computeCount, 1 )

		Gaffer.ValuePlug.clearCache()
		deleteAttributes["names"].setValue( "*" )
		with Gaffer.PerformanceMonitor() as monitor :
			deleteAttributes["out"].attributes( "/plane" )
		self.assertEqual( monitor.plugStatistics( plane["out"]["attributes"] ).computeCount, 0 )

		Gaffer.ValuePlug.clearCache()
		deleteAttributes["names"].setValue( "" )
		deleteAttributes["invertNames"].setValue( True )
		with Gaffer.PerformanceMonitor() as monitor :
			deleteAttributes["out"].attributes( "/plane" )
		self.assertEqual( monitor.plugStatistics( plane["out"]["attributes"] ).computeCount, 0 )

	def testChangingInputAttributes( self ) :

		plane = GafferScene.Plane()
		attributes = GafferScene.CustomAttributes()
		attributes["in"].setInput( plane["out"] )
		deleteAttributes = GafferScene.DeleteAttributes()
		deleteAttributes["in"].setInput( attributes["out"] )
		deleteAttributes["names"].setValue( "a" )
		self.assertEqual( deleteAttributes["out"].attributes( "/plane" ), IECore.CompoundObject() )

		attributes["attributes"].addChild( Gaffer.NameValuePlug( "a", 10 ) )
		attributes["attributes"].addChild( Gaffer.NameValuePlug( "b", 10 ) )
		self.assertEqual( deleteAttributes["out"].attributes( "/plane" ), IECore.CompoundObject( { "b" : IECore.IntData( 10 ) } ) )

	def testChangingFilter( self ) :

		plane = GafferScene.Plane()
		attributes = GafferScene.CustomAttributes()
		attributes["in"].setInput( plane["out"] )
		attributes["attributes"].addChild( Gaffer.NameValuePlug( "a", 10 ) )

		deleteAttributes = GafferScene.DeleteAttributes()
		deleteAttributes["in"].setInput( attributes["out"] )
		deleteAttributes["names"].setValue( "a" )
		self.assertEqual( deleteAttributes["out"].attributes( "/plane" ), IECore.CompoundObject() )

		pathFilter = GafferScene.PathFilter()
		deleteAttributes["filter"].setInput( pathFilter["out"] )
		self.assertEqual( deleteAttributes["out"].attributes( "/plane" ), attributes["out"].attributes( "/plane" ) )

		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		self.assertEqual( deleteAttributes["out"].attributes( "/plane" ), IECore.CompoundObject() )

if __name__ == "__main__":
	unittest.main()
