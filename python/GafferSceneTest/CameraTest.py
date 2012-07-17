##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

class CameraTest( unittest.TestCase ) :

	def testConstruct( self ) :
	
		p = GafferScene.Camera()
		self.assertEqual( p.getName(), "Camera" )
		self.assertEqual( p["name"].getValue(), "camera" )
	
	def testCompute( self ) :
	
		p = GafferScene.Camera( inputs = {
			"resolution" : IECore.V2i( 200, 100 ),
			"projection" : "perspective",
			"fieldOfView" : 45,
		} )
	
		self.assertEqual( p["out"].object( "/" ), None )
		self.assertEqual( p["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( p["out"].bound( "/" ), IECore.Box3f() )
		self.assertEqual( p["out"].childNames( "/" ), IECore.StringVectorData( [ "camera" ] ) )
		
		self.assertEqual( p["out"].transform( "/camera" ), IECore.M44f() )
		self.assertEqual( p["out"].bound( "/camera" ), IECore.Box3f() )
		self.assertEqual( p["out"].childNames( "/camera" ), None )
		
		o = p["out"].object( "/camera" )
		self.failUnless( isinstance( o, IECore.Camera ) )
		self.assertEqual( o.parameters()["resolution"].value, IECore.V2i( 200, 100 ) )
		self.assertEqual( o.parameters()["projection"].value, "perspective" )
		self.assertEqual( o.parameters()["projection:fov"].value, 45 )
	
if __name__ == "__main__":
	unittest.main()
