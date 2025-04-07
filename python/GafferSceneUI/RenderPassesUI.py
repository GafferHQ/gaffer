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

import re

import Gaffer
import GafferUI
import GafferScene
import GafferSceneUI

from Qt import QtGui

Gaffer.Metadata.registerNode(

	GafferScene.RenderPasses,

	"description",
	"""
	Appends render passes to the scene globals.

	Render passes can be used to define named variations of a scene.
	These can be rendered by dispatching a RenderPassWedge node downstream
	of your render node of choice, or written to disk by dispatching
	a RenderPassWedge node downstream of a SceneWriter.

	Scenes can be varied per render pass based on the value of the
	`renderPass` context variable, which will contain the name of the
	current render pass being dispatched. `${renderPass}` can be used
	on the `selector` plug of Spreadsheet or NameSwitch nodes to choose
	specific plug values or branches of the node graph per render pass,
	and its value can be queried using Expression or ContextQuery nodes.

	> Tip : The list of render passes is stored in the `renderPass:names`
	> option in the scene globals.
	""",

	plugs = {

		"names" : [

			"description",
			"""
			The names of render passes to be created.

			> Tip : If any of the specified names already exist, they
			> will be removed from their existing position in the list
			> and appended to the end.
			""",

			"plugValueWidget:type", "GafferSceneUI.RenderPassesUI._RenderPassVectorDataPlugValueWidget",

		],

	}

)

class _RenderPassNameWidget( GafferUI.TextWidget ) :

	def __init__( self, **kw ) :

		GafferUI.TextWidget.__init__( self, **kw )

		self._qtWidget().setValidator( _RenderPassNameValidator( self._qtWidget() ) )

	def setRenderPassName( self, name ) :

		self.setText( name )

	def getRenderPassName( self ) :

		return self.getText()

	def renderPassNameChangedSignal( self ) :

		return self.textChangedSignal()

class _RenderPassNameValidator( QtGui.QValidator ) :

	def __init__( self, parent ) :

		QtGui.QValidator.__init__( self, parent )

	def validate( self, input, pos ) :

		if len( input ) :
			if re.match( "^[A-Za-z0-9_-]+$", input ) :
				result = QtGui.QValidator.Acceptable
			else :
				result = QtGui.QValidator.Invalid
		else :
			result = QtGui.QValidator.Intermediate

		return result, input, pos

## Render Pass Name Widget Registration
# -------------------------------------
# We provide a default widget to display and edit a render pass name, but
# facilities may wish to customise the widget used in order to provide their
# own UI or name validation. These methods allow registration of a custom
# widget via a startup config.

__renderPassNameWidget = _RenderPassNameWidget

## 'w' should be a callable that returns a widget with
## `getRenderPassName()` and `setRenderPassName( renderPassName )` methods.
## Optional `renderPassNameChangedSignal` and `activatedSignal` signals can
## be emitted to inform observers of changes to, or the choice of render pass name.
def registerRenderPassNameWidget( w ) :

	global __renderPassNameWidget
	__renderPassNameWidget = w

def createRenderPassNameWidget() :

	return __renderPassNameWidget()

class _RenderPassVectorDataPlugValueWidget( GafferUI.VectorDataPlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		GafferUI.VectorDataPlugValueWidget.__init__( self, plug, **kw )

		self.vectorDataWidget().editSignal().connect( Gaffer.WeakMethod( self.__edit ) )

	def __edit( self, vectorDataWidget, column, row ) :

		return _Editor()

class _Editor( GafferUI.ListContainer ) :

	def __init__( self ) :

		GafferUI.ListContainer.__init__( self, orientation = GafferUI.ListContainer.Orientation.Horizontal, spacing = 2 )
		with self :
			self.__nameWidget = createRenderPassNameWidget()

		self._qtWidget().setFocusProxy( self.__nameWidget._qtWidget() )

		GafferUI.Widget.focusChangedSignal().connect( Gaffer.WeakMethod( self.__focusChanged ) )

	def setValue( self, value ) :

		self.__nameWidget.setRenderPassName( value )

	def getValue( self ) :

		return self.__nameWidget.getRenderPassName()

	def __focusChanged( self, oldWidget, newWidget ) :

		if not self.isAncestorOf( newWidget ) :
			self.setVisible( False )
