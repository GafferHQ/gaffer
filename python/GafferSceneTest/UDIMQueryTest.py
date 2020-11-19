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
import math
import imath

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class UDIMQueryTest( GafferSceneTest.SceneTestCase ) :


	def test( self ) :

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ '/...' ] ) )

		rootFilter = GafferScene.PathFilter()
		rootFilter["paths"].setValue( IECore.StringVectorData( [ '/*' ] ) )

		plane0 = GafferScene.Plane()
		plane0["transform"]["translate"].setValue( imath.V3f( 2, 1, 0 ) )
		plane0["transform"]["scale"].setValue( imath.V3f( 2, 2, 1 ) )
		plane0["divisions"].setValue( imath.V2i( 10, 10 ) )

		group = GafferScene.Group()
		group["in"][0].setInput( plane0["out"] )

		udimQuery = GafferScene.UDIMQuery()
		udimQuery["in"].setInput( group["out"] )
		udimQuery["filter"].setInput( allFilter["out"] )

		def dictResult():
			c = udimQuery["out"].getValue().items()
			return { key0:{ key1:dict(val1.items()) for (key1,val1) in val0.items() } for (key0,val0) in c }

		# Test a basic single UDIM
		self.assertEqual( dictResult(), {'1001': {'/group/plane': {}}} )

		# Add an attribute
		udimQuery["attributes"].setValue( 'attributeA attributeB attributeC' )
		customAttributes0 = GafferScene.CustomAttributes()
		customAttributes0["attributes"].addChild( Gaffer.NameValuePlug( "attributeA", "test" ) )
		customAttributes0["in"].setInput( plane0["out"] )
		group["in"][0].setInput( customAttributes0["out"] )

		self.assertEqual( dictResult(), {'1001': {'/group/plane': {'attributeA': IECore.StringData( 'test' )}}} )

		# Add an alternate UV set based on P, using a projection camera
		projCam = GafferScene.Camera()
		projCam["transform"]["translate"].setValue( imath.V3f( 0.5, 0.5, 0 ) )
		projCam["projection"].setValue( 'orthographic' )
		projCam["orthographicAperture"].setValue( imath.V2f( 1 ) )
		group["in"][1].setInput( projCam["out"] )


		mapProjection = GafferScene.MapProjection()
		mapProjection["camera"].setValue( '/group/camera' )
		mapProjection["uvSet"].setValue( 'uvAlt' )
		mapProjection["filter"].setInput( allFilter["out"] )
		mapProjection["in"].setInput( group["out"] )

		udimQuery["in"].setInput( mapProjection["out"] )

		self.assertEqual( dictResult(), {'1001': {'/group/plane': {'attributeA': IECore.StringData( 'test' )}}} )

		udimQuery["uvSet"].setValue( 'uvAlt' )

		self.assertEqual( dictResult(), {i: {'/group/plane': {'attributeA': IECore.StringData( 'test' )}} for i in [ "1002", "1003", "1012", "1013" ] } )


		# Add two more objects
		plane1 = GafferScene.Plane()
		plane1["transform"]["translate"].setValue( imath.V3f( 6.5, 2.5, 0 ) )
		plane1["divisions"].setValue( imath.V2i( 10, 10 ) )

		customAttributes1 = GafferScene.CustomAttributes( "CustomAttributes1" )
		customAttributes1["in"].setInput( plane1["out"] )
		customAttributes1["filter"].setInput( allFilter["out"] )
		customAttributes1["attributes"].addChild( Gaffer.NameValuePlug( "attributeA", "baz" ) )
		customAttributes1["attributes"].addChild( Gaffer.NameValuePlug( "attributeB", 12 ) )

		plane2 = GafferScene.Plane()
		plane2["transform"]["translate"].setValue( imath.V3f( 8, 4, 0 ) )
		plane2["transform"]["scale"].setValue( imath.V3f( 2, 2, 1 ) )
		plane2["divisions"].setValue( imath.V2i( 10, 10 ) )

		group["in"][2].setInput( customAttributes1["out"] )
		group["in"][3].setInput( plane2["out"] )

		customAttributes2 = GafferScene.CustomAttributes( "CustomAttributes2" )
		customAttributes2["in"].setInput( group["out"] )
		customAttributes2["filter"].setInput( rootFilter["out"] )
		customAttributes2["attributes"].addChild( Gaffer.NameValuePlug( "attributeC", "inherited" ) )

		mapProjection["in"].setInput( customAttributes2["out"] )

		self.assertEqual( dictResult(), dict(
			[(i, {'/group/plane': {'attributeA': IECore.StringData( 'test' ), 'attributeC': IECore.StringData( 'inherited' )}}) for i in [ "1002", "1003", "1012", "1013" ]] +
			[("1027", {'/group/plane1': {'attributeA': IECore.StringData( 'baz' ), 'attributeB': IECore.IntData( 12 ), 'attributeC': IECore.StringData( 'inherited' )}})] +
			[(i, {'/group/plane2': {'attributeC': IECore.StringData( 'inherited' )}}) for i in ["1038", "1039", "1048", "1049"]]
 ) )

		# Switch back to default uv set so that everything lands on top of each other
		udimQuery["uvSet"].setValue( 'uv' )

		self.assertEqual( dictResult(),
			{ "1001" : {
				'/group/plane': {'attributeA': IECore.StringData( 'test' ), 'attributeC': IECore.StringData( 'inherited' )},
				'/group/plane1': {'attributeA': IECore.StringData( 'baz' ), 'attributeB': IECore.IntData( 12 ), 'attributeC': IECore.StringData( 'inherited' )},
				'/group/plane2': { 'attributeC': IECore.StringData( 'inherited' )}
			}})

	def testNameChangeOnly( self ) :

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ '/...' ] ) )

		plane0 = GafferScene.Plane()

		udimQuery = GafferScene.UDIMQuery()
		udimQuery["in"].setInput( plane0["out"] )
		udimQuery["filter"].setInput( allFilter["out"] )

		def dictResult():
			c = udimQuery["out"].getValue().items()
			return { key0:{ key1:dict(val1.items()) for (key1,val1) in val0.items() } for (key0,val0) in c }


		# Test a basic single UDIM
		initialHash = udimQuery["out"].hash()
		self.assertEqual( dictResult(), {'1001': {'/plane': {}}} )

		plane0["name"].setValue( "test" )
		self.assertNotEqual( initialHash, udimQuery["out"].hash() )
		self.assertEqual( dictResult(), {'1001': {'/test': {}}} )

if __name__ == "__main__":
	unittest.main()
