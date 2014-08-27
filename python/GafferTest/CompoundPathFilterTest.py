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

import unittest

import Gaffer
import GafferTest

class CompoundPathFilterTest( GafferTest.TestCase ) :

	def test( self ) :

		f1 = Gaffer.FileNamePathFilter( [ "*.gfr" ] )
		f2 = Gaffer.FileNamePathFilter( [ "*.tif" ] )

		c = Gaffer.CompoundPathFilter()
		self.assertEqual( c.getFilters(), [] )

		c.addFilter( f1 )
		self.assertEqual( c.getFilters(), [ f1 ] )

		c.addFilter( f2 )
		self.assertEqual( c.getFilters(), [ f1, f2 ] )

		c.removeFilter( f1 )
		self.assertEqual( c.getFilters(), [ f2 ] )

		c.setFilters( [ f1, f2 ] )
		self.assertEqual( c.getFilters(), [ f1, f2 ] )

	def testChangedSignal( self ) :

		cf = Gaffer.CompoundPathFilter()

		self.__numChanges = 0
		def f( filter ) :
			self.failUnless( filter is cf )
			self.__numChanges += 1

		f1 = Gaffer.FileNamePathFilter( [ "*.gfr" ] )
		f2 = Gaffer.FileNamePathFilter( [ "*.tif" ] )

		c = cf.changedSignal().connect( f )
		self.assertEqual( self.__numChanges, 0 )

		cf.addFilter( f1 )
		self.assertEqual( self.__numChanges, 1 )

		cf.setFilters( [ f1 ] )
		self.assertEqual( self.__numChanges, 1 )

		cf.setFilters( [ f1, f2 ] )
		self.assertEqual( self.__numChanges, 2 )

		cf.removeFilter( f1 )
		self.assertEqual( self.__numChanges, 3 )

		# changing filters while not enabled shouldn't emit the signal

		cf.setEnabled( False )
		self.assertEqual( self.__numChanges, 4 )

		cf.setFilters( [] )
		self.assertEqual( self.__numChanges, 4 )

		cf.setFilters( [ f1, f2 ] )
		self.assertEqual( self.__numChanges, 4 )

	def testChangedSignalPropagation( self ) :

		cf = Gaffer.CompoundPathFilter()

		self.__numChanges = 0
		def f( filter ) :
			self.failUnless( filter is cf )
			self.__numChanges += 1

		f1 = Gaffer.FileNamePathFilter( [ "*.gfr" ] )
		f2 = Gaffer.FileNamePathFilter( [ "*.tif" ] )

		c = cf.changedSignal().connect( f )
		self.assertEqual( self.__numChanges, 0 )

		cf.setFilters( [ f1, f2 ] )
		self.assertEqual( self.__numChanges, 1 )

		f1.changedSignal()( f1 )
		self.assertEqual( self.__numChanges, 2 )

		f2.changedSignal()( f2 )
		self.assertEqual( self.__numChanges, 3 )

		cf.removeFilter( f1 )
		self.assertEqual( self.__numChanges, 4 )
		f1.changedSignal()( f1 )
		self.assertEqual( self.__numChanges, 4 )

		cf.removeFilter( f2 )
		self.assertEqual( self.__numChanges, 5 )
		f2.changedSignal()( f2 )
		self.assertEqual( self.__numChanges, 5 )

		cf.addFilter( f1 )
		self.assertEqual( self.__numChanges, 6 )
		f1.changedSignal()( f1 )
		self.assertEqual( self.__numChanges, 7 )

if __name__ == "__main__":
	unittest.main()

