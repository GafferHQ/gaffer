##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

import os

import imath

import IECore

import Gaffer
import GafferUITest
import GafferScene
import GafferSceneUI

class TransformToolTest( GafferUITest.TestCase ) :

	def testSelectionEditability( self ) :

		script = Gaffer.ScriptNode()

		script["box"] = Gaffer.Box()
		script["box"]["plane"] = GafferScene.Plane()
		Gaffer.PlugAlgo.promote( script["box"]["plane"]["out"] )

		# Box is editable, so all fields of the selection should be useable.

		selection = GafferSceneUI.TransformTool.Selection( script["box"]["out"], "/plane", script.context() )

		self.assertEqual( selection.scene(), script["box"]["out"] )
		self.assertEqual( selection.path(), "/plane" )
		self.assertEqual( selection.context(), script.context() )
		self.assertEqual( selection.upstreamScene(), script["box"]["plane"]["out"] )
		self.assertEqual( selection.upstreamPath(), "/plane" )
		self.assertEqual( selection.upstreamContext()["scene:path"], IECore.InternedStringVectorData( [ "plane" ] ) )
		self.assertTrue( selection.editable() )
		self.assertEqual( selection.transformPlug(), script["box"]["plane"]["transform"] )
		self.assertEqual( selection.transformSpace(), imath.M44f() )

		# Reference internals are not editable, so attempts to access invalid
		# fields should throw.

		referenceFileName = os.path.join( self.temporaryDirectory(), "test.grf" )
		script["box"].exportForReference( referenceFileName )

		script["reference"] = Gaffer.Reference()
		script["reference"].load( referenceFileName )

		selection = GafferSceneUI.TransformTool.Selection( script["reference"]["out"], "/plane", script.context() )

		self.assertEqual( selection.scene(), script["reference"]["out"] )
		self.assertEqual( selection.path(), "/plane" )
		self.assertEqual( selection.context(), script.context() )
		self.assertEqual( selection.upstreamScene(), script["reference"]["plane"]["out"] )
		self.assertEqual( selection.upstreamPath(), "/plane" )
		self.assertEqual( selection.upstreamContext()["scene:path"], IECore.InternedStringVectorData( [ "plane" ] ) )
		self.assertFalse( selection.editable() )
		with self.assertRaisesRegexp( RuntimeError, "Selection is not editable" ) :
			selection.transformPlug()
		with self.assertRaisesRegexp( RuntimeError, "Selection is not editable" ) :
			selection.transformSpace()

if __name__ == "__main__":
	unittest.main()
