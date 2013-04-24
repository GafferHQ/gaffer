##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import weakref

import IECore

import Gaffer
import GafferUI

class NodeEditor( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :
	
		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		
		GafferUI.NodeSetEditor.__init__( self, self.__column, scriptNode, **kw )
		
		self._updateFromSet()
	
	## Ensures that the specified node has a visible NodeEditor editing it, creating
	# one if necessary.
	## \todo User preferences for whether these are made floating, embedded, whether
	# they are reused etc. This class should provide the behaviour, but the code for
	# linking it to preferences should be in a startup file.
	## \todo Consider how this relates to draggable editor tabs and editor floating
	# once we implement that in CompoundEditor - I suspect that acquire will become a method
	# on CompoundEditor instead at this point.
	@classmethod
	def acquire( cls, node ) :
	
		if isinstance( node, Gaffer.ScriptNode ) :
			script = node
		else :
			script = node.scriptNode()
		
		scriptWindow = GafferUI.ScriptWindow.acquire( script )
		
		for editor in scriptWindow.getLayout().editors( type = GafferUI.NodeEditor ) :
			if node.isSame( editor._lastAddedNode() ) :
				tabbedContainer = editor.ancestor( GafferUI.TabbedContainer )
				if tabbedContainer is not None :
					tabbedContainer.setCurrent( editor )
				return editor
		
		childWindows = scriptWindow.childWindows()
		for window in childWindows :
			if hasattr( window, "nodeEditor" ) :
				if node in window.nodeEditor.getNodeSet() :
					window.setVisible( True )
					return window.nodeEditor
				
		window = GafferUI.Window( "Node Editor", borderWidth = 8 )
		window.nodeEditor = GafferUI.NodeEditor( script )
		window.nodeEditor.setNodeSet( Gaffer.StandardSet( [ node ] ) )
		window.setChild( window.nodeEditor )
		
		window.__closedConnection = window.closedSignal().connect( IECore.curry( cls.__deleteWindow, weakref.ref( window ) ) )
		window.__nodeParentChangedConnection = node.parentChangedSignal().connect( IECore.curry( cls.__deleteWindow, weakref.ref( window ) ) )
				
		scriptWindow.addChildWindow( window )
		
		window.setVisible( True )

		return window.nodeEditor
						
	def __repr__( self ) :

		return "GafferUI.NodeEditor( scriptNode )"

	def _updateFromSet( self ) :
		
		GafferUI.NodeSetEditor._updateFromSet( self )
				
		del self.__column[:]
		
		node = self._lastAddedNode()
		if not node :
			return
		
		with self.__column :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, borderWidth=8, spacing=4 ) :
				GafferUI.Label( "Node Name" )
				GafferUI.NameWidget( node )
				infoIcon = GafferUI.Image( "info.png" )
				toolTip = "<h3>" + node.typeName() + "</h3>"
				description = GafferUI.Metadata.nodeDescription( node )
				if description :
					toolTip += "\n\n" + description
				infoIcon.setToolTip( toolTip )
						
		frame = GafferUI.Frame( borderStyle=GafferUI.Frame.BorderStyle.None, borderWidth=0 )
		self.__column.append( frame, expand=True )
		frame.setChild( GafferUI.NodeUI.create( node ) )

	def _titleFormat( self ) :
	
		return GafferUI.NodeSetEditor._titleFormat( self, _maxNodes = 1, _reverseNodes = True, _ellipsis = False )
		
	@staticmethod
	def __deleteWindow( windowWeakRef, *unusedArgs ) :
	
		window = windowWeakRef()
		if window is None :
			return
			
		window.parent().removeChild( window )
				
GafferUI.EditorWidget.registerType( "NodeEditor", NodeEditor )
