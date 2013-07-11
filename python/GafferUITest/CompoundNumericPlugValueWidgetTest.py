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

import Gaffer
import GafferTest
import GafferUI

class CompoundNumericPlugValueWidgetTest( unittest.TestCase ) :

	def test( self ) :
	
		n = Gaffer.Node()
		n["v1"]= Gaffer.V3fPlug()
		n["v2"]= Gaffer.V3fPlug()
		
		w = GafferUI.CompoundNumericPlugValueWidget( n["v1"] )
		self.assertTrue( w.getPlug().isSame( n["v1"] ) )
		self.assertTrue( w._row()[0].getPlug().isSame( n["v1"][0] ) )
		self.assertTrue( w._row()[1].getPlug().isSame( n["v1"][1] ) )
		self.assertTrue( w._row()[2].getPlug().isSame( n["v1"][2] ) )
		
		w.setPlug( n["v2"] )
		self.assertTrue( w.getPlug().isSame( n["v2"] ) )
		self.assertTrue( w._row()[0].getPlug().isSame( n["v2"][0] ) )
		self.assertTrue( w._row()[1].getPlug().isSame( n["v2"][1] ) )
		self.assertTrue( w._row()[2].getPlug().isSame( n["v2"][2] ) )
		
if __name__ == "__main__":
	unittest.main()
