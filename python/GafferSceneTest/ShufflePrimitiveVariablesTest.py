##########################################################################
#
#  Copyright (c) 2020, Image Engine Design Inc. All rights reserved.
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

class ShufflePrimitiveVariablesTest( GafferSceneTest.SceneTestCase ) :

	def testShuffles( self ) :

		sphere = GafferScene.Sphere()
		extraVariables = GafferScene.PrimitiveVariables()
		extraVariables["in"].setInput( sphere["out"] )
		extraVariables["primitiveVariables"].addChild( Gaffer.NameValuePlug( "ten", 10 ) )
		extraVariables["primitiveVariables"].addChild( Gaffer.NameValuePlug( "twenty", 20 ) )
		shuffles = GafferScene.ShufflePrimitiveVariables()
		shuffles["in"].setInput( extraVariables["out"] )
		shuffles["shuffles"].addChild( Gaffer.ShufflePlug( "P", "Pref" ) )

		# Not filtered to anything, so should be a perfect pass through.
		self.assertScenesEqual( extraVariables["out"], shuffles["out"] )
		self.assertSceneHashesEqual( extraVariables["out"], shuffles["out"] )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )
		shuffles["filter"].setInput( sphereFilter["out"] )
		original = extraVariables["out"].object( "/sphere" )
		result = shuffles["out"].object( "/sphere" )
		self.assertEqual( set( result.keys() ), set( original.keys() ) | { "Pref" } )
		self.assertEqual( result["Pref"], result["P"] )

		# shuffle something that doesn't exist
		shuffles["shuffles"].addChild( Gaffer.ShufflePlug( "fake", "wontExist" ) )
		result = shuffles["out"].object( "/sphere" )
		self.assertEqual( set( result.keys() ), set( original.keys() ) | { "Pref" } )

		# shuffle with wildcards
		shuffles["shuffles"][1]["source"].setValue( "t*n*" )
		shuffles["shuffles"][1]["destination"].setValue( "user:${source}" )
		result = shuffles["out"].object( "/sphere" )
		self.assertEqual( set( result.keys() ), set( original.keys() ) | { "Pref", "user:ten", "user:twenty" } )
		self.assertEqual( result["Pref"], result["P"] )
		self.assertEqual( result["user:ten"], result["ten"] )
		self.assertEqual( result["user:twenty"], result["twenty"] )

		# delete source primvars
		shuffles["shuffles"][0]["deleteSource"].setValue( True )
		shuffles["shuffles"][1]["deleteSource"].setValue( True )
		result = shuffles["out"].object( "/sphere" )
		self.assertEqual( set( result.keys() ), { "Pref", "N", "uv", "user:ten", "user:twenty" } )
		self.assertEqual( result["Pref"], original["P"] )
		self.assertEqual( result["user:ten"], original["ten"] )
		self.assertEqual( result["user:twenty"], original["twenty"] )

	def testBoundUpdate( self ) :

		sphere1 = GafferScene.Sphere()
		sphere2 = GafferScene.Sphere()
		sphere2["radius"].setValue( 2 )

		group = GafferScene.Group()
		group["in"][0].setInput( sphere1["out"] )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )

		stashP = GafferScene.ShufflePrimitiveVariables()
		stashP["in"].setInput( group["out"] )
		stashP["filter"].setInput( sphereFilter["out"] )
		stashP["shuffles"].addChild( Gaffer.ShufflePlug( "P", "Pref" ) )

		# P is unchanged, we want a perfect pass through of the input bounds.
		self.assertScenesEqual( stashP["out"], group["out"], checks = { "bound" } )
		self.assertSceneHashesEqual( stashP["out"], group["out"], checks = { "bound" } )

		copy = GafferScene.CopyPrimitiveVariables()
		copy["in"].setInput( stashP["out"] )
		copy["source"].setInput( sphere2["out"] )
		copy["filter"].setInput( sphereFilter["out"] )
		copy["sourceLocation"].setValue( "/sphere" )
		copy["primitiveVariables"].setValue( "P" )

		restoreP = GafferScene.ShufflePrimitiveVariables()
		restoreP["in"].setInput( copy["out"] )
		restoreP["filter"].setInput( sphereFilter["out"] )
		restoreP["shuffles"].addChild( Gaffer.ShufflePlug( "Pref", "P" ) )

		# P is changed, we need to update bounds
		self.assertSceneValid( restoreP["out"] )
		self.assertNotEqual( restoreP["out"].bound( "/" ), copy["out"].bound( "/" ) )
		self.assertNotEqual( restoreP["out"].bound( "/group" ), copy["out"].bound( "/" ) )
		self.assertNotEqual( restoreP["out"].bound( "/group/sphere" ), copy["out"].bound( "/" ) )

		# If we turn off "adjustBounds", we want a perfect pass through of the input bounds.
		restoreP["adjustBounds"].setValue( False )
		self.assertScenesEqual( restoreP["out"], copy["out"], checks = { "bound" } )
		self.assertSceneHashesEqual( restoreP["out"], copy["out"], checks = { "bound" } )

		# If "adjustBounds" is on, but the shuffle is disabled, we also want
		# a perfect pass through of the input bounds.
		restoreP["adjustBounds"].setValue( True )
		restoreP["shuffles"][0]["enabled"].setValue( False )
		self.assertScenesEqual( restoreP["out"], copy["out"], checks = { "bound" } )
		self.assertSceneHashesEqual( restoreP["out"], copy["out"], checks = { "bound" } )

if __name__ == "__main__":
	unittest.main()
