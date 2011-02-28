##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

from PySide import QtGui

import IECore

from Gaffer import ScriptNode
import GafferUI
from Menu import Menu
from Widget import Widget
from EditorWidget import EditorWidget

## \todo Output redirection of both python stderr and stdout and IECore::msg - with the option to still output to the shell as well
#		- but how do we know which script editor to output to? eh?
#			- perhaps we should only output things that this editor does and ignore all other actions?
#			- then where do messages go? a special console ui?
## \todo Custom right click menu with script load, save, execute file, undo, redo etc.
## \todo Standard way for users to customise all menus
## \todo Tab completion and popup help. rlcompleter module should be useful for tab completion. Completer( dict ) constructs a completer
# that works in a specific namespace.
class ScriptEditor( GafferUI.EditorWidget ) :

	def __init__( self, scriptNode=None ) :
	
		GafferUI.EditorWidget.__init__( self, QtGui.QWidget(), scriptNode )
	
		layout = QtGui.QGridLayout()
		self._qtWidget().setLayout( layout )
		
		self.__splittable = GafferUI.SplitContainer()
		layout.addWidget( self.__splittable._qtWidget(), 0, 0 )
		
		self.__outputWidget = GafferUI.MultiLineTextWidget( editable = False )
		self.__inputWidget = GafferUI.MultiLineTextWidget()
		
		self.__splittable.append( self.__outputWidget )
		self.__splittable.append( self.__inputWidget )
	
		self.__inputWidgetKeyPressConnection = self.__inputWidget.keyPressSignal().connect( self.__keyPress )
	
## \todo ?
#		self.__gtkOutputWidget.connect( "button-press-event", self.__buttonPress )
#		self.__gtkInputWidget.connect( "button-press-event", self.__buttonPress )

	def setScriptNode( self, scriptNode ) :
	
		GafferUI.EditorWidget.setScriptNode( self, scriptNode )
		
		if scriptNode :
			self.__execConnection = self.getScriptNode().scriptExecutedSignal().connect( self.__execSlot )
			self.__evalConnection = self.getScriptNode().scriptEvaluatedSignal().connect( self.__evalSlot )
		else :
			self.__execConnection = None
			self.__evalConnection = None

	def __repr__( self ) :

		return "GafferUI.ScriptEditor()"
			
	def __execSlot( self, scriptNode, script ) :
	
		assert( scriptNode.isSame( self.getScriptNode() ) )
		self.__outputWidget.appendText( script )
		
	def __evalSlot( self, scriptNode, script, result ) :
	
		assert( scriptNode.isSame( self.getScriptNode() ) )
		text = script + "\nResult : " + str( result ) + "\n"
		self.__outputWidget.appendText( text )
		
	def __keyPress( self, widget, event ) :
		
		assert( widget is self.__inputWidget )
				
		if event.key=="Enter" or ( event.key=="Return" and event.modifiers==event.Modifiers.Control ) :
			
			haveSelection = True
			toExecute = widget.selectedText()
			if not toExecute :
				haveSelection = False
				toExecute = widget.getText()
			
			try :
			
				self.getScriptNode().execute( toExecute )
				if not haveSelection :
					widget.setText( "" )
			
			except Exception as e :
			
				self.__outputWidget.appendText( str( e ) )
			
			return True
			
		return False

#	def __buttonPress( self, widget, event ) :
#		
#		if event.button == 3 :
#		
#			haveSelection = False
#			if widget.get_buffer().get_selection_bounds() :
#				haveSelection = True
#			editable = widget.get_editable()
#			clipboard = gtk.Clipboard()
#						
#			m = IECore.MenuDefinition()
#			
#			if editable :
#				m.append( "/Cut", { "command" : IECore.curry( widget.get_buffer().cut_clipboard, clipboard, editable ), "active" : haveSelection } )	
#			m.append( "/Copy", { "command" : IECore.curry( widget.get_buffer().copy_clipboard, clipboard ), "active" : haveSelection } )	
#			if editable :
#				if clipboard.wait_for_text() :
#					pasteActive = True
#				else :
#					pasteActive = False
#				m.append( "/Paste", { "command" : IECore.curry( widget.get_buffer().paste_clipboard, clipboard, None, editable ), "active" : pasteActive } )	
#				m.append( "/Delete", { "command" : IECore.curry( widget.get_buffer().cut_clipboard, clipboard, editable ), "active" : haveSelection } )	
#			
#			m = Menu( m )
#			m.popup()
#			
#			return True
#			
#		return False
		
GafferUI.EditorWidget.registerType( "ScriptEditor", ScriptEditor )
