##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import GafferScene
import GafferUI

## \todo Make the label column fixed width.
## \todo Have links to show you where in the hierarchy an attribute was set
## and to take you to the node that set it.
class SceneInspector( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :
	
		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 8 )
		
		GafferUI.NodeSetEditor.__init__( self, column, scriptNode, **kw )
		
		with column :
			with GafferUI.ScrolledContainer() :
				self.__textWidget = GafferUI.Label()
		
		self.__pendingUpdate = False
		self._updateFromSet()
				
	def __repr__( self ) :

		return "GafferSceneUI.SceneInspector( scriptNode )"

	def _updateFromSet( self ) :
		
		GafferUI.NodeSetEditor._updateFromSet( self )

		self.__scenePlugs = []
		self.__plugDirtiedConnections = []
		self.__parentChangedConnections = []
		for node in self.getNodeSet()[-2:] :
			outputScenePlugs = [ p for p in node.children( GafferScene.ScenePlug.staticTypeId() ) if p.direction() == Gaffer.Plug.Direction.Out ]
			if len( outputScenePlugs ) :
				self.__scenePlugs.append( outputScenePlugs[0] )
				self.__plugDirtiedConnections.append( node.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ) ) )
				self.__parentChangedConnections.append( outputScenePlugs[0].parentChangedSignal().connect( Gaffer.WeakMethod( self.__plugParentChanged ) ) )

		self.__update()
				
	def _updateFromContext( self, modifiedItems ) :
	
		self.__update()
	
	def _titleFormat( self ) :
	
		return GafferUI.NodeSetEditor._titleFormat( self, _maxNodes = 2, _reverseNodes = True, _ellipsis = False )
	
	def __plugDirtied( self, plug ) :

		if self.__pendingUpdate :
			return
			
		if isinstance( plug, GafferScene.ScenePlug ) and plug.direction() == Gaffer.Plug.Direction.Out :
			self.__pendingUpdate = True
			GafferUI.EventLoop.addIdleCallback( self.__update )

	def __plugParentChanged( self, plug, oldParent ) :
	
		# if a plug has been removed or moved to another node, then
		# we need to stop viewing it - _updateFromSet() will find the
		# next suitable plug from the current node set.
		self._updateFromSet()

	def __update( self ) :

		self.__pendingUpdate = False

		selectedPaths = self.getContext().get( "ui:scene:selectedPaths", [] )

		self.__textWidget.setText( "" )
		
		numCombinations = len( self.__scenePlugs ) * len( selectedPaths )
		if numCombinations == 0 or numCombinations > 2 :
			return
		
		inspections = []
		with self.getContext() :
			for scenePlug in self.__scenePlugs :
				for path in selectedPaths :
					inspections.append( self.__inspect( scenePlug, path ) )
				
		html = "<table cellpadding=4 cellspacing=0 style='table-layout: fixed;'>"

		rows = []
		self.__appendDiffRow( rows, "Node", inspections, "node" )
		self.__appendDiffRow( rows, "Path", inspections, "path" )
		self.__appendDiffRow( rows, "Transform", inspections, "transform" )
		self.__appendDiffRow( rows, "Bound", inspections, "bound" )
		
		for keyPrefix, heading in [ ( "attr:", "Attributes" ), ( "object:", "Object" ) ] :
			
			keys = set()
			for inspection in inspections :
				keys |= set( [ k for k in inspection.keys() if k.startswith( keyPrefix ) ] )
			if len( keys ) :
				self.__appendRow( rows, "<h3>" + heading + "</h3>" )
				for key in sorted( list( keys ) ) :
					self.__appendDiffRow( rows, key[len( keyPrefix ):], inspections, key )
		
		html += "\n".join( rows )
		
		html += "</table>"
						
		self.__textWidget.setText( html )
	
		return False # remove idle callback

	def __inspect( self, plug, path ) :
	
		# basic info
		
		result = {}
		result["node"] = plug.node().relativeName( plug.ancestor( Gaffer.ScriptNode.staticTypeId() ) )
		result["path"] = path
		result["bound"] = plug.bound( path )
		
		# transform
		
		transform = plug.transform( path )
		if transform != IECore.M44f() :
			result["transform"] = transform
		
		# attributes
		
		pathParts = path.strip( "/" ).split( "/" )
		for i in range( 0, len( pathParts ) + 1 ) :
			path = "/" + "/".join( pathParts[:i] )
			attributes = plug.attributes( path )
			if attributes :
				for k, v in attributes.items() :
					result["attr:" + k] = v
		
		# object
		
		object = plug.object( path )
		if not isinstance( object, IECore.NullObject ) :
			
			result["object:Type"] = object.typeName()
			
			if isinstance( object, IECore.Primitive ) :
				
				result["object:Primitive Variables"] = " ".join( sorted( object.keys() ) )
				for interpName, interpValue in IECore.PrimitiveVariable.Interpolation.names.items() :
					if interpValue not in ( IECore.PrimitiveVariable.Interpolation.Invalid, IECore.PrimitiveVariable.Interpolation.Constant ) :
						result["object:Num " + interpName] = object.variableSize( interpValue )
				
				if isinstance( object, IECore.MeshPrimitive ) :
				
					result["object:Interpolation"] = object.interpolation
						
			elif isinstance( object, IECore.Camera ) :
				parameters = object.parameters()
				for key in sorted( parameters.keys() ) :
					result["object:"+key] = self.__formatValue( parameters[key] )
		
		return result
	
	def __appendRow( self, rows, label, value="" ) :
		
		backgroundColor = "#454545" if len( rows ) % 2 else "#4c4c4c"
		
		row = "<tr>"
		row += "<td align=right bgcolor=%s><b>%s</b></td>" % ( backgroundColor, label )
		row += "<td bgcolor=%s>%s</td>" % ( backgroundColor, value )
		row += "</tr>"
	
		rows.append( row )
	
	def __appendDiffRow( self, rows, label, inspections, key ) :
							
		if len( inspections ) == 1 :
			if key in inspections[0] :
				self.__appendRow( rows, label, self.__formatValue( inspections[0][key], key ) )
		elif key in inspections[0] and key in inspections[1] and inspections[0][key] == inspections[1][key] :
			self.__appendRow( rows, label, self.__formatValue( inspections[0][key], key ) )
		else :
	
			diff = "<table>"
			
			if key in inspections[0] :
				diff += "<tr>"
				diff += "<td bgcolor=#623131>%s</td>" % self.__formatValue( inspections[0][key], key )
				diff += "</tr>"
				
			if key in inspections[1] :
				diff += "<tr>"
				diff += "<td bgcolor=#285b38>%s</td>" % self.__formatValue( inspections[1][key], key )
				diff += "</tr>"
				
			diff += "</table>"

			self.__appendRow( rows, label, diff )
	
	# key is used as a formatting hint, it is not actually output in the format.
	def __formatValue( self, value, key = "" ) :
	
		if isinstance( value, ( IECore.M44f, IECore.M44d ) ) :
			return self.__formatMatrix( value )
		elif isinstance( value, ( IECore.Box3f, IECore.Box3d ) ) :
			return self.__formatBox( value )
		elif isinstance( value, IECore.ObjectVector ) and key.startswith( "attr:" ) and key.endswith( ":shader" ) :
			return self.__formatShader( value )
		else :
			return str( value )
	
	def __formatMatrix( self, matrix ) :
		
		result = "<table cellpadding=3>"
		for i in range( 0, 4 ) :
			result += "<tr>"
			for j in range( 0, 4 ) :
				result += "<td>" + self.__formatFloat( matrix[i,j] ) + "</td>"
			result += "</tr>"
		result += "</table>"
		
		return result
		
	def __formatBox( self, box ) :
		
		if box.isEmpty() :
			return "Empty"
			
		result = "<table cellpadding=3>"
		for v in ( box.min, box.max ) :
			result += "<tr>"
			for i in range( 0, 3 ) :
				result += "<td>" + self.__formatFloat( v[i] ) + "</td>"
			result += "</tr>"
		result += "</table>"
		
		return result

	def __formatFloat( self, value ) :

		return ( "%.4f" % value ).rstrip( '0' ).rstrip( '.' )

	def __formatShader( self, value ) :
	
		shaderName = value[-1].name
		nodeName = value[-1].blindData().get( "gaffer:nodeName", None )
		if nodeName is not None and nodeName.value != shaderName :
			return "%s (%s)" % ( nodeName.value, shaderName )
		else :
			return shaderName
		
GafferUI.EditorWidget.registerType( "SceneInspector", SceneInspector )
