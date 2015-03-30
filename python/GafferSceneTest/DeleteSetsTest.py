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

class DeleteSetsTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		s1 = GafferScene.Set()
		s1["name"].setValue("s1")
		s1["paths"].setValue( IECore.StringVectorData( ["/blah1"] ) )

		s2 = GafferScene.Set()
		s2["name"].setValue("s2")
		s2["in"].setInput( s1["out"] )
		s2["paths"].setValue( IECore.StringVectorData( ["/blah2"] ) )

		s3 = GafferScene.Set()
		s3["name"].setValue("s3")
		s3["in"].setInput( s2["out"] )
		s3["paths"].setValue( IECore.StringVectorData( ["/blah3"] ) )

		d = GafferScene.DeleteSets()
		d["in"].setInput(s3["out"])

		# no sets to delete, so everything should be intact:
		self.assertEqual( set( d["out"]["globals"].getValue()["gaffer:sets"].keys() ), set( ['s1','s2','s3'] ) )
		self.assertEqual( d["out"]["globals"].getValue()["gaffer:sets"]["s1"].value.paths(), ['/blah1'] )
		self.assertEqual( d["out"]["globals"].getValue()["gaffer:sets"]["s2"].value.paths(), ['/blah2'] )
		self.assertEqual( d["out"]["globals"].getValue()["gaffer:sets"]["s3"].value.paths(), ['/blah3'] )

		# delete s1 and s2:
		d["names"].setValue( "s1 s2" )
		self.assertEqual( set( d["out"]["globals"].getValue()["gaffer:sets"].keys() ), set( ['s3'] ) )
		self.assertEqual( d["out"]["globals"].getValue()["gaffer:sets"]["s3"].value.paths(), ['/blah3'] )

		# invert:
		d["invertNames"].setValue( True )
		self.assertEqual( set( d["out"]["globals"].getValue()["gaffer:sets"].keys() ), set( ['s1', 's2'] ) )
		self.assertEqual( d["out"]["globals"].getValue()["gaffer:sets"]["s1"].value.paths(), ['/blah1'] )
		self.assertEqual( d["out"]["globals"].getValue()["gaffer:sets"]["s2"].value.paths(), ['/blah2'] )

	def testWildcards( self ) :

		s1 = GafferScene.Set()
		s1["name"].setValue("a1")

		s2 = GafferScene.Set()
		s2["name"].setValue("a2")
		s2["in"].setInput( s1["out"] )

		s3 = GafferScene.Set()
		s3["name"].setValue("b1")
		s3["in"].setInput( s2["out"] )

		s4 = GafferScene.Set()
		s4["name"].setValue("b2")
		s4["in"].setInput( s3["out"] )

		d = GafferScene.DeleteSets()
		d["in"].setInput(s4["out"])

		self.assertEqual( set( d["out"]["globals"].getValue()["gaffer:sets"].keys() ), set( [ "a1", "a2", "b1", "b2" ] ) )

		d["names"].setValue( "a*" )
		self.assertEqual( set( d["out"]["globals"].getValue()["gaffer:sets"].keys() ), set( [ "b1", "b2" ] ) )

		d["names"].setValue( "*1" )
		self.assertEqual( set( d["out"]["globals"].getValue()["gaffer:sets"].keys() ), set( [ "a2", "b2" ] ) )

		d["names"].setValue( "*1 b2" )
		self.assertEqual( set( d["out"]["globals"].getValue()["gaffer:sets"].keys() ), set( [ "a2" ] ) )

		d["names"].setValue( "b2 a*" )
		self.assertEqual( set( d["out"]["globals"].getValue()["gaffer:sets"].keys() ), set( [ "b1" ] ) )

	def testAffects( self ) :

		d = GafferScene.DeleteSets()

		self.failUnless( d["out"]["globals"] in d.affects( d["in"]["globals"] ) )
		self.failUnless( d["out"]["globals"] in d.affects( d["names"] ) )
		self.failUnless( d["out"]["globals"] in d.affects( d["invertNames"] ) )

if __name__ == "__main__":
	unittest.main()
