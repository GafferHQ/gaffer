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

from __future__ import with_statement

import os
import unittest

import IECore

import Gaffer
import GafferTest

class StringPlugTest( GafferTest.TestCase ) :

	def testExpansion( self ) :
						
		n = GafferTest.StringInOutNode()
		self.assertHashesValid( n )
		
		# nothing should be expanded when we're in a non-computation context
		n["in"].setValue( "testyTesty.##.exr" )
		self.assertEqual( n["in"].getValue(), "testyTesty.##.exr" )
		
		n["in"].setValue( "${a}/$b/${a:b}" )
		self.assertEqual( n["in"].getValue(), "${a}/$b/${a:b}" )
		
		# but expansions should happen magically when the compute()
		# calls getValue().
		context = Gaffer.Context()
		context.setFrame( 10 )
		n["in"].setValue( "testyTesty.###.exr" )
		with context :
			self.assertEqual( n["out"].getValue(), "testyTesty.010.exr" )
		
		context["A"] = "apple"
		n["in"].setValue( "what a lovely $A" )
		with context :
			self.assertEqual( n["out"].getValue(), "what a lovely apple" )
		n["in"].setValue( "what a lovely ${A}" )
		with context :
			self.assertEqual( n["out"].getValue(), "what a lovely apple" )
		context["A"] = "peach"
		with context :
			self.assertEqual( n["out"].getValue(), "what a lovely peach" )		
		
		context["env:dir"] = "a/path"
		n["in"].setValue( "a/${env:dir}/b" )
		with context :
			self.assertEqual( n["out"].getValue(), "a/a/path/b" )
		
		n["in"].setValue( "$dontExist" )
		with context :
			self.assertEqual( n["out"].getValue(), "" )
		
		# once again, nothing should be expanded when we're in a
		# non-computation context
		n["in"].setValue( "testyTesty.##.exr" )
		self.assertEqual( n["in"].getValue(), "testyTesty.##.exr" )
	
	def testRecursiveExpansion( self ) :
	
		n = GafferTest.StringInOutNode()
		n["in"].setValue( "$a" )
		
		context = Gaffer.Context()
		context["a"] = "a$b"
		context["b"] = "b"
		
		with context :
			self.assertEqual( n["out"].getValue(), "ab" )
	
	def testRecursiveExpansionCycles( self ) :
	
		n = GafferTest.StringInOutNode()
		n["in"].setValue( "$a" )
		
		context = Gaffer.Context()
		context["a"] = "a$b"
		context["b"] = "b$a"
		
		with context :
			self.assertRaises( RuntimeError, n["out"].getValue )
	
	def testTildeExpansion( self ) :
	
		n = GafferTest.StringInOutNode()
		
		n["in"].setValue( "~" )
		self.assertEqual( n["out"].getValue(), os.path.expanduser( "~" ) )

		n["in"].setValue( "~/something.tif" )
		self.assertEqual( n["out"].getValue(), os.path.expanduser( "~/something.tif" ) )
		
		# ~ shouldn't be expanded unless it's at the front - it would
		# be meaningless in other cases.
		n["in"].setValue( "in ~1900" )
		self.assertEqual( n["out"].getValue(), "in ~1900" )
	
	def testEnvironmentExpansion( self ) :
	
		n = GafferTest.StringInOutNode()
		
		n["in"].setValue( "${A}" )
		h1 = n["out"].hash()
		self.assertEqual( n["out"].getValue(), "" )
		
		os.environ["A"] = "a"
		self.assertEqual( n["out"].getValue(), "a" )
		h2 = n["out"].hash()
		self.assertNotEqual( h1, h2 )
		
		context = Gaffer.Context()
		context["A"] = "b"
		with context :
			# context should win against environment
			self.assertEqual( n["out"].getValue(), "b" )
			self.assertNotEqual( n["out"].hash(), h1 )
			self.assertNotEqual( n["out"].hash(), h2 )
	
	def testDefaultValueExpansion( self ) :
	
		n = GafferTest.StringInOutNode( defaultValue = "${A}" )
		context = Gaffer.Context()
		context["A"] = "b"
		with context :
			self.assertEqual( n["out"].getValue(), "b" )
		
if __name__ == "__main__":
	unittest.main()
	
