##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import GafferTest
import GafferScene
import GafferArnold

class ArnoldRenderTest( GafferTest.TestCase ) :

	__scriptFileName = "/tmp/test.gfr"
	
	def testExecute( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["plane"] = GafferScene.Plane()
		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["mode"].setValue( "generate" )
		s["render"]["in"].setInput( s["plane"]["out"] )
		
		s["expression"] = Gaffer.Expression()
		s["expression"]["engine"].setValue( "python" )
		s["expression"]["expression"].setValue( "parent['render']['fileName'] = '/tmp/test.%d.ass' % int( context['frame'] )" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()
		
		p = subprocess.Popen(
			"gaffer execute " + self.__scriptFileName + " -frames 1-3",
			shell=True,
			stderr = subprocess.PIPE,
		)
		p.wait()
		self.failIf( p.returncode )
		
		for i in range( 1, 4 ) :
			self.failUnless( os.path.exists( "/tmp/test.%d.ass" % i ) )

	def testWaitForImage( self ) :
	
		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		
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
		
		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["displays"]["out"] )
		
		s["render"]["verbosity"].setValue( 1 )
		s["render"]["fileName"].setValue( "/tmp/test.ass" )

		s["fileName"].setValue( self.__scriptFileName )
		
		s["render"].execute( [ Gaffer.Context.current() ] )
			
		self.failUnless( os.path.exists( "/tmp/test.tif" ) )		
	
	def testExecuteWithStringSubstitutions( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["plane"] = GafferScene.Plane()
		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["mode"].setValue( "generate" )
		s["render"]["in"].setInput( s["plane"]["out"] )
		s["render"]["fileName"].setValue( "/tmp/test.####.ass" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()
		
		p = subprocess.Popen(
			"gaffer execute " + self.__scriptFileName + " -frames 1-3",
			shell=True,
			stderr = subprocess.PIPE,
		)
		p.wait()
		self.failIf( p.returncode )
		
		for i in range( 1, 4 ) :
			self.failUnless( os.path.exists( "/tmp/test.%04d.ass" % i ) )
	
	def testImageOutput( self ) :
	
		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		
		s["displays"] = GafferScene.Displays()
		s["displays"].addDisplay(
			"beauty",
			IECore.Display(
				"/tmp/test.####.tif",
				"tiff",
				"rgba",
				{}
			)
		)
		s["displays"]["in"].setInput( s["plane"]["out"] )
		
		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["displays"]["out"] )
		
		s["render"]["verbosity"].setValue( 1 )
		s["render"]["fileName"].setValue( "/tmp/test.####.ass" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()
		
		c = Gaffer.Context()
		for i in range( 1, 4 ) :
			c.setFrame( i )
			with c :
				s["render"].execute( [ Gaffer.Context.current() ] )
			
		for i in range( 1, 4 ) :
			self.failUnless( os.path.exists( "/tmp/test.%04d.tif" % i ) )		
	
	def testTypeNamePrefixes( self ) :
	
		self.assertTypeNamesArePrefixed( GafferArnold )
	
	def testDefaultNames( self ) :
	
		self.assertDefaultNamesAreCorrect( GafferArnold )
	
	
	def setUp( self ) :
	
		if os.path.exists( "/tmp/test.tif" ) :
			os.remove( "/tmp/test.tif" )
				
		for i in range( 1, 4 ) :
			if os.path.exists( "/tmp/test.%d.ass" % i ) :
				os.remove( "/tmp/test.%d.ass" % i )
			if os.path.exists( "/tmp/test.%04d.ass" % i ) :
				os.remove( "/tmp/test.%04d.ass" % i )
			if os.path.exists( "/tmp/test.%04d.tif" % i ) :
				os.remove( "/tmp/test.%04d.tif" % i )
				
if __name__ == "__main__":
	unittest.main()
