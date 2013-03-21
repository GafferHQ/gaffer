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

class ExecutableNodeTest( unittest.TestCase ) :

	def testIsExecutable( self ) :

		# \todo test class and instance tests (also with non-executable objects)
		pass

	def testDerivedClass( self ) :

		# \todo use default accepts and requirements and isExecutable (instance and class)
		# \todo test calls to hash, execute and requirements defined in python
		pass

	def testTaskConstructors( self ) :
	
		c = Gaffer.Context()

		t = Gaffer.ExecutableNode.Task()
		n = Gaffer.OpHolder()
		t.node = n
		t.context = c
		
		t2 = Gaffer.ExecutableNode.Task( n, c )

		t3 = Gaffer.ExecutableNode.Task( t2 )

		self.assertEqual( t.node, n )
		self.assertEqual( t.context, c )
		self.assertEqual( t2.node, n )
		self.assertEqual( t2.context, c )
		self.assertEqual( t3.node, n )
		self.assertEqual( t3.context, c )

	def testTaskComparison( self ) :

		c = Gaffer.Context()
		n = Gaffer.OpHolder()
		t1 = Gaffer.ExecutableNode.Task( n, c )
		t2 = Gaffer.ExecutableNode.Task()
		t2.node = n
		t2.context = c
		c2 = Gaffer.Context()
		c2["a"] = 2
		t3 = Gaffer.ExecutableNode.Task( n, c2 )
		n2 = Gaffer.OpHolder()
		t4 = Gaffer.ExecutableNode.Task( n2, c2 )

		self.assertEqual( t1, t1 )
		self.assertEqual( t1, t2 )
		self.assertEqual( t2, t1 )
		self.assertNotEqual( t1, t3 )
		self.assertNotEqual( t3, t1 )
		self.assertNotEqual( t3, t4 )
		self.assertNotEqual( t4, t3 )

	def testTaskSet( self ) :

		c = Gaffer.Context()
		n = Gaffer.OpHolder()
		t1 = Gaffer.ExecutableNode.Task( n, c )
		t2 = Gaffer.ExecutableNode.Task( n, c )
		self.assertEqual( t1, t2 )
		c2 = Gaffer.Context()
		c2["a"] = 2
		t3 = Gaffer.ExecutableNode.Task( n, c2 )
		n2 = Gaffer.OpHolder()
		t4 = Gaffer.ExecutableNode.Task( n2, c2 )
		t5 = Gaffer.ExecutableNode.Task( n2, c )

		s = set( [ t1, t2, t3, t4, t4, t4, t1, t2, t4, t3, t2 ] )
		self.assertEqual( len(s), 3 )
		self.assertEqual( s, set( [ t1, t3, t4 ] ) )
		self.assertTrue( t1 in s )
		self.assertTrue( t2 in s )
		self.assertTrue( t3 in s )
		self.assertTrue( t4 in s )
		self.assertFalse( t5 in s )

if __name__ == "__main__":
	unittest.main()
	
