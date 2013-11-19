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
import GafferTest
import GafferUI
import GafferUITest
import GafferImage
import GafferImageUI

class ImageViewTest( GafferUITest.TestCase ) :

	def testFactory( self ) :
	
		image = GafferImage.Constant()
		view = GafferUI.View.create( image["out"] )
		
		self.assertTrue( isinstance( view, GafferImageUI.ImageView ) )
		self.assertTrue( view["in"].getInput().isSame( image["out"] ) )
		
	def testDeprecatedDeriving( self ) :
	
		class MyView( GafferImageUI.ImageView ) :
		
			def __init__( self, viewedPlug = None ) :
			
				GafferImageUI.ImageView.__init__( self, "MyView", Gaffer.ObjectPlug( "in", defaultValue = IECore.NullObject.defaultNullObject() ) )
				
				self["in"].setInput( viewedPlug )
				
				self.__preprocessor = Gaffer.Node()
				self.__preprocessor["in"] = Gaffer.ObjectPlug( defaultValue = IECore.NullObject.defaultNullObject() )
				self.__preprocessor["out"] = GafferImage.ImagePlug( direction = Gaffer.Plug.Direction.Out )
				self.__preprocessor["constant"] = GafferImage.Constant()
				self.__preprocessor["constant"]["format"].setValue( GafferImage.Format( 20, 20, 1 ) )
				self.__preprocessor["out"].setInput( self.__preprocessor["constant"]["out"] )
				
				self._setPreprocessor( self.__preprocessor )
					
		GafferUI.View.registerView( GafferTest.SphereNode.staticTypeId(), "out", MyView )

		sphere = GafferTest.SphereNode()
				
		view = GafferUI.View.create( sphere["out"] )
		self.assertTrue( isinstance( view, MyView ) )
		self.assertTrue( view["in"].getInput().isSame( sphere["out"] ) )
		self.assertTrue( isinstance( view["in"], Gaffer.ObjectPlug ) )
		view["exposure"].setValue( 1 )
		view["gamma"].setValue( 0.5 )
		
		view._update()
		
	def testDeriving( self ) :
	
		class MyView( GafferImageUI.ImageView ) :
		
			def __init__( self, viewedPlug = None ) :
			
				GafferImageUI.ImageView.__init__( self, "MyView" )
			
				converter = Gaffer.Node()
				converter["in"] = Gaffer.ObjectPlug( defaultValue = IECore.NullObject.defaultNullObject() )
				converter["out"] = GafferImage.ImagePlug( direction = Gaffer.Plug.Direction.Out )
				converter["constant"] = GafferImage.Constant()
				converter["constant"]["format"].setValue( GafferImage.Format( 20, 20, 1 ) )
				converter["out"].setInput( converter["constant"]["out"] )
				
				self._insertConverter( converter )
				
				self["in"].setInput( viewedPlug )
					
		GafferUI.View.registerView( GafferTest.SphereNode.staticTypeId(), "out", MyView )

		sphere = GafferTest.SphereNode()
				
		view = GafferUI.View.create( sphere["out"] )
		self.assertTrue( isinstance( view, MyView ) )
		self.assertTrue( view["in"].getInput().isSame( sphere["out"] ) )
		self.assertTrue( isinstance( view["in"], Gaffer.ObjectPlug ) )
		view["exposure"].setValue( 1 )
		view["gamma"].setValue( 0.5 )
		
		view._update()	
		
if __name__ == "__main__":
	unittest.main()
	
