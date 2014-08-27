##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

import platform

import IECore

import GafferUI

QtGui = GafferUI._qtImport( "QtGui" )

class MenuBar( GafferUI.Widget ) :

	def __init__( self, definition, **kw ) :

		GafferUI.Widget.__init__( self, _MenuBar(), **kw )

		self.definition = definition

	def __setattr__( self, key, value ) :

		self.__dict__[key] = value
		if key=="definition" :

			self._qtWidget().clear()
			self._subMenus = []

			done = set()
			for path, item in self.definition.items() :

				pathComponents = path.strip( "/" ).split( "/" )
				name = pathComponents[0]
				if not name in done :

					if len( pathComponents ) > 1 :
						subMenuDefinition = self.definition.reRooted( "/" + name )
					else :
						subMenuDefinition = item.subMenu or IECore.MenuDefinition()

					menu = GafferUI.Menu( subMenuDefinition, _qtParent=self._qtWidget() )
					menu._qtWidget().setTitle( name )
					self._qtWidget().addMenu( menu._qtWidget() )
					self._subMenus.append( menu )

				done.add( name )

class _MenuBar( QtGui.QMenuBar ) :

	def __init__( self, parent=None ) :

		QtGui.QMenuBar.__init__( self, parent )

		self.setSizePolicy( QtGui.QSizePolicy( QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed ) )

		# disable menu merging on mac
		self.setNativeMenuBar( False )

	def showEvent( self, event ) :

		# normally, Menus aren't populated with items until they're shown,
		# but we need them populated before so that the keyboard shortcuts
		# become available. we wait until a menu bar show event because we
		# know then that we're parented below a Window, and many of our menu
		# commands and status items we use need to find their parent ScriptWindow
		# before they work properly.
		for subMenu in GafferUI.Widget._owner( self )._subMenus :
			subMenu._buildFully()

		return QtGui.QMenuBar.showEvent( self, event )
