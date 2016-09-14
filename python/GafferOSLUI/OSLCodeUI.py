##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
import GafferOSL

Gaffer.Metadata.registerNode(

	GafferOSL.OSLCode,

	"description",
	"""
	Allows arbitrary OSL shaders to be written directly within
	Gaffer.
	""",

	"layout:customWidget:Code:widgetType", "GafferOSLUI.OSLCodeUI._CodeWidget",
	"layout:customWidget:Code:section", "Code",
	"layout:customWidget:Code:index", 0,

	plugs = {

		"name" : [

			"plugValueWidget:type", "",

		],

	}

)

# _CodeWidget
##########################################################################

class _CodeWidget( GafferUI.Widget ) :

	def __init__( self, node, **kw ) :

		column = GafferUI.ListContainer( spacing = 4 )
		GafferUI.Widget.__init__( self, column, **kw )

		self.__node = node

		with column :

			self.__textWidget = GafferUI.MultiLineTextWidget()
			self.__activatedConnection = self.__textWidget.activatedSignal().connect( Gaffer.WeakMethod( self.__activated ) )
			self.__editingFinishedConnection = self.__textWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__editingFinished ) )

			self.__messageWidget = GafferUI.MessageWidget()

		self.__codeChangedConnection = self.__node.codeChangedSignal().connect( Gaffer.WeakMethod( self.__codeChanged ) )

		self.__update()

	def __setCode( self ) :

		try :
			self.__node.setCode( self.__textWidget.getText() )
			self.__messageWidget.setVisible( False )
		except Exception as e :
			self.__messageWidget.clear()
			self.__messageWidget.setVisible( True )
			self.__messageWidget.messageHandler().handle(
				IECore.Msg.Level.Error, "Parse error", str( e )
			)

	def __update( self ) :

		self.__textWidget.setText( self.__node.getCode() )

		self.__messageWidget.clear()
		self.__messageWidget.setVisible( False )

	def __codeChanged( self, node ) :

		self.__update()

	def __activated( self, widget ) :

		self.__setCode()

	def __editingFinished( self, widget ) :

		self.__setCode()
