##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

import os
import unittest

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class SubTreeTest( GafferSceneTest.SceneTestCase ) :
		
	def testPassThrough( self ) :
	
		a = GafferScene.AlembicSource()
		a["fileName"].setValue( os.path.dirname( __file__ ) + "/alembicFiles/animatedCube.abc" )	
		
		s = GafferScene.SubTree()
		s["in"].setInput( a["out"] )
		
		self.assertSceneValid( s["out"] )

		self.assertScenesEqual( a["out"], s["out"] )
		self.assertSceneHashesEqual( a["out"], s["out"] )
		self.assertTrue( a["out"].object( "/pCube1/pCubeShape1", _copy = False ).isSame( s["out"].object( "/pCube1/pCubeShape1", _copy = False ) ) )
		
	def testSubTree( self ) :
	
		a = GafferScene.AlembicSource()
		a["fileName"].setValue( os.path.dirname( __file__ ) + "/alembicFiles/animatedCube.abc" )	
		
		s = GafferScene.SubTree()
		s["in"].setInput( a["out"] )
		s["root"].setValue( "/pCube1" )
				
		self.assertSceneValid( s["out"] )
		self.assertScenesEqual( s["out"], a["out"], scenePlug2PathPrefix = "/pCube1" )
		self.assertTrue( a["out"].object( "/pCube1/pCubeShape1", _copy = False ).isSame( s["out"].object( "/pCubeShape1", _copy = False ) ) )

	def testForwardDeclarations( self ) :
	
		l = GafferSceneTest.TestLight()
		g = GafferScene.Group()
		g["in"].setInput( l["out"] )
		
		self.assertForwardDeclarationsValid( g["out"] )
		
		s = GafferScene.SubTree()
		s["in"].setInput( g["out"] )
		s["root"].setValue( "/group" )
		
		self.assertForwardDeclarationsValid( s["out"] )

	def testRootHashesEqual( self ) :
		
		a = GafferScene.AlembicSource()
		a["fileName"].setValue( os.path.dirname( __file__ ) + "/alembicFiles/animatedCube.abc" )	
		
		s = GafferScene.SubTree()
		s["in"].setInput( a["out"] )
		
		self.assertSceneValid( s["out"] )
		self.assertPathHashesEqual( a["out"], "/", s["out"], "/" )
	
	def testDisabled( self ) :
	
		p = GafferScene.Plane()
		g = GafferScene.Group()
		g["in"].setInput( p["out"] )
		
		s = GafferScene.SubTree()
		s["in"].setInput( g["out"] )
		s["root"].setValue( "/group" )
		s["enabled"].setValue( False )
		
		self.assertSceneValid( s["out"] )
		self.assertScenesEqual( s["out"], g["out"] )
		self.assertSceneHashesEqual( s["out"], g["out"] )

	def testForwardDeclarationsFromOmittedBranchAreOmitted( self ) :

		# /group
		#	/lightGroup1
		#		/light
		#	/lightGroup2
		#		/light
		#	/lightGroup
		#		/light
		#	/lightGroup10
		#		/light

		l = GafferSceneTest.TestLight()

		lg1 = GafferScene.Group()
		lg1["name"].setValue( "lightGroup1" )
		lg1["in"].setInput( l["out"] )

		lg2 = GafferScene.Group()
		lg2["name"].setValue( "lightGroup2" )
		lg2["in"].setInput( l["out"] )

		lg3 = GafferScene.Group()
		lg3["name"].setValue( "lightGroup" )
		lg3["in"].setInput( l["out"] )

		lg4 = GafferScene.Group()
		lg4["name"].setValue( "lightGroup10" )
		lg4["in"].setInput( l["out"] )

		g = GafferScene.Group()
		g["in"].setInput( lg1["out"] )
		g["in1"].setInput( lg2["out"] )
		g["in2"].setInput( lg3["out"] )
		g["in3"].setInput( lg4["out"] )

		self.assertForwardDeclarationsValid( g["out"] )

		# /light

		s = GafferScene.SubTree()
		s["in"].setInput( g["out"] )
		s["root"].setValue( "/group/lightGroup1" )

		forwardDeclarations = s["out"]["globals"].getValue()["gaffer:forwardDeclarations"]
		self.assertEqual( forwardDeclarations.keys(), [ "/light" ] )

		self.assertForwardDeclarationsValid( s["out"] )

		# with includeRoot == True
		
		s["includeRoot"].setValue( True )
		
		forwardDeclarations = s["out"]["globals"].getValue()["gaffer:forwardDeclarations"]
		self.assertEqual( forwardDeclarations.keys(), [ "/lightGroup1/light" ] )

		self.assertForwardDeclarationsValid( s["out"] )

	def testForwardDeclarationPassThroughWhenNoRoot( self ) :

		l = GafferSceneTest.TestLight()
		g = GafferScene.Group()
		g["in"].setInput( l["out"] )

		s = GafferScene.SubTree()
		s["in"].setInput( g["out"] )

		forwardDeclarations = s["out"]["globals"].getValue()["gaffer:forwardDeclarations"]
		self.assertEqual( forwardDeclarations.keys(), [ "/group/light" ] )
		self.assertForwardDeclarationsValid( s["out"] )

		s["root"].setValue( "/" )
		forwardDeclarations = s["out"]["globals"].getValue()["gaffer:forwardDeclarations"]
		self.assertEqual( forwardDeclarations.keys(), [ "/group/light" ] )
		self.assertForwardDeclarationsValid( s["out"] )

		# with includeRoot == True
		
		s["includeRoot"].setValue( True )
		
		s["root"].setValue( "" )
		forwardDeclarations = s["out"]["globals"].getValue()["gaffer:forwardDeclarations"]
		self.assertEqual( forwardDeclarations.keys(), [ "/group/light" ] )
		self.assertForwardDeclarationsValid( s["out"] )

		s["root"].setValue( "/" )
		forwardDeclarations = s["out"]["globals"].getValue()["gaffer:forwardDeclarations"]
		self.assertEqual( forwardDeclarations.keys(), [ "/group/light" ] )
		self.assertForwardDeclarationsValid( s["out"] )
		
	def testAffects( self ) :
	
		s = GafferScene.SubTree()
		
		for n in s["in"].keys() :
			a = s.affects( s["in"][n] )
			self.assertEqual( len( a ), 1 )
			self.assertTrue( a[0].isSame( s["out"][n] ) )

	def testIncludeRoot( self ) :
	
		a = GafferScene.AlembicSource()
		a["fileName"].setValue( os.path.dirname( __file__ ) + "/alembicFiles/animatedCube.abc" )	
		
		s = GafferScene.SubTree()
		s["in"].setInput( a["out"] )
		s["root"].setValue( "/pCube1" )
		s["includeRoot"].setValue( True )
				
		self.assertSceneValid( s["out"] )
		
		self.assertScenesEqual( s["out"], a["out"], pathsToIgnore = [ "/", ] )
		self.assertEqual( s["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "pCube1" ] ) )
		self.assertEqual( s["out"].bound( "/" ), a["out"].bound( "/pCube1" ) )		

		self.assertTrue( a["out"].object( "/pCube1/pCubeShape1", _copy = False ).isSame( s["out"].object( "/pCube1/pCubeShape1", _copy = False ) ) )

	def testRootBoundWithTransformedChild( self ) :
	
		a = GafferScene.AlembicSource()
		a["fileName"].setValue( os.path.dirname( __file__ ) + "/alembicFiles/animatedCube.abc" )	
		
		s = GafferScene.SubTree()
		s["in"].setInput( a["out"] )
		s["root"].setValue( "/pCube1" )
		s["includeRoot"].setValue( True )
				
		with Gaffer.Context() as c :
			
			c.setFrame( 10 )
			
			expectedRootBound = a["out"].bound( "/pCube1" )
			expectedRootBound = expectedRootBound.transform( a["out"].transform( "/pCube1" ) )
			
			self.assertEqual( s["out"].bound( "/" ), expectedRootBound )		

	def testIncludeRootPassesThroughWhenNoRootSpecified( self ) :
	
		a = GafferScene.AlembicSource()
		a["fileName"].setValue( os.path.dirname( __file__ ) + "/alembicFiles/animatedCube.abc" )	
		
		s = GafferScene.SubTree()
		s["in"].setInput( a["out"] )
		s["root"].setValue( "" )
		s["includeRoot"].setValue( True )
				
		self.assertSceneValid( s["out"] )

		self.assertScenesEqual( a["out"], s["out"] )
		self.assertSceneHashesEqual( a["out"], s["out"] )
		self.assertTrue( a["out"].object( "/pCube1/pCubeShape1", _copy = False ).isSame( s["out"].object( "/pCube1/pCubeShape1", _copy = False ) ) )

	def testForwardDeclarationsWithIncludeRoot( self ) :
	
		l = GafferSceneTest.TestLight()
		g = GafferScene.Group()
		g["in"].setInput( l["out"] )
		
		self.assertForwardDeclarationsValid( g["out"] )
		
		s = GafferScene.SubTree()
		s["in"].setInput( g["out"] )
		s["root"].setValue( "/group" )
		s["includeRoot"].setValue( True )
		
		forwardDeclarations = s["out"]["globals"].getValue()["gaffer:forwardDeclarations"]
		self.assertEqual( forwardDeclarations.keys(), [ "/group/light" ] )
		self.assertForwardDeclarationsValid( s["out"] )
			
if __name__ == "__main__":
	unittest.main()
