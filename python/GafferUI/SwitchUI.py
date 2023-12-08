##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUI

from GafferUI.PlugValueWidget import sole

Gaffer.Metadata.registerNode(

	Gaffer.Switch,

	"description",
	"""
	Chooses between multiple input connections, passing through the
	chosen input to the output.
	""",

	# Add + buttons for creating new plugs in the GraphEditor
	"noduleLayout:customGadget:addButtonTop:gadgetType", "GafferUI.SwitchUI.PlugAdder",
	"noduleLayout:customGadget:addButtonTop:section", "top",
	"noduleLayout:customGadget:addButtonBottom:gadgetType", "GafferUI.SwitchUI.PlugAdder",
	"noduleLayout:customGadget:addButtonBottom:section", "bottom",
	"noduleLayout:customGadget:addButtonLeft:gadgetType", "GafferUI.SwitchUI.PlugAdder",
	"noduleLayout:customGadget:addButtonLeft:section", "left",
	"noduleLayout:customGadget:addButtonRight:gadgetType", "GafferUI.SwitchUI.PlugAdder",
	"noduleLayout:customGadget:addButtonRight:section", "right",

	plugs = {

		"index" : [

			"description",
			"""
			The index of the input which is passed through. A value
			of 0 chooses the first input, 1 the second and so on. Values
			larger than the number of available inputs wrap back around to
			the beginning.
			""",

			"nodule:type", "",

		],

		"in" : [

			"description",
			"""
			The array of inputs to choose from. One of these is chosen
			by the index plug to be passed through to the output.
			""",

			"nodule:type", "GafferUI::CompoundNodule",
			"plugValueWidget:type", "",

			"noduleLayout:spacing", lambda plug : 2.0 if Gaffer.Metadata.value( plug, "noduleLayout:section" ) in ( "top", "bottom", None ) else 0.25,

		],

		"out" : [

			"description",
			"""
			Outputs the input specified by the index.
			""",

			"plugValueWidget:type", "",

		],

		"connectedInputs" : [

			"description",
			"""
			The indices of the input array that have incoming connections.

			> Tip : This can be used to drive a Wedge or Collect node so that
			> they operate over each input in turn.
			""",

			"nodule:type", "",
			"layout:section", "Advanced",
			"plugValueWidget:type", "GafferUI.SwitchUI._ConnectedInputsPlugValueWidget",

		],

	}

)

class _ConnectedInputsPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__textWidget = GafferUI.TextWidget( editable = False )
		GafferUI.PlugValueWidget.__init__( self, self.__textWidget, plugs, **kw )

	def _updateFromValues( self, values, exception ) :

		value = sole( values )
		self.__textWidget.setText(
			", ".join( [ str( x ) for x in value ] )
			if value is not None
			else "---"
		)

		self.__textWidget.setErrored( exception is not None )
