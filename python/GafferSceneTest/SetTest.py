##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

class SetTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Set()
		s["in"].setInput( p["out"] )

		s["paths"].setValue( IECore.StringVectorData( [ "/one", "/plane" ] ) )
		g = s["out"]["globals"].getValue()
		self.assertEqual( g.keys(), [ "gaffer:sets" ] )
		self.assertEqual( g["gaffer:sets"].keys(), [ "set" ] )
		self.assertEqual( set( g["gaffer:sets"]["set"].value.paths() ), set( [ "/one", "/plane" ] ) )

		s["name"].setValue( "shinyThings" )

		g = s["out"]["globals"].getValue()
		self.assertEqual( g.keys(), [ "gaffer:sets" ] )
		self.assertEqual( g["gaffer:sets"].keys(), [ "shinyThings" ] )
		self.assertEqual( set( g["gaffer:sets"]["shinyThings"].value.paths() ), set( [ "/one", "/plane" ] ) )

		s["paths"].setValue( IECore.StringVectorData( [ "/two", "/sphere" ] ) )

		g = s["out"]["globals"].getValue()
		self.assertEqual( g.keys(), [ "gaffer:sets" ] )
		self.assertEqual( g["gaffer:sets"].keys(), [ "shinyThings" ] )
		self.assertEqual( set( g["gaffer:sets"]["shinyThings"].value.paths() ), set( [ "/two", "/sphere" ] ) )

	def testInputNotModified( self ) :

		s1 = GafferScene.Set()
		s1["name"].setValue( "setOne" )
		s1["paths"].setValue( IECore.StringVectorData( [ "/one" ] ) )

		s2 = GafferScene.Set()
		s2["in"].setInput( s1["out"] )
		s2["name"].setValue( "setTwo" )
		s2["paths"].setValue( IECore.StringVectorData( [ "/two" ] ) )

		g1 = s1["out"]["globals"].getValue( _copy = False )
		self.assertEqual( g1.keys(), [ "gaffer:sets" ] )
		self.assertEqual( g1["gaffer:sets"].keys(), [ "setOne" ] )
		self.assertEqual( g1["gaffer:sets"]["setOne"].value.paths(), [ "/one" ] )

		g2 = s2["out"]["globals"].getValue( _copy = False )
		self.assertEqual( g2.keys(), [ "gaffer:sets" ] )
		self.assertEqual( set( g2["gaffer:sets"].keys() ), set( [ "setOne", "setTwo" ] ) )
		self.assertEqual( g2["gaffer:sets"]["setOne"].value.paths(), [ "/one" ] )
		self.assertEqual( g2["gaffer:sets"]["setTwo"].value.paths(), [ "/two" ] )

		self.assertEqual( g1.keys(), [ "gaffer:sets" ] )
		self.assertEqual( g1["gaffer:sets"].keys(), [ "setOne" ] )
		self.assertEqual( g1["gaffer:sets"]["setOne"].value.paths(), [ "/one" ] )

if __name__ == "__main__":
	unittest.main()
