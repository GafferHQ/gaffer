##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.RenderPassWedge,

	"description",
	"""
	Causes upstream nodes to be dispatched multiple times in a range
	of contexts, each time with a different value for the `renderPass`
	context variable. Each value of `renderPass` is the name of a
	render pass created from one or more RenderPasses nodes in the
	network upstream of the `in` plug.

	> Tip : Typically, a RenderPassWedge would be placed downstream of
	> your render node of choice, allowing render tasks to be dispatched
	> for each render pass.

	Tasks can be varied per pass by using `${renderPass}` in an upstream
	Spreadsheet or NameSwitch's `selector` or through use of a
	ContextQuery node or an expression.

	Specific passes can be disabled from wedging by setting the
	`renderPass:enabled` option to `False` in contexts where that render
	pass name is the value of the `renderPass` context variable.

	Customisation
	-------------

	The behaviour of the RenderPassWedge node can be customised by registering
	an adaptor that conditionally deletes, renames or disables passes. A common
	use case is to conditionally enable passes on a per-shot basis according to
	the presence or absence of particular assets within the scene.

	Adaptors should be registered using a client value of "RenderPassWedge" - for example :

	`GafferScene.SceneAlgo.registerRenderAdaptor( "MyConditionalPassAdaptor", adaptorCreationFunction, client = "RenderPassWedge" )`
	""",

	plugs = {

		"in" : [

			"description",
			"""
			The input scene containing the render passes to wedge.
			""",
			"nodule:type", "GafferUI::StandardNodule",

		],

		"names" : [

			"description",
			"""
			The names of the render passes to be wedged.

			> Note : Render pass names are queried at the
			> script's start frame to ensure they do not vary
			> over time and to prevent scenes with expensive
			> globals from slowing task dispatch.
			""",
			"plugValueWidget:type", "GafferSceneUI.RenderPassWedgeUI._PassNamesWidget",

		],

		"out" : [

			"description",
			"""
			A direct pass-through of the input scene.
			""",

		],

	}

)

##########################################################################
# _PassNamesWidget
##########################################################################

class _PassNamesWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__textWidget = GafferUI.MultiLineTextWidget( editable = False )

		self.__busyWidget = GafferUI.BusyWidget( size = 18 )
		# Sneak into the corner of the text widget.
		self.__busyWidget._qtWidget().setParent( self.__textWidget._qtWidget() )

		GafferUI.PlugValueWidget.__init__( self, self.__textWidget, plugs, **kw )

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		return [
			plug.getValue()
			for plug in plugs
		]

	def _updateFromValues( self, values, exception ) :

		if len( values ) :
			self.__textWidget.setText( "\n".join( values[0] ) )

		self.__busyWidget.setVisible( exception is None and not values )
		self.__textWidget.setErrored( exception is not None )
