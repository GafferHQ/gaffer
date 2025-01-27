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

class VisibleSetDataTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		d = GafferScene.VisibleSetData()
		self.assertEqual( d.value, GafferScene.VisibleSet() )

		v1 = GafferScene.VisibleSet()
		v1.expansions = IECore.PathMatcher( [ "/a" ] )
		v1.inclusions = IECore.PathMatcher( [ "/b" ] )
		v1.exclusions = IECore.PathMatcher( [ "/c" ] )

		v2 = GafferScene.VisibleSet()
		v2.expansions = IECore.PathMatcher( [ "/d" ] )
		v2.inclusions = IECore.PathMatcher( [ "/e" ] )
		v2.exclusions = IECore.PathMatcher( [ "/f" ] )

		vd1a = GafferScene.VisibleSetData( v1 )
		vd1b = GafferScene.VisibleSetData( v1 )
		vd2 = GafferScene.VisibleSetData( v2 )

		self.assertEqual( vd1a.value, v1 )
		self.assertEqual( vd1b.value, v1 )
		self.assertEqual( vd2.value, v2 )

		self.assertEqual( vd1a, vd1b )
		self.assertNotEqual( vd1a, vd2 )

		self.assertEqual( vd1a.hash(), vd1b.hash() )
		self.assertNotEqual( vd1a.hash(), vd2.hash() )

		vd2c = vd2.copy()
		self.assertEqual( vd2c, vd2 )
		self.assertEqual( vd2c.hash(), vd2.hash() )

	def testSerialisation( self ) :

		v = GafferScene.VisibleSet()
		v.expansions = IECore.PathMatcher( [ "/a" ] )
		v.inclusions = IECore.PathMatcher( [ "/b" ] )
		v.exclusions = IECore.PathMatcher( [ "/c" ] )

		d = GafferScene.VisibleSetData( v )

		m = IECore.MemoryIndexedIO( IECore.CharVectorData(), [], IECore.IndexedIO.OpenMode.Write )

		d.save( m, "f" )

		m2 = IECore.MemoryIndexedIO( m.buffer(), [], IECore.IndexedIO.OpenMode.Read )
		d2 = IECore.Object.load( m2, "f" )

		self.assertEqual( d2, d )
		self.assertEqual( d2.hash(), d.hash() )
		self.assertEqual( d2.value, v )

	def testStoreInContext( self ) :

		v = GafferScene.VisibleSet()
		v.expansions = IECore.PathMatcher( [ "/a" ] )
		v.inclusions = IECore.PathMatcher( [ "/b" ] )
		v.exclusions = IECore.PathMatcher( [ "/c" ] )

		d = GafferScene.VisibleSetData( v )

		c = Gaffer.Context()
		c["v"] = d
		self.assertEqual( c["v"], d )

if __name__ == "__main__":
	unittest.main()
