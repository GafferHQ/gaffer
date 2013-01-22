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

import unittest

import IECore

import Gaffer
import GafferTest

class CompoundDataPlugTest( unittest.TestCase ) :

	def test( self ) :

		p = Gaffer.CompoundDataPlug()
	
		m1 = p.addMember( "a", IECore.IntData( 10 ) )
		self.failUnless( isinstance( m1, Gaffer.CompoundPlug ) )
		self.assertEqual( m1.getName(), "member1" )
		self.assertEqual( m1["name"].getValue(), "a" )
		self.assertEqual( m1["value"].getValue(), 10 )
		self.failIf( "enabled" in m1 )
		
		d, n = p.memberDataAndName( m1 )
		self.assertEqual( d, IECore.IntData( 10 ) )
		self.assertEqual( n, "a" )
		
		m1["name"].setValue( "b" )
		d, n = p.memberDataAndName( m1 )
		self.assertEqual( d, IECore.IntData( 10 ) )
		self.assertEqual( n, "b" )
		
		m2 = p.addMember( "c", IECore.FloatData( .5 ) )
		self.failUnless( isinstance( m2, Gaffer.CompoundPlug ) )
		self.assertEqual( m2.getName(), "member2" )
		self.assertEqual( m2["name"].getValue(), "c" )
		self.assertEqual( m2["value"].getValue(), .5 )
		self.failIf( "enabled" in m2 )
	
		d, n = p.memberDataAndName( m2 )
		self.assertEqual( d, IECore.FloatData( .5 ) )
		self.assertEqual( n, "c" )
		
		m3 = p.addOptionalMember( "o", IECore.StringData( "--" ), plugName = "m", enabled = True )
		self.failUnless( isinstance( m3, Gaffer.CompoundPlug ) )
		self.assertEqual( m3.getName(), "m" )
		self.assertEqual( m3["name"].getValue(), "o" )
		self.assertEqual( m3["value"].getValue(), "--" )
		self.failUnless( "enabled" in m3 )
		self.assertEqual( m3["enabled"].getValue(), True )
		
		d, n = p.memberDataAndName( m3 )
		self.assertEqual( d, IECore.StringData( "--" ) )
		self.assertEqual( n, "o" )
		
		m3["enabled"].setValue( False )
		d, n = p.memberDataAndName( m3 )
		self.assertEqual( d, None )
		self.assertEqual( n, "" )
	
	def testVectorData( self ) :
	
		p = Gaffer.CompoundDataPlug()
		
		m1 = p.addMember( "a", IECore.FloatVectorData( [ 1, 2, 3 ] ) )
		self.failUnless( isinstance( m1, Gaffer.CompoundPlug ) )
		
		d, n = p.memberDataAndName( m1 )
		self.assertEqual( d, IECore.FloatVectorData( [ 1, 2, 3 ] ) )
		self.assertEqual( n, "a" )
		
		m2 = p.addMember( "b", IECore.IntVectorData( [ 1, 2, 3 ] ) )
		self.failUnless( isinstance( m2, Gaffer.CompoundPlug ) )
		
		d, n = p.memberDataAndName( m2 )
		self.assertEqual( d, IECore.IntVectorData( [ 1, 2, 3 ] ) )
		self.assertEqual( n, "b" )
		
		m3 = p.addMember( "c", IECore.StringVectorData( [ "1", "2", "3" ] ) )
		self.failUnless( isinstance( m3, Gaffer.CompoundPlug ) )
		
		d, n = p.memberDataAndName( m3 )
		self.assertEqual( d, IECore.StringVectorData( [ "1", "2", "3" ] ) )
		self.assertEqual( n, "c" )
	
	def testImathVectorData( self ) :
	
		p = Gaffer.CompoundDataPlug()
		
		m1 = p.addMember( "a", IECore.V3fData( IECore.V3f( 1, 2, 3 ) ) )
		self.failUnless( isinstance( m1, Gaffer.CompoundPlug ) )
		
		d, n = p.memberDataAndName( m1 )
		self.assertEqual( d, IECore.V3fData( IECore.V3f( 1, 2, 3 ) ) )
		self.assertEqual( n, "a" )
		
		m2 = p.addMember( "b", IECore.V2fData( IECore.V2f( 1, 2 ) ) )
		self.failUnless( isinstance( m2, Gaffer.CompoundPlug ) )
		
		d, n = p.memberDataAndName( m2 )
		self.assertEqual( d, IECore.V2fData( IECore.V2f( 1, 2 ) ) )
		self.assertEqual( n, "b" )
	
	def testPlugFlags( self ) :
	
		p = Gaffer.CompoundDataPlug()
		m1 = p.addMember( "a", IECore.V3fData( IECore.V3f( 1, 2, 3 ) ), plugFlags = Gaffer.Plug.Flags.Default )
		self.assertEqual( m1.getFlags(), Gaffer.Plug.Flags.Default )
		self.assertEqual( m1["name"].getFlags(), Gaffer.Plug.Flags.Default)
		self.assertEqual( m1["value"].getFlags(), Gaffer.Plug.Flags.Default )
		
		m2 = p.addOptionalMember( "a", IECore.V3fData( IECore.V3f( 1, 2, 3 ) ), plugFlags = Gaffer.Plug.Flags.Default )
		self.assertEqual( m2.getFlags(), Gaffer.Plug.Flags.Default )
		self.assertEqual( m2["name"].getFlags(), Gaffer.Plug.Flags.Default )
		self.assertEqual( m2["value"].getFlags(), Gaffer.Plug.Flags.Default )
		self.assertEqual( m2["enabled"].getFlags(), Gaffer.Plug.Flags.Default )
					
if __name__ == "__main__":
	unittest.main()
	
