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
#      * Neither the name of Image Engine Design nor the names of
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
import math

class Transform2DPlugTest( unittest.TestCase ) :

	def testMatrix( self ) :
	
		p = Gaffer.Transform2DPlug()
		
		p["pivot"].setValue( IECore.V2f( 1, 1 ) )
		p["translate"].setValue( IECore.V2f( 1, 2 ) )
		p["rotate"].setValue( 45 )
		p["scale"].setValue( IECore.V2f( 2, 3 ) )
	
		displayWindow = IECore.Box2i( IECore.V2i(0), IECore.V2i(9) )
		pixelAspect = 1.
		formatHeight = displayWindow.size().y+1 
		pivotValue = p["pivot"].getValue()
		pivotValue.y = formatHeight - pivotValue.y
		pivot = IECore.M33f.createTranslated( pivotValue )
		
		translateValue = p["translate"].getValue()
		translateValue.y = -translateValue.y
		translate = IECore.M33f.createTranslated( translateValue )
		
		rotate = IECore.M33f.createRotated( IECore.degreesToRadians( p["rotate"].getValue() ) )
		scale = IECore.M33f.createScaled( p["scale"].getValue() )
		invPivot = IECore.M33f.createTranslated( pivotValue * IECore.V2f(-1.) )
		
		transforms = {
			"p" : pivot,
			"t" : translate,
			"r" : rotate,
			"s" : scale,
			"pi" : invPivot,
		}

		transform = IECore.M33f()
		for m in ( "pi", "s", "r", "t", "p" ) :
			transform = transform * transforms[m]

		self.assertEqual( p.matrix( displayWindow, pixelAspect ), transform )

	def testTransformOrderExplicit( self ) :
	
		plug = Gaffer.Transform2DPlug()
		
		displayWindow = IECore.Box2i( IECore.V2i(0), IECore.V2i(9) )
		pixelAspect = 1.
	
		t =	IECore.V2f( 100, 0 )
		r =	90
		s =	IECore.V2f( 2, 2 )
		p = IECore.V2f( 10, -10 )
		plug["translate"].setValue(  t )
		plug["rotate"].setValue( r )
		plug["scale"].setValue( s )
		plug["pivot"].setValue( p )
		
		# Test if this is equal to a simple hardcoded matrix, down to floating point error
		# This verifies that translation is not being affected by rotation and scale,
		# which is what users will expect
		self.assertTrue( plug.matrix( displayWindow, pixelAspect ).equalWithAbsError(
			IECore.M33f(
				0,   2, 0,
				-2,  0, 0,
				150, 0, 1),
			2e-6
		) )
	
	def testCreateCounterpart( self ) :
	
		t = Gaffer.Transform2DPlug()
		t2 = t.createCounterpart( "a", Gaffer.Plug.Direction.Out )
		
		self.assertEqual( t2.getName(), "a" )
		self.assertEqual( t2.direction(), Gaffer.Plug.Direction.Out )
		self.assertTrue( isinstance( t2, Gaffer.Transform2DPlug ) )
		
	def testRunTimeTyped( self ) :
	
		p = Gaffer.Transform2DPlug()
		self.failIf( p.typeId() == Gaffer.CompoundPlug.staticTypeId() )
		self.failUnless( p.isInstanceOf( Gaffer.CompoundPlug.staticTypeId() ) )

if __name__ == "__main__":
	unittest.main()
	
