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

import difflib
import collections

import IECore

import Gaffer
import GafferScene
import GafferUI

## \todo Have links to show you where in the hierarchy an attribute was set
## and to take you to the node that set it.
class SceneInspector( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :
		
		mainColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 8 )
		
		GafferUI.NodeSetEditor.__init__( self, mainColumn, scriptNode, **kw )
		
		self.__sections = []

		columns = {}
		with mainColumn :
			columns[None] = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 8 )
			tabbedContainer = GafferUI.TabbedContainer()
			
		for registration in self.__sectionRegistrations :
			section = registration.section()
			column = columns.get( registration.tab )
			if column is None :
				with tabbedContainer :
					with GafferUI.ScrolledContainer( horizontalMode = GafferUI.ScrolledContainer.ScrollMode.Never, parenting = { "label" : registration.tab } ) :
						column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 8 )
						columns[registration.tab] = column
			column.append( section )
			self.__sections.append( section )
		
		for tab, column in columns.items() :
			if tab is not None :
				column.append( GafferUI.Spacer( IECore.V2i( 0 ) ), expand = True )
		
		self.__pendingUpdate = False
		self._updateFromSet()

	## Simple struct to specify the target of an inspection.
	Target = collections.namedtuple( "SceneAndPath", [ "scene", "path" ] )
	
	@classmethod
	def registerSection( cls, section, tab ) :
	
		assert( issubclass( section, cls.Section ) )
	
		cls.__sectionRegistrations.append( cls.__SectionRegistration( section = section, tab = tab ) )
	
	__SectionRegistration = collections.namedtuple( "SectionRegistration", [ "section", "tab" ] )
	__sectionRegistrations = []
				
	def __repr__( self ) :

		return "GafferSceneUI.SceneInspector( scriptNode )"

	def _updateFromSet( self ) :
		
		GafferUI.NodeSetEditor._updateFromSet( self )

		self.__scenePlugs = []
		self.__plugDirtiedConnections = []
		self.__parentChangedConnections = []
		for node in self.getNodeSet()[-2:] :
			outputScenePlugs = [ p for p in node.children( GafferScene.ScenePlug ) if p.direction() == Gaffer.Plug.Direction.Out ]
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
		
		assert( len( self.__scenePlugs ) <= 2 )
		paths = self.getContext().get( "ui:scene:selectedPaths", [] )
		paths = paths[:2] if len( self.__scenePlugs ) < 2 else paths[:1]
		if not paths :
			paths = [ "/" ]
			
		targets = []
		for scene in self.__scenePlugs :
			for path in paths :
				targets.append( self.Target( scene, path ) )
		
		with self.getContext() :
			for section in self.__sections :
				section.update( targets )
			
		return False # remove idle callback

GafferUI.EditorWidget.registerType( "SceneInspector", SceneInspector )

##########################################################################
# Diff
##########################################################################

## Base class for widgets which want to display a diff view for a pair
# of values. It maintains two frames, one for each value, and in update()
# it displays one or both of the frames, with background colours appropriate
# to the relationship between the two values.
class Diff( GafferUI.Widget ) :

	def __init__( self, orientation=GafferUI.ListContainer.Orientation.Vertical, **kw ) :
	
		self.__column = GafferUI.ListContainer( orientation )
		GafferUI.Widget.__init__( self, self.__column, **kw )

		with self.__column :
			for i in range( 0, 2 ) :
				GafferUI.Frame(
					borderWidth = 4,
					borderStyle = GafferUI.Frame.BorderStyle.None,
					parenting = { "expand" : True }
				)
		
		## \todo Should we provide frame types via methods on the
		# Frame class? Are DiffA/DiffB types for a frame a bit too
		# specialised?
		self.__column[1]._qtWidget().setObjectName( "gafferDiffB" )
	
	def frame( self, index ) :
	
		return self.__column[index]
	
	## Updates the UI to reflect the relationship between the values.
	# If they are equal or if there is only one, then only the first
	# frame is shown, with a default background colour. If there are
	# two and they differ, then both frames are shown, with red and
	# green backgrounds respectively. Derived classes are expected to
	# override this method to additionally edit widgets inside the
	# frames to display the actual values.
	def update( self, values ) :
	
		assert( len( values ) <= 2 )
		
		different = len( values ) > 1 and values[0] != values[1]
				
		self.frame( 0 ).setVisible( len( values ) > 0 and values[0] is not None )
		self.frame( 1 ).setVisible( len( values ) > 1 and values[1] is not None and different )
		
		self.frame( 0 )._qtWidget().setObjectName( "gafferDiffA" if different else "" )
		self.frame( 0 )._repolish()

class TextDiff( Diff ) :

	def __init__( self, orientation=GafferUI.ListContainer.Orientation.Vertical, highlightDiffs=True, **kw ) :
	
		Diff.__init__( self, orientation, **kw )
	
		self.frame( 0 ).setChild( GafferUI.Label() )
		self.frame( 1 ).setChild( GafferUI.Label() )
		
		self.__highlightDiffs = highlightDiffs
		
	def update( self, values ) :
	
		Diff.update( self, values )
		
		formattedValues = self.__formatValues( values )
		for i, value in enumerate( formattedValues ) :
			self.frame( i ).getChild().setText( self.__htmlHeader + value + self.__htmlFooter )
		
	def __formatValues( self, values ) :
		
		if len( values ) == 0 :
			return []
		elif len( values ) == 2 and type( values[0] ) != type( values[1] ) :
			# different types - format each separately
			return self.__formatValues( [ values[0] ] ) + self.__formatValues( [ values[1] ] )
		elif isinstance( values[0], IECore.Data ) and hasattr( values[0], "value" ) :
			return self.__formatValues( [ v.value for v in values ] )
		elif isinstance( values[0], ( IECore.V3f, IECore.V2f ) ) :
			return self.__formatVectors( values )
		elif isinstance( values[0], ( IECore.M44f, IECore.M44d ) ) :
			return self.__formatMatrices( values )
		elif isinstance( values[0], ( IECore.Box3f, IECore.Box3d, IECore.Box2f, IECore.Box2d ) ) :
			return self.__formatBoxes( values )
		elif isinstance( values[0], IECore.ObjectVector ) :
			return self.__formatShaders( values )
		elif isinstance( values[0], float ) :
			return self.__formatFloats( values )
		elif isinstance( values[0], basestring ) :
			return self.__formatStrings( [ str( v ) for v in values ] )
		else :
			return [ str( v ) for v in values ]
			
	def __formatVectors( self, vectors ) :
	
		# it'd be nice to control cellspacing in the stylesheet, but qt doesn't seem to support it
		result = [ "<table cellspacing=2><tr>" ] * len( vectors )
		for i in range( 0, vectors[0].dimensions() ) :
			cells = self.__formatFloatsAsTableCells( [ v[i] for v in vectors ] )
			for resultIndex, cell in enumerate( cells ) :
					result[resultIndex] += cell
		result = [ r + "</tr></table>" for r in result ]
		
		return result
		
	def __formatMatrices( self, matrices ) :
		
		# it'd be nice to control cellspacing in the stylesheet, but qt doesn't seem to support it
		result = [ "<table cellspacing=2>" ] * len( matrices )
		for i in range( 0, 4 ) :
			result = [ r + "<tr>" for r in result ]
			for j in range( 0, 4 ) :
				cells = self.__formatFloatsAsTableCells( [ m[i,j] for m in matrices ] )
				for resultIndex, cell in enumerate( cells ) :
					result[resultIndex] += cell
			result = [ r + "</tr>" for r in result ]
		result = [ r + "</table>" for r in result ]
		
		return result
		
	def __formatBoxes( self, boxes ) :
		
		if len( boxes ) == 2 and ( boxes[0].isEmpty() or boxes[1].isEmpty() ) :
			# We can't diff empty boxes against non-empty, because they're formatted differently.
			return [ self.__formatBoxes( [ b ] )[0] if not b.isEmpty() else "Empty" for b in boxes ]
		
		# it'd be nice to control cellspacing in the stylesheet, but qt doesn't seem to support it
		result = [ "<table cellspacing=2>" ] * len( boxes )
		for field in ( "min", "max" ) :
			result = [ r + "<tr>" for r in result ]
			for i in range( 0, boxes[0].min.dimensions() ) :
				cells = self.__formatFloatsAsTableCells( [ getattr( b, field )[i] for b in boxes ] )
				for resultIndex, cell in enumerate( cells ) :
					result[resultIndex] += cell
			result = [ r + "</tr>" for r in result ]
		result = [ r + "</table>" for r in result ]
		
		return result

	def __formatFloats( self, values ) :

		return self.__formatStrings( [ self.__formatFloat( v ) for v in values ] )
	
	def __formatFloatsAsTableCells( self, values ) :
	
		different = len( values ) == 2 and values[0] != values[1]
		if not different or not self.__highlightDiffs :
			return [ "<td>" + self.__formatFloat( v ) + "</td>" for v in values ]
		else :
			# need to use internal span to prevent the class getting applied to not only the td
			# but also the internal text, doubling up on the effect.
			return [
				"<td class=diffA><span class=>" + self.__formatFloat( values[0] ) + "</span></td>",
				"<td class=diffB><span class=>" + self.__formatFloat( values[1] ) + "</span></td>",
			]
					
	def __formatShaders( self, values ) :
	
		formattedValues = []
		for value in values :
			shaderName = value[-1].name
			nodeName = value[-1].blindData().get( "gaffer:nodeName", None )
			if nodeName is not None and nodeName.value != shaderName :
				formattedValues.append( "%s (%s)" % ( nodeName.value, shaderName ) )
			else :
				formattedValues.append( shaderName )
				
		return self.__formatStrings( formattedValues )

	def __formatStrings( self, strings ) :
	
		if len( strings ) == 1 :
			return strings

		a = strings[0]
		b = strings[1]

		if a == b or not self.__highlightDiffs :
			return strings

		aFormatted = ""
		bFormatted = ""
		for op, a1, a2, b1, b2 in difflib.SequenceMatcher( None, a, b ).get_opcodes() :

			if op == "equal" :
				aFormatted += a[a1:a2]
				bFormatted += b[b1:b2]
			elif op == "replace" :
				aFormatted += '<span class="diffA">' + a[a1:a2] + "</span>"
				bFormatted += '<span class="diffB">' + b[b1:b2] + "</span>"
			elif op == "delete" :
				aFormatted += '<span class="diffA">' + a[a1:a2] + "</span>"
			elif op == "insert" :
				bFormatted += '<span class="diffB">' + b[b1:b2] + "</span>"

		return [ aFormatted, bFormatted ]

	def __formatFloat( self, value ) :
	
		if value == 0.0 :
			# this makes sure -0 is returned as 0
			return "0"
			
		return ( "%.4f" % value ).rstrip( '0' ).rstrip( '.' )

	__htmlHeader = (
		"<html><head><style type=text/css>"
		".diffA { background-color:rgba( 255, 77, 3, 75 ); }"
		".diffB { background-color:rgba( 167, 214, 6, 75 ); }"
		"td { padding:3px; }"
		"</style></head>"
		"<body>"
	)
	
	__htmlFooter = "</body></html>"

##########################################################################
# Row
##########################################################################

## A class to simplify the process of making a row containing a label
# and some content, and for colouring rows alternately.
class Row( GafferUI.Widget ) :

	def __init__( self, label, content, alternate = False, **kw ) :
	
		self.__frame = GafferUI.Frame( borderWidth = 4 )
	
		GafferUI.Widget.__init__( self, self.__frame, **kw )

		with self.__frame :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) as self.__row :
				label = GafferUI.Label(
					label,
					horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right,
					verticalAlignment = GafferUI.Label.VerticalAlignment.Top
				)
				label._qtWidget().setFixedWidth( 150 )
				self.__row.append( content )
				GafferUI.Spacer( IECore.V2i( 0 ), parenting = { "expand" : True } )
		
		self.setAlternate( alternate )
		
	def setContent( self, content ) :
	
		self.__row[1] = content
		
	def getContent( self ) :
	
		return self.__row[1]

	def setAlternate( self, alternate ) :

		self.__frame._qtWidget().setObjectName( "gafferLighter" if alternate else "" )
	
	def getAlternate( self ) :
	
		return self.__frame._qtWidget.objectName() == "gafferLighter"

##########################################################################
# Section
##########################################################################

## Base class for widgets which make up a section of the SceneInspector.
class Section( GafferUI.Widget ) :

	def __init__( self, collapsed = False, label = None, **kw ) :
	
		self.__mainColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 0 )
		self.__collapsible = None
		if collapsed is not None :
			self.__collapsible = GafferUI.Collapsible( label=label, collapsed=collapsed )
			self.__collapsible.setChild( self.__mainColumn )
		
		GafferUI.Widget.__init__( self, self.__collapsible if self.__collapsible is not None else self.__mainColumn, **kw )
	
		self.__numRows = 0
	
	def update( self, targets ) :
	
		raise NotImplementedError

	def _mainColumn( self ) :
	
		return self.__mainColumn

# export classes for use in custom sections
SceneInspector.Row = Row
SceneInspector.Diff = Diff
SceneInspector.TextDiff = TextDiff
SceneInspector.Section = Section

##########################################################################
# Private section implementations
##########################################################################

class __NodeSection( Section ) :

	def __init__( self ) :
					
		Section.__init__( self, collapsed = None )

		with self._mainColumn() :
			self.__row = Row( "Node Name", TextDiff( highlightDiffs = False ) )

	def update( self, targets ) :
		
		values = []
		for target in targets :
			node = target.scene.node()
			values.append( node.relativeName( node.ancestor( Gaffer.ScriptNode ) ) )
		
		self.__row.getContent().update( values )

SceneInspector.registerSection( __NodeSection, tab = None )

class __PathSection( Section ) :

	def __init__( self ) :
		
		Section.__init__( self, collapsed = None )

		with self._mainColumn() :
			self.__row = Row( "Location", TextDiff() )
			
	def update( self, targets ) :
			
		self.__row.getContent().update( [ target.path for target in targets ] )

SceneInspector.registerSection( __PathSection, tab = "Selection" )

class __TransformSection( Section ) :

	def __init__( self ) :
	
		Section.__init__( self, collapsed = True, label = "Transform" )
		
		with self._mainColumn() :
			self.__localMatrixRow = Row( "Local", TextDiff( orientation = GafferUI.ListContainer.Orientation.Horizontal ) )
			self.__worldMatrixRow = Row( "World", TextDiff( orientation = GafferUI.ListContainer.Orientation.Horizontal ), alternate = True )
		
	def update( self, targets ) :
	
		self.__localMatrixRow.getContent().update( [ target.scene.transform( target.path ) for target in targets ] )
		self.__worldMatrixRow.getContent().update( [ target.scene.fullTransform( target.path ) for target in targets ] )
		
SceneInspector.registerSection( __TransformSection, tab = "Selection" )

class __BoundSection( Section ) :

	def __init__( self ) :
	
		Section.__init__( self, collapsed = True, label = "Bounding box" )
		
		with self._mainColumn() :
			self.__localBoundRow = Row( "Local", TextDiff( orientation = GafferUI.ListContainer.Orientation.Horizontal ) )
			self.__worldBoundRow = Row( "World", TextDiff( orientation = GafferUI.ListContainer.Orientation.Horizontal ), alternate = True )
	
	def update( self, targets ) :
	
		localBounds = []
		worldBounds = []
		for target in targets :
			bound = target.scene.bound( target.path )
			transform = target.scene.fullTransform( target.path )
			localBounds.append( bound )
			worldBounds.append( bound.transform( transform ) )
			
		self.__localBoundRow.getContent().update( localBounds )
		self.__worldBoundRow.getContent().update( worldBounds )
		
SceneInspector.registerSection( __BoundSection, tab = "Selection" )

class __AttributesSection( Section ) :

	def __init__( self ) :
	
		Section.__init__( self, collapsed = True, label = "Attributes" )
	
		self.__rows = {} # mapping from attribute name to row
		
	def update( self, targets ) :
	
		attributes = []
		for target in targets :
			attributes.append( target.scene.fullAttributes( target.path ) )
		
		rows = []
		attributeNames = sorted( set( reduce( lambda k, a : k + a.keys(), attributes, [] ) ) )
		for attributeName in attributeNames :
			
			row = self.__rows.get( attributeName )
			if row is None :
				row = Row( attributeName, TextDiff() )
				self.__rows[attributeName] = row
			
			values = [ a.get( attributeName ) for a in attributes ]
			row.getContent().update( values )
			
			row.setAlternate( len( rows ) % 2 )
			
			rows.append( row )
		
		self._mainColumn()[:] = rows
		
SceneInspector.registerSection( __AttributesSection, tab = "Selection" )

class __ObjectSection( Section ) :

	def __init__( self ) :
	
		Section.__init__( self, collapsed = True, label = "Object" )
	
		with self._mainColumn() :
			self.__typeRow = Row( "Type", TextDiff() )
			self.__uniformRow = Row( "Uniform", TextDiff(), alternate = True )
			self.__vertexRow = Row( "Vertex", TextDiff() )
			self.__varyingRow = Row( "Varying", TextDiff(), alternate = True )
			self.__faceVaryingRow = Row( "FaceVarying", TextDiff() )
			self.__variablesRow = Row( "Variables", TextDiff(), alternate = True )
			
	def update( self, targets ) :
	
		objects = []
		for target in targets :
			objects.append( target.scene.object( target.path ) )
		
		self.__typeRow.getContent().update(
			[ object.typeName() if not isinstance( object, IECore.NullObject ) else None for object in objects ]
		)
		
		self.__uniformRow.getContent().update(
			[ object.variableSize( IECore.PrimitiveVariable.Interpolation.Uniform ) if isinstance( object, IECore.Primitive ) else None for object in objects ]		
		)
		
		self.__vertexRow.getContent().update(
			[ object.variableSize( IECore.PrimitiveVariable.Interpolation.Vertex ) if isinstance( object, IECore.Primitive ) else None for object in objects ]		
		)
		
		self.__varyingRow.getContent().update(
			[ object.variableSize( IECore.PrimitiveVariable.Interpolation.Varying ) if isinstance( object, IECore.Primitive ) else None for object in objects ]		
		)
		
		self.__faceVaryingRow.getContent().update(
			[ object.variableSize( IECore.PrimitiveVariable.Interpolation.FaceVarying ) if isinstance( object, IECore.Primitive ) else None for object in objects ]		
		)
		
		self.__variablesRow.getContent().update(
			[ " ".join( sorted( object.keys() ) ) if isinstance( object, IECore.Primitive ) else None for object in objects ]
		)
		
SceneInspector.registerSection( __ObjectSection, tab = "Selection" )

class __OptionsSection( Section ) :

	def __init__( self ) :
	
		Section.__init__( self, collapsed = True, label = "Options" )
	
		self.__rows = {} # mapping from option name to row
		
	def update( self, targets ) :
	
		options = []
		for target in targets :
			options.append( target.scene["globals"].getValue() )
		
		rows = []
		optionNames = sorted( set( reduce( lambda k, o : k + o.keys(), options, [] ) ) )
		for optionName in optionNames :
			
			if optionName == "gaffer:sets" :
				# this will be displayed by a specialised section
				continue
			
			row = self.__rows.get( optionName )
			if row is None :
				row = Row( optionName, TextDiff() )
				self.__rows[optionName] = row
			
			values = [ o.get( optionName ) for o in options ]
			row.getContent().update( values )
			
			row.setAlternate( len( rows ) % 2 )
			
			rows.append( row )
		
		self._mainColumn()[:] = rows
		
SceneInspector.registerSection( __OptionsSection, tab = "Globals" )
