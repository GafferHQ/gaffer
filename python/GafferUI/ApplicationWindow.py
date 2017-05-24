##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
#      * Neither the name of Image Engine Design Inc nor the names of
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

def getTitle( scriptNode ) :

	f = scriptNode["fileName"].getValue()
	if not f :
		f = "untitled"
	else :
		d, n, f = f.rpartition( "/" )

	u = " *" if scriptNode["unsavedChanges"].getValue() else ""

	return "{0}{1}".format(f, u)

class ApplicationWindow( GafferUI.Window ) :

	def __init__( self, applicationRoot, **kw ) :

		self.__scriptPlugSetConnections = {}
		self.__automaticallyCreatedInstances = []
		self.__scriptAddedConnection = applicationRoot["scripts"].childAddedSignal().connect(  Gaffer.WeakMethod( self.__scriptAdded ) )
		self.__scriptRemovedConnection = applicationRoot["scripts"].childRemovedSignal().connect(  Gaffer.WeakMethod( self.__scriptRemoved ) )

		self.__applicationRoot = applicationRoot

		GafferUI.Window.__init__( self, **kw )

		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 2 ) as verticalList:
			GafferUI.MenuBar( self.menuDefinition() )
			self.__scriptTabbedContainer = GafferUI.TabbedContainer()

		self.setChild( verticalList )

	def menuDefinition(self):
		return GafferUI.ScriptWidget.menuDefinition( self.__applicationRoot ) if self.__applicationRoot else IECore.MenuDefinition()

	def __updateTabLabel(self, scriptNode):
		title = getTitle(scriptNode)

		for w in self.__automaticallyCreatedInstances :
			if w.scriptNode().isSame( scriptNode ) :
				w.parent().setLabel(w, title)

	def __scriptPlugChanged( self, plug ) :
		scriptNode = plug.ancestor( Gaffer.ScriptNode )

		if not scriptNode:
			return

		self.__updateTabLabel( scriptNode )


	def __scriptAdded( self, scriptContainer, script ) :

		w = GafferUI.ScriptWidget( script )

		self.__scriptTabbedContainer.append( w, label = getTitle( script ) )
		w.setVisible(True)

		self.__automaticallyCreatedInstances.append( w )
		self.__scriptPlugSetConnections[script] = script.plugSetSignal().connect( Gaffer.WeakMethod( self.__scriptPlugChanged ) )

	def __scriptRemoved(self, scriptContainer, script ) :

		if script in self.__scriptPlugSetConnections:
			del self.__scriptPlugSetConnections[script]

		for w in self.__automaticallyCreatedInstances :
			if w.scriptNode().isSame( script ) :
				self.__scriptTabbedContainer.remove( w )
				self.__automaticallyCreatedInstances.remove( w )

		if not len( scriptContainer.children() ) and GafferUI.EventLoop.mainEventLoop().running() :
			GafferUI.EventLoop.mainEventLoop().stop()

	def __unsavedScriptFilenames(self):

		unsavedFilenames = []

		for w in self.__automaticallyCreatedInstances :
			scriptNode = w.scriptNode()
			if scriptNode["unsavedChanges"].getValue():
				f = scriptNode["fileName"].getValue()
				f = f.rpartition( "/" )[2] if f else "untitled"
				unsavedFilenames.append(f)

		return unsavedFilenames

	def _acceptsClose( self ) :

		unsavedScripts = self.__unsavedScriptFilenames()

		if not unsavedScripts:
			return True

		plural = len(unsavedScripts) > 1

		dialogue = GafferUI.ConfirmationDialogue(
			"Discard Unsaved Changes?",
			"The %s %s %s unsaved changes. Do you want to discard them?" % ("files" if plural else "file" , ", ".join( unsavedScripts ), "have" if plural else "has"),
			confirmLabel = "Discard"
		)
		return dialogue.waitForConfirmation( parentWindow=self )

	def acceptsTabClose(self, scriptWidget):

		scriptNode = scriptWidget.scriptNode()
		if not scriptNode["unsavedChanges"].getValue() :
			return True

		f = scriptNode["fileName"].getValue()
		f = f.rpartition( "/" )[2] if f else "untitled"

		dialogue = GafferUI.ConfirmationDialogue(
			"Discard Unsaved Changes?",
			"The file %s has unsaved changes. Do you want to discard them?" % f,
			confirmLabel = "Discard"
		)
		return dialogue.waitForConfirmation( parentWindow=self )

	def activeScriptWidget(self):
		return self.__scriptTabbedContainer.getCurrent()

	def applicationRoot( self ) :
		return self.__applicationRoot


