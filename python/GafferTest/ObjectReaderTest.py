##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import IECore

import Gaffer
import GafferTest

class ObjectReaderTest( unittest.TestCase ) :

	def test( self ) :
	
		fileName = os.path.dirname( __file__ ) + "/images/checker.exr"
		
		node = Gaffer.ObjectReader()
		node["fileName"].setValue( fileName )
		self.assertEqual( node["fileName"].getValue(), fileName )
				
		# check that there are plugs for the reader parameters,
		# but not for the fileName parameter.
		
		reader = IECore.Reader.create( fileName )
		
		for k in reader.parameters().keys() :
			if k != "fileName" :
				self.failUnless( k in node["parameters"] )
		
		self.failIf( "fileName" in node["parameters"] )
		
		# check that the result is the same as loading it ourselves
		
		self.assertEqual( reader.read(), node["out"].getValue() )
		
		# check that changing the parameter plugs affects the loading
		
		dirtyCapturer = GafferTest.CapturingSlot( node.plugDirtiedSignal() )
		
		node["parameters"]["channels"].setValue( IECore.StringVectorData( [ "R" ] ) )
		
		self.assertEqual( len( dirtyCapturer ), 1 )
		self.assertEqual( dirtyCapturer[0][0].getName(), "out" )
		
		reader["channels"].setValue( IECore.StringVectorData( [ "R" ] ) )
						
		self.assertEqual( reader.read(), node["out"].getValue() )				
	
	def testChangingFileType( self ) :
	
		imageFileName = os.path.dirname( __file__ ) + "/images/checker.exr"
		cobFileName = os.path.dirname( __file__ ) + "/cobs/pSphereShape1.cob"
	
		node = Gaffer.ObjectReader()
		node["fileName"].setValue( imageFileName )
		
		reader = IECore.Reader.create( imageFileName )
		
		self.assertEqual( len( node["parameters"] ), len( reader.parameters() ) - 1 )
		for k in reader.parameters().keys() :
			if k != "fileName" :
				self.failUnless( k in node["parameters"] )
		
		
		node["fileName"].setValue( cobFileName )
		
		reader = IECore.Reader.create( cobFileName )
		
		self.assertEqual( len( node["parameters"] ), len( reader.parameters() ) - 1 )
		for k in reader.parameters().keys() :
			if k != "fileName" :
				self.failUnless( k in node["parameters"] )
		
		self.assertEqual( reader.read(), node["out"].getValue() )
		
	def testExtraneousPlugsAfterSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.ObjectReader()
		s["n"]["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker.exr" )

		self.failIf( "parameters1" in s["n"] )
		
		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.failIf( "parameters1" in s["n"] )
		
	def testReadAfterSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.ObjectReader()
		s["n"]["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker.exr" )

		r = s["n"]["out"].getValue()
		
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n"]["out"].getValue(), r )
	
	def testReadNoFilename( self ) :
	
		r = Gaffer.ObjectReader()
		self.assertEqual( r["out"].getValue(), r["out"].defaultValue() )
	
	def testExtraneousParameterPlugsAfterSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.ObjectReader()
		s["n"]["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker.exr" )

		originalParameterPlugNames = s["n"]["parameters"].keys()

		r = s["n"]["out"].getValue()
		
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n"]["parameters"].keys(), originalParameterPlugNames )
			
if __name__ == "__main__":
	unittest.main()
	
