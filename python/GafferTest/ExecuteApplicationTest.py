##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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
import subprocess
import unittest

import Gaffer
import GafferTest

class ExecuteApplicationTest( unittest.TestCase ) :

	__scriptFileName = "/tmp/executeScript.gfr"
	__outputFileName = "/tmp/sphere.cob"

	def testErrorReturnStatusForMissingScript( self ) :
		
		p = subprocess.Popen(
			"gaffer execute thisScriptDoesNotExist",
			shell=True,
			stderr = subprocess.PIPE,
		)
		p.wait()
		
		self.failUnless( "thisScriptDoesNotExist" in "".join( p.stderr.readlines() ) )
		self.failUnless( p.returncode )
	
	def testExecuteWriteNode( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["sphere"] = GafferTest.SphereNode()
		s["write"] = Gaffer.WriteNode()
		s["write"]["in"].setInput( s["sphere"]["out"] )
		s["write"]["fileName"].setValue( self.__outputFileName )
			
		s["fileName"].setValue( self.__scriptFileName )
		s.save()		
	
		self.failIf( os.path.exists( self.__outputFileName ) )
		p = subprocess.Popen(
			"gaffer execute " + self.__scriptFileName,
			shell=True,
			stderr = subprocess.PIPE,
		)
		p.wait()
	
		print "".join( p.stderr.readlines() )
	
		self.failUnless( os.path.exists( self.__outputFileName ) )
		self.failIf( p.returncode )
	
	def tearDown( self ) :
	
		for f in [
			self.__scriptFileName,
			self.__outputFileName,
		] :
			if os.path.exists( f ) :
				os.remove( f )
	
if __name__ == "__main__":
	unittest.main()
	
