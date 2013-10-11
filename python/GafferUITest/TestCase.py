##########################################################################
#  
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

import sys
import unittest

import GafferTest
import GafferUI

## A useful base class for creating test cases for the ui.
class TestCase( GafferTest.TestCase ) :
		
	def tearDown( self ) :
	
		# Here we check that there are no Widget instances knocking
		# around after each test has run. this provides good coverage
		# for the Widget lifetime problems that are all too easy to
		# create. First we clear any previous exception, as it can be
		# holding references to widgets that were active when the exception
		# was thrown (and unittest.TestCase will be reporting an error
		# anyway).
	
		if "_ExpectedFailure" in str( sys.exc_info()[0] ) :
			# the expected failure exception in the unittest module
			# unhelpfully also hangs on to exceptions, so we remove
			# that before calling exc_clear().
			sys.exc_info()[1].exc_info = ( None, None, None )
		
		sys.exc_clear()
				
		widgetInstances = self.__widgetInstances()
		self.assertEqual( widgetInstances, [] )
	
	def waitForIdle( self, count = 1 ) :
	
		self.__idleCount = 0
		def f() :
			
			self.__idleCount += 1
			
			if self.__idleCount >= count :
				GafferUI.EventLoop.mainEventLoop().stop()
				return False
			
			return True
			
		GafferUI.EventLoop.addIdleCallback( f )
		GafferUI.EventLoop.mainEventLoop().start()
		
	@staticmethod
	def __widgetInstances() :
	
		result = []
		# yes, this is accessing Widget internals. we could add a public method
		# to the widget to expose this information, but i'd rather not add yet
		# more methods if we can avoid it.
		for w in GafferUI.Widget._Widget__qtWidgetOwners.values() :
			if w() is not None :
				result.append( w() )
	
		return result
