##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

## \todo Need to update when plugs are dirtied.
## \todo Decent representation of shaders.
## \todo Make the label column fixed width.
## \todo Have links to show you where in the hierarchy an attribute was set
## and to take you to the node that set it.
class SceneInspector( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :
	
		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 8 )
		
		GafferUI.NodeSetEditor.__init__( self, column, scriptNode, **kw )
		
		with column :
			with GafferUI.ScrolledContainer() :
				self.__textWidget = GafferUI.Label()#MultiLineTextWidget( editable = False )
		
		self._updateFromSet()
				
	def __repr__( self ) :

		return "GafferSceneUI.SceneInspector( scriptNode )"

	def _updateFromSet( self ) :
		
		self.__update()
				
	def _updateFromContext( self ) :
	
		self.__update()
	
	def __update( self ) :
			
		sceneNodes = [ node for node in self.getNodeSet() if isinstance( node, GafferScene.SceneNode ) ]
		selectedPaths = self.getContext().get( "ui:scene:selectedPaths", [] )

		self.__textWidget.setText( "" )
		
		numCombinations = len( sceneNodes ) * len( selectedPaths )
		if numCombinations == 0 or numCombinations > 2 :
			return
		
		inspections = []
		with self.getContext() :
			for node in sceneNodes :
				for path in selectedPaths :
					inspections.append( self.__inspect( node, path ) )
				
		html = "<table cellpadding=4 cellspacing=0 style='table-layout: fixed;'>"

		rows = []
		self.__appendRow( rows, "Node", inspections, "node" )
		self.__appendRow( rows, "Path", inspections, "path" )
		self.__appendRow( rows, "Transform", inspections, "transform" )
		self.__appendRow( rows, "Bound", inspections, "bound" )
		
		for keyPrefix, heading in [ ( "attr:", "Attributes" ), ( "object:", "Object" ) ] :
			
			keys = set()
			for inspection in inspections :
				keys |= set( [ k for k in inspection.keys() if k.startswith( keyPrefix ) ] )
			if len( keys ) :
	
				self.__appendRow( rows, "<h3>" + heading + "</h3>" )
					
				keys = sorted( list( keys ) )
				for index, key in enumerate( keys ) :
					self.__appendRow( rows, key[len( keyPrefix ):], inspections, key )
		
		html += "\n".join( rows )
		
		html += "</table>"
						
		self.__textWidget.setText( html )
	
	def __inspect( self, node, path ) :
	
		# basic info
		
		result = {}
		result["node"] = node.relativeName( node.ancestor( Gaffer.ScriptNode.staticTypeId() ) )
		result["path"] = path
		result["bound"] = node["out"].bound( path )
		
		# transform
		
		transform = node["out"].transform( path )
		if transform != IECore.M44f() :
			result["transform"] = transform
		
		# attributes
		
		pathParts = path.strip( "/" ).split( "/" )
		for i in range( 0, len( pathParts ) + 1 ) :
			path = "/" + "/".join( pathParts[:i] )
			attributes = node["out"].attributes( path )
			if attributes :
				for k, v in attributes.items() :
					result["attr:" + k] = v
		
		# object
		
		object = node["out"].object( path )
		if object is not None :
			result["object:Type"] = object.typeName()
			result["object:Primitive Variables"] = " ".join( sorted( object.keys() ) )
		
		return result
	
	def __appendRow( self, rows, label, inspections=[], name=None ) :
	
		if name is not None and name not in inspections[0] :
			return
	
		backgroundColor = "#454545" if len( rows ) % 2 else "#4c4c4c"
		
		row = "<tr>"
		row += "<td align=right bgcolor=%s><b>%s</b></td>" % ( backgroundColor, label )
		
		valueText = ""
		if inspections and name is not None :
			valueText = self.__diff( inspections, name )
			
		row += "<td bgcolor=%s>%s</td>" % ( backgroundColor, valueText )
		row += "</tr>"
	
		rows.append( row )
		
	def __diff( self, inspections, name ) :
		
		if len( inspections ) == 1 :
			return self.__formatValue( inspections[0][name] )
		elif name in inspections[0] and name in inspections[1] and inspections[0][name] == inspections[1][name] :
			return self.__formatValue( inspections[0][name] )
		else :
	
			result = "<table>"
			
			if name in inspections[0] :
				result += "<tr>"
				result += "<td bgcolor=#623131>%s</td>" % self.__formatValue( inspections[0][name] )
				result += "</tr>"
				
			if name in inspections[1] :
				result += "<tr>"
				result += "<td bgcolor=#285b38>%s</td>" % self.__formatValue( inspections[1][name] )
				result += "</tr>"
				
			result += "</table>"
			
			return result	
	
	def __formatValue( self, value ) :
	
		if isinstance( value, ( IECore.M44f, IECore.M44d ) ) :
			return self.__formatMatrix( value )
		elif isinstance( value, ( IECore.Box3f, IECore.Box3d ) ) :
			return self.__formatBox( value )
		else :
			return str( value )
	
	def __formatMatrix( self, matrix ) :
		
		result = "<table cellpadding=3>"
		for i in range( 0, 4 ) :
			result += "<tr>"
			for j in range( 0, 4 ) :
				result += "<td>" + str( matrix[i,j] ) + "</td>"
			result += "</tr>"
		result += "</table>"
		
		return result
		
	def __formatBox( self, box ) :
	
		result = "<table cellpadding=3>"
		for v in ( box.min, box.max ) :
			result += "<tr>"
			for i in range( 0, 3 ) :
				result += "<td>" + str( v[i] ) + "</td>"
			result += "</tr>"
		result += "</table>"
		
		return result

GafferUI.EditorWidget.registerType( "SceneInspector", SceneInspector )
