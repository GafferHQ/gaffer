##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

import IECore

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class StandardNodeToolbarTest( GafferUITest.TestCase ) :

	def testNoUnnecessaryUpdates( self ) :

		script = Gaffer.ScriptNode()

		script["node"] = GafferTest.AddNode()
		Gaffer.Metadata.registerValue(
			script["node"]["op1"], "plugValueWidget:type",
			"GafferUITest.PlugValueWidgetTest.UpdateCountPlugValueWidget"
		)
		Gaffer.Metadata.registerValue( script["node"]["op1"], "toolbarLayout:section", "Top" )

		view = GafferUITest.ViewTest.MyView( script["node"]["op1"] )
		view.setContext( script.context() )
		view["testPlug"] = Gaffer.IntPlug()
		Gaffer.Metadata.registerValue(
			view["testPlug"], "plugValueWidget:type",
			"GafferUITest.PlugValueWidgetTest.UpdateCountPlugValueWidget"
		)

		for node, plug in [
			( script["node"], script["node"]["op1"] ),
			( view, view["testPlug" ] ),
		] :

			toolbar = GafferUI.StandardNodeToolbar( node )
			widget = toolbar._StandardNodeToolbar__layout.plugValueWidget( plug )
			self.assertEqual( widget.updateCount, 1 )
			self.assertTrue( widget.updateContexts[0].isSame( script.context() ) )

if __name__ == "__main__":
	unittest.main()
