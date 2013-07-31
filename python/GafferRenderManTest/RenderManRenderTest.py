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

import os
import unittest
import subprocess

import IECore

import Gaffer
import GafferScene
import GafferRenderMan
import GafferRenderManTest

class RenderManRenderTest( GafferRenderManTest.RenderManTestCase ) :

	__scriptFileName = "/tmp/test.gfr"
		
	def testBoundsAndImageOutput( self ) :
	
		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["plane"]["transform"]["translate"].setValue( IECore.V3f( 0, 0, -5 ) )
		
		s["displays"] = GafferScene.Displays()
		s["displays"].addDisplay(
			"beauty",
			IECore.Display(
				"/tmp/test.tif",
				"tiff",
				"rgba",
				{}
			)
		)
		s["displays"]["in"].setInput( s["plane"]["out"] )
		
		s["render"] = GafferRenderMan.RenderManRender()
		s["render"]["in"].setInput( s["displays"]["out"] )
		s["render"]["mode"].setValue( "generate" )
		
		s["render"]["ribFileName"].setValue( "/tmp/test.rib" )

		s["fileName"].setValue( "/tmp/test.gfr" )
		s.save()
		
		s["render"].execute( [ Gaffer.Context.current() ] )
		
		self.assertTrue( os.path.exists( "/tmp/test.rib" ) )
		
		p = subprocess.Popen(
			"renderdl " + "/tmp/test.rib",
			shell = True,
			stderr = subprocess.PIPE
		)
		p.wait()
		
		self.failIf( "exceeded its bounds" in "".join( p.stderr.readlines() ) )
		
		self.assertTrue( os.path.exists( "/tmp/test.tif" ) )
	
	def testCameraMotionBlur( self ) :
	
		s = Gaffer.ScriptNode()

		s["camera"] = GafferScene.Camera()
		
		s["attributes"] = GafferScene.StandardAttributes()
		s["attributes"]["in"].setInput( s["camera"]["out"] )
		
		s["options"] = GafferScene.StandardOptions()
		s["options"]["in"].setInput( s["attributes"]["out"] )
		s["options"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["options"]["options"]["renderCamera"]["value"].setValue( "/camera" )
		
		s["render"] = GafferRenderMan.RenderManRender()
		s["render"]["in"].setInput( s["options"]["out"] )
		s["render"]["mode"].setValue( "generate" )
		
		s["render"]["ribFileName"].setValue( "/tmp/test.rib" )

		s["fileName"].setValue( "/tmp/test.gfr" )
		s.save()
		
		s["render"].execute( [ Gaffer.Context.current() ] )
		
		self.assertTrue( os.path.exists( "/tmp/test.rib" ) )
		
		# camera motion off, we should have no motion statements
		
		r = "".join( file( "/tmp/test.rib" ).readlines() )
		self.failIf( "MotionBegin" in r )
		
		# camera motion on, we should have no motion statements

		s["options"]["options"]["cameraBlur"]["enabled"].setValue( True )
		s["options"]["options"]["cameraBlur"]["value"].setValue( True )

		s["render"].execute( [ Gaffer.Context.current() ] )
		
		r = "".join( file( "/tmp/test.rib" ).readlines() )
		self.failUnless( "MotionBegin" in r )
		
		# motion disabled on camera object, we should have no motion statements
		# even though motion blur is enabled in the globals.
		
		s["attributes"]["attributes"]["transformBlur"]["enabled"].setValue( True )
		s["attributes"]["attributes"]["transformBlur"]["value"].setValue( False )
	
		s["render"].execute( [ Gaffer.Context.current() ] )
		
		r = "".join( file( "/tmp/test.rib" ).readlines() )
		self.failIf( "MotionBegin" in r )	
		
		# motion enabled on camera object, with extra samples specified. we should
		# have a motion statement with multiple segments
		
		s["attributes"]["attributes"]["transformBlur"]["value"].setValue( True )
		s["attributes"]["attributes"]["transformBlurSegments"]["enabled"].setValue( True )
		s["attributes"]["attributes"]["transformBlurSegments"]["value"].setValue( 5 )
		
		s["render"].execute( [ Gaffer.Context.current() ] )
		
		def motionTimes( ribFileName ) :
		
			for line in file( ribFileName ).readlines() :
				if "MotionBegin" in line :
					times = line.partition( "[" )[2].partition( "]" )[0]
					times = times.strip().split()
					return [ float( t ) for t in times ]
			
			return []
				
		self.assertEqual( len( motionTimes( "/tmp/test.rib" ) ), 6 )
		
		# different shutter times
		
		s["attributes"]["attributes"]["transformBlurSegments"]["enabled"].setValue( False )
		s["options"]["options"]["shutter"]["enabled"].setValue( True )
		
		s["render"].execute( [ Gaffer.Context.current() ] )
		
		self.assertEqual( motionTimes( "/tmp/test.rib" ), [ 0.75, 1.25 ] )
		
		s["options"]["options"]["shutter"]["value"].setValue( IECore.V2f( -0.1, 0.3 ) )
		
		s["render"].execute( [ Gaffer.Context.current() ] )
		
		self.assertEqual( motionTimes( "/tmp/test.rib" ), [ 0.9, 1.3 ] )
	
	def testDynamicLoadProcedural( self ) :
	
		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
				
		s["render"] = GafferRenderMan.RenderManRender()
		s["render"]["in"].setInput( s["plane"]["out"] )
		s["render"]["mode"].setValue( "generate" )
		
		s["render"]["ribFileName"].setValue( "/tmp/test.rib" )

		s["fileName"].setValue( "/tmp/test.gfr" )
		s.save()
		
		s["render"].execute( [ Gaffer.Context.current() ] )
		
		self.assertTrue( os.path.exists( "/tmp/test.rib" ) )
		
		rib = "\n".join( file( "/tmp/test.rib" ).readlines() )
		self.assertTrue( "DynamicLoad" in rib )
		self.assertFalse( "Polygon" in rib )
	
	def testDirectoryCreation( self ) :
	
		s = Gaffer.ScriptNode()
		s["variables"].addMember( "renderDirectory", "/tmp/renderTests" )
		s["variables"].addMember( "ribDirectory", "/tmp/ribTests" )
		
		s["plane"] = GafferScene.Plane()
		
		s["displays"] = GafferScene.Displays()
		s["displays"]["in"].setInput( s["plane"]["out"] )
		s["displays"].addDisplay(
			"beauty",
			IECore.Display(
				"$renderDirectory/test.####.exr",
				"exr",
				"rgba",
				{}
			)
		)
		
		s["render"] = GafferRenderMan.RenderManRender()
		s["render"]["in"].setInput( s["displays"]["out"] )
		s["render"]["ribFileName"].setValue( "$ribDirectory/test.####.rib" )
		s["render"]["mode"].setValue( "generate" )
		
		self.assertFalse( os.path.exists( "/tmp/renderTests" ) )
		self.assertFalse( os.path.exists( "/tmp/ribTests" ) )
		self.assertFalse( os.path.exists( "/tmp/ribTests/test.0001.rib" ) )
		
		s["fileName"].setValue( "/tmp/test.gfr" )
		
		s["render"].execute( [ s.context() ] )
		
		self.assertTrue( os.path.exists( "/tmp/renderTests" ) )
		self.assertTrue( os.path.exists( "/tmp/ribTests" ) )
		self.assertTrue( os.path.exists( "/tmp/ribTests/test.0001.rib" ) )

		# check that having the directories already exist is ok too
		
		s["render"].execute( [ s.context() ] )

		self.assertTrue( os.path.exists( "/tmp/renderTests" ) )
		self.assertTrue( os.path.exists( "/tmp/ribTests" ) )
		self.assertTrue( os.path.exists( "/tmp/ribTests/test.0001.rib" ) )

	def testTypeNamePrefixes( self ) :
	
		self.assertTypeNamesArePrefixed( GafferRenderMan )
		self.assertTypeNamesArePrefixed( GafferRenderManTest )

	def testDefaultNames( self ) :
	
		self.assertDefaultNamesAreCorrect( GafferRenderMan )
		self.assertDefaultNamesAreCorrect( GafferRenderManTest )
		
	def setUp( self ) :
	
		for f in (
			"/tmp/test.tif",
			"/tmp/test.rib",
			"/tmp/test.gfr",
			"/tmp/renderTests",
			"/tmp/ribTests/test.0001.rib",
			"/tmp/ribTests",			
		) :
			if os.path.isfile( f ) :
				os.remove( f )
			elif os.path.isdir( f ) :
				os.rmdir( f )

	def tearDown( self ) :
	
		self.setUp()
				
if __name__ == "__main__":
	unittest.main()
