##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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
import GafferML

class TensorPlugTest( GafferTest.TestCase ) :

	def testDefaultValue( self ) :

		plug = GafferML.TensorPlug()
		self.assertEqual( plug.defaultValue(), GafferML.Tensor() )
		self.assertEqual( plug.getValue(), GafferML.Tensor() )

		plug = GafferML.TensorPlug( defaultValue = GafferML.Tensor( IECore.IntVectorData( [ 1, 2, ] ), [ 2 ] ) )
		self.assertEqual( plug.defaultValue(), GafferML.Tensor( IECore.IntVectorData( [ 1, 2, ] ), [ 2 ] ) )

	def testSerialisationOfDynamicPlugs( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = Gaffer.Node()
		script["node"]["user"]["p"] = GafferML.TensorPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )
		self.assertIsInstance( script2["node"]["user"]["p"], GafferML.TensorPlug )
		self.assertEqual( script2["node"]["user"]["p"].getValue(), GafferML.Tensor() )

if __name__ == "__main__" :
	unittest.main()
