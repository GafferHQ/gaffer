##########################################################################
#
#  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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

import imath

import IECore

import Gaffer
import GafferUI

class MenuButton( GafferUI.Button ) :

	def __init__( self, text="", image=None, hasFrame=True, menu=None, **kw ) :

		GafferUI.Button.__init__( self, text, image, hasFrame, **kw )

		self.__menu = None
		self.setMenu( menu )

		self._qtWidget().pressed.connect( Gaffer.WeakMethod( self.__pressed ) )

	def setMenu( self, menu ) :

		# Note that although QPushButton does have a setMenu() method that would
		# ostensibly do everything for us, we don't use it. Primarily this is because
		# it pops the menu up in utterly the wrong position when we place a MenuButton
		# in GLWidget overlay - this is a Qt bug. Secondarily, we also want to use
		# Menu.popup() as it gives the menu a parent for return from Menu.parent(),
		# which may be important to the menu item callbacks.

		if menu is self.__menu :
			return

		self.__menu = menu

		if self.__menu is not None :
			self.__menuVisibilityChangedConnection = self.__menu.visibilityChangedSignal().connect(
				Gaffer.WeakMethod( self.__menuVisibilityChanged ),
				scoped = True
			)
		else :
			self.__menuVisibilityChangedConnection = None

		self.setEnabled( self.__menu is not None )

	def getMenu( self ) :

		return self.__menu

	def setText( self, text ) :

		GafferUI.Button.setText( self, text )

		# Because we can't use QPushButton::setMenu() to manage our menus,
		# we also can't use the QPushButton::menu-indicator subcontrol to
		# style menus. Instead we use this custom property to drive the
		# stylesheet.
		self._qtWidget().setProperty( "gafferMenuIndicator", text != "" )

	def __pressed( self ) :

		if self.__menu is None :
			return

		b = self.bound()
		self.__menu.popup(
			parent = self,
			position = imath.V2i( b.min().x, b.max().y ),
		)

	def __menuVisibilityChanged( self, menu ) :

		if not menu.visible() :
			self._qtWidget().setDown( False )
			# There is a bug whereby Button never receives the event for __leave,
			# if the menu is shown. This results in the image highlight state sticking.
			if self.widgetAt( self.mousePosition() ) is not self :
				self._Button__leave( self )
