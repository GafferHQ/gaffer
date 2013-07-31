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

class ObjectWriterTest( unittest.TestCase ) :

	__exrFileName = "/tmp/checker.exr"
	__tifFileName = "/tmp/checker.tif"
	__exrSequence = IECore.FileSequence( "/tmp/checker.####.exr 1-4" )

	def test( self ) :
	
		checker = os.path.dirname( __file__ ) + "/images/checker.exr"
		checker = IECore.Reader.create( checker ).read()
		
		node = Gaffer.ObjectWriter()
		node["fileName"].setValue( self.__exrFileName )
		node["in"].setValue( checker )
		
		self.assertEqual( node["fileName"].getValue(), self.__exrFileName )
		self.assertEqual( node["in"].getValue(), checker )
				
		# check that there are plugs for the writer parameters,
		# but not for the fileName parameter.
		
		writer = IECore.Writer.create( checker, self.__exrFileName )
		
		for k in writer.parameters().keys() :
			if k != "fileName" and k != "object" :
				self.failUnless( k in node["parameters"] )
		
		self.failIf( "fileName" in node["parameters"] )
		
		# check that saving it works
		
		self.failIf( os.path.exists( self.__exrFileName ) )
		node.execute( [ Gaffer.Context() ] )
		self.failUnless( os.path.exists( self.__exrFileName ) )
		
		checker2 = IECore.Reader.create( self.__exrFileName ).read()
		self.assertEqual( checker, checker2 )

	def testChangingFileType( self ) :
	
		checker = os.path.dirname( __file__ ) + "/images/checker.exr"
		checker = IECore.Reader.create( checker ).read()
		
		node = Gaffer.ObjectWriter()
		node["fileName"].setValue( self.__exrFileName )
		node["in"].setValue( checker )
				
		node["fileName"].setValue( self.__tifFileName )
		
		node.execute( [ Gaffer.Context() ] )
		self.failUnless( os.path.exists( self.__tifFileName ) )
		
		self.failUnless( IECore.TIFFImageReader.canRead( self.__tifFileName ) )

 	def testExtraneousPlugsAfterSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.ObjectWriter()
		s["n"]["fileName"].setValue( self.__exrFileName )

		self.failUnless( "parameters" in s["n"] )
		self.failIf( "parameters1" in s["n"] )
		
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.failUnless( "parameters" in s["n"] )
		self.failIf( "parameters1" in s["n"] )
		
	def testStringSubstitutions( self ) :
	
		checker = os.path.dirname( __file__ ) + "/images/checker.exr"
		checker = IECore.Reader.create( checker ).read()
		
		node = Gaffer.ObjectWriter()
		node["fileName"].setValue( self.__exrSequence.fileName )
		node["in"].setValue( checker )
		
		contexts = []
		for i in self.__exrSequence.frameList.asList() :
			context = Gaffer.Context()
			context.setFrame( i )
			contexts.append( context )

		node.execute( contexts )
		
		for f in self.__exrSequence.fileNames() :
			self.failUnless( os.path.exists( f ) )
		
	def tearDown( self ) :
		
		for f in [
			self.__tifFileName,
			self.__exrFileName,
		] + self.__exrSequence.fileNames() :
			if os.path.exists( f ) :
				os.remove( f )
	
if __name__ == "__main__":
	unittest.main()
	
