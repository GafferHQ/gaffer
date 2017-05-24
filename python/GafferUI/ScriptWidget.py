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

import weakref

import IECore

import Gaffer
import GafferUI

class ScriptWidget( GafferUI.Frame) :

	def __init__( self, script, **kw ) :

		GafferUI.Frame.__init__( self, borderWidth=0, borderStyle=GafferUI.Frame.BorderStyle.None, **kw )

		self.__script = script

		applicationRoot = self.__script.ancestor( Gaffer.ApplicationRoot )

		layouts = GafferUI.Layouts.acquire( applicationRoot ) if applicationRoot is not None else None

		if layouts is not None and "Default" in layouts.names() :
			self.setChild( layouts.create( "Default", script ) )
		else :
			self.setChild( GafferUI.CompoundEditor( script ) )

		ScriptWidget.__instances.append( weakref.ref( self ) )

	def scriptNode( self ) :
		return self.__script

	def setLayout( self, compoundEditor ) :
		assert( compoundEditor.scriptNode().isSame( self.scriptNode() ) )
		self.setChild( compoundEditor )

	def getLayout( self ) :
		return self.getChild()

	def __closed( self, widget ) :

		scriptParent = self.__script.parent()
		if scriptParent is not None :
			scriptParent.removeChild( self.__script )

	def __scriptPlugChanged( self, plug ) :

		if plug.isSame( self.__script["fileName"] ) or plug.isSame( self.__script["unsavedChanges"] ) :
			self.__updateTitle()

	def __updateTitle( self ) :

		f = self.__script["fileName"].getValue()
		if not f :
			f = "untitled"
			d = ""
		else :
			d, n, f = f.rpartition( "/" )
			d = " - " + d

		u = " *" if self.__script["unsavedChanges"].getValue() else ""

		self.setTitle( "Gaffer : %s%s%s" % ( f, u, d ) )

	__instances = [] # weak references to all instances - used by acquire()
	## Returns the ScriptWindow for the specified script, creating one
	# if necessary.
	@staticmethod
	def acquire( menuOrScriptNode, createIfNecessary=True ) :

		if isinstance(menuOrScriptNode, GafferUI.Menu ):
			applicationWindow = menuOrScriptNode.ancestor( GafferUI.ApplicationWindow )
			return applicationWindow.activeScriptWidget()
		elif isinstance(menuOrScriptNode, Gaffer.ScriptNode ):
			for w in ScriptWidget.__instances :
				scriptWindow = w()
				if scriptWindow is not None and scriptWindow.scriptNode().isSame( menuOrScriptNode ) :
					return scriptWindow

			return ScriptWidget( menuOrScriptNode ) if createIfNecessary else None

		return None

	## Returns an IECore.MenuDefinition which is used to define the menu bars for all ScriptWindows
	# created as part of the specified application. This can be edited at any time to modify subsequently
	# created ScriptWindows - typically editing would be done as part of gaffer startup.
	@staticmethod
	def menuDefinition( applicationOrApplicationRoot ) :

		if isinstance( applicationOrApplicationRoot, Gaffer.Application ) :
			applicationRoot = applicationOrApplicationRoot.root()
		else :
			assert( isinstance( applicationOrApplicationRoot, Gaffer.ApplicationRoot ) )
			applicationRoot = applicationOrApplicationRoot

		menuDefinition = getattr( applicationRoot, "_scriptWindowMenuDefinition", None )
		if menuDefinition :
			return menuDefinition

		menuDefinition = IECore.MenuDefinition()
		applicationRoot._scriptWindowMenuDefinition = menuDefinition

		return menuDefinition