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

import Gaffer
import GafferSceneUI
import GafferUITest

class AttributeEditorTest( GafferUITest.TestCase ) :

	def testRegisterAttribute( self ) :

		attributeNames = [ "test:visible", "test:this", "test:that", "test:other" ]

		for attribute in attributeNames :
			GafferSceneUI.AttributeEditor.registerAttribute( "Standard", attribute, "testSection" )
			self.addCleanup( GafferSceneUI.AttributeEditor.deregisterColumn, "Standard", attribute, "testSection" )

		script = Gaffer.ScriptNode()
		editor = GafferSceneUI.AttributeEditor( script )
		editor.settings()["section"].setValue( "testSection" )
		GafferSceneUI.AttributeEditor._AttributeEditor__updateColumns.flush( editor )

		columnAttributes = [
			c.inspector().name() for c in editor.sceneListing().getColumns()
			if isinstance( c, GafferSceneUI.Private.InspectorColumn )
		]

		for attribute in attributeNames :
			self.assertIn( attribute, columnAttributes )

		GafferSceneUI.AttributeEditor.deregisterColumn( "Standard", "test:visible", "testSection" )

		editor._AttributeEditor__updateColumns()
		GafferSceneUI.AttributeEditor._AttributeEditor__updateColumns.flush( editor )

		columnAttributes = [
			c.inspector().name() for c in editor.sceneListing().getColumns()
			if isinstance( c, GafferSceneUI.Private.InspectorColumn )
		]

		for attribute in attributeNames :
			if attribute != "test:visible" :
				self.assertIn( attribute, columnAttributes )
			else :
				self.assertNotIn( attribute, columnAttributes )

if __name__ == "__main__":
	unittest.main()
