##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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
import GafferUI

QtGui = GafferUI._qtImport( "QtGui" )

## The PlugWidget combines a LabelPlugValueWidget with a second PlugValueWidget
## suitable for editing the plug.
## \todo This could provide functionality for arbitrary Widgets to be placed
## on the right, which combined with the ability to find a 
## PlugWidget given a Plug could be quite useful for many things.
## \todo Remove label and description capabilities - label should /always/
## be the plug name and description should always be supplied via the
## Metadata mechanism.
class PlugWidget( GafferUI.Widget ) :

	def __init__( self, plugOrWidget, label=None, description=None, **kw ) :
	
		GafferUI.Widget.__init__( self, QtGui.QWidget(), **kw )

		layout = QtGui.QHBoxLayout()
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.setSpacing( 4 )
		layout.setSizeConstraint( QtGui.QLayout.SetMinAndMaxSize )
		self._qtWidget().setLayout( layout )

		if isinstance( plugOrWidget, Gaffer.Plug ) :
			self.__valueWidget = GafferUI.PlugValueWidget.create( plugOrPlugValueWidget )
			plug = plugOrPlugValueWidget
		else :
			assert( isinstance( plugOrWidget, GafferUI.PlugValueWidget ) or hasattr( plugOrWidget, "plugValueWidget" ) )
			self.__valueWidget = plugOrWidget
			plug = self.plugValueWidget().getPlug()
			
		self.__label = GafferUI.LabelPlugValueWidget(
			plug,
			horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top,
		)

		## \todo Decide how we allow this sort of tweak using the public
		# interface. Perhaps we should have a SizeableContainer or something?
		self.__label.label()._qtWidget().setFixedWidth( self.labelWidth() )

		if label is not None :
			self.__label.label().setText( label )

		if description is not None :
			self.__label.label().setToolTip( description )

		layout.addWidget( self.__label._qtWidget() )
		layout.addWidget( self.__valueWidget._qtWidget() )

	def plugValueWidget( self ) :
	
		if isinstance( self.__valueWidget, GafferUI.PlugValueWidget ) :
			return self.__valueWidget
		else :
			return self.__valueWidget.plugValueWidget()

	def labelPlugValueWidget( self ) :
	
		return self.__label
	
	@staticmethod
	def labelWidth() :
	
		return 110
