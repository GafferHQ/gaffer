##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import inspect
import unittest
import imath

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class PrimitiveVariableExistsTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		# Make a few input scenes

		script = Gaffer.ScriptNode()

		script["Cube"] = GafferScene.Cube( "Cube" )
		script["PathFilter"] = GafferScene.PathFilter( "PathFilter" )
		script["PathFilter"]["paths"].setValue( IECore.StringVectorData( [ '/cube' ] ) )
		script["PrimitiveVariables"] = GafferScene.PrimitiveVariables( "PrimitiveVariables" )
		script["PrimitiveVariables"]["primitiveVariables"].addChild( Gaffer.CompoundDataPlug.MemberPlug( "member1" ) )
		script["PrimitiveVariables"]["primitiveVariables"]["member1"].addChild( Gaffer.StringPlug( "name" ) )
		script["PrimitiveVariables"]["primitiveVariables"]["member1"].addChild( Gaffer.Color3fPlug( "value" ) )
		script["PrimitiveVariables"]["primitiveVariables"]["member1"].addChild( Gaffer.BoolPlug( "enabled", defaultValue = True ) )
		script["PrimitiveVariables"]["in"].setInput( script["Cube"]["out"] )
		script["PrimitiveVariables"]["filter"].setInput( script["PathFilter"]["out"] )
		script["PrimitiveVariables"]["primitiveVariables"]["member1"]["name"].setValue( 'Cs' )
		script["PrimitiveVariableExists"] = GafferScene.PrimitiveVariableExists( "PrimitiveVariableExists" )
		script["PrimitiveVariableExists"]["in"].setInput( script["PrimitiveVariables"]["out"] )

		# No primitive variables if there is no scene path
		self.assertEqual( script["PrimitiveVariableExists"]["out"].getValue(), False )

		c = Gaffer.Context()
		c["scene:path"] = IECore.InternedStringVectorData( [ "cube" ] )
		with c:
			self.assertEqual( script["PrimitiveVariableExists"]["out"].getValue(), True )

			script["PrimitiveVariableExists"]["primitiveVariable"].setValue( "bogus" )

			self.assertEqual( script["PrimitiveVariableExists"]["out"].getValue(), False )

			script["PrimitiveVariableExists"]["primitiveVariable"].setValue( "Cs" )

			self.assertEqual( script["PrimitiveVariableExists"]["out"].getValue(), True )

if __name__ == "__main__":
	unittest.main()
