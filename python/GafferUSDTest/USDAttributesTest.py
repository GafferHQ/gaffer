##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Image Engine Design Inc nor the names of
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

import os
import collections
import pathlib
import unittest

import IECore

import Gaffer
import GafferUSD
import GafferScene
import GafferSceneTest

class USDAttributesTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		plane = GafferScene.Plane()
		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		attributes = GafferUSD.USDAttributes()
		attributes["in"].setInput( plane["out"] )
		attributes["filter"].setInput( planeFilter["out"] )

		self.assertEqual( attributes["out"].attributes( "/plane" ), IECore.CompoundObject() )

		expected = collections.OrderedDict( [
			( "usd:purpose", IECore.StringData( "default" ) ),
			( "usd:kind", IECore.StringData( "assembly" ) ),
		] )

		self.assertEqual( attributes["attributes"].keys(), list( expected.keys() ) )

		for name, value in expected.items() :
			self.assertEqual( attributes["attributes"][name]["name"].getValue(), name )
			self.assertEqual( attributes["attributes"][name]["enabled"].getValue(), False )
			self.assertEqual( attributes["attributes"][name]["value"].getValue(), value.value )
			attributes["attributes"][name]["enabled"].setValue( True )

		self.assertEqual( attributes["out"].attributes( "/plane" ), IECore.CompoundObject( expected ) )

	def testLoadFrom1_5( self ) :

		script = Gaffer.ScriptNode()
		script["fileName"].setValue( pathlib.Path( __file__ ).parent / "scripts" / "usdAttributes-1.5.15.0.gfr" )
		script.load()

		self.assertIn( "usd:kind", script["USDAttributes"]["attributes"].keys() )
		self.assertNotIn( "kind", script["USDAttributes"]["attributes"].keys() )
		self.assertEqual( script["USDAttributes"]["attributes"]["usd:kind"]["value"].getValue(), "group" )

if __name__ == "__main__":
	unittest.main()
