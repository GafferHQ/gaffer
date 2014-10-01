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

import cgi
import math
import difflib
import itertools
import collections
import functools

import IECore

import Gaffer
import GafferScene
import GafferUI

class SceneInspector( GafferUI.NodeSetEditor ) :

	## A list of Section instances may be passed to create a custom inspector,
	# otherwise all registered Sections will be used.
	def __init__( self, scriptNode, sections = None, **kw ) :

		mainColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 8 )

		GafferUI.NodeSetEditor.__init__( self, mainColumn, scriptNode, **kw )

		self.__sections = []

		if sections is not None :

			for section in sections :
				mainColumn.append( section )
				self.__sections.append( section )

			mainColumn.append( GafferUI.Spacer( IECore.V2i( 0 ) ), expand = True )

		else :

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

		self.__visibilityChangedConnection = self.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__visibilityChanged ) )

		self.__pendingUpdate = False
		self.__targetPaths = None

		self.__playback = None
		self.__acquirePlayback()

		self._updateFromSet()

	## Simple struct to specify the target of an inspection.
	Target = collections.namedtuple( "Target", [ "scene", "path" ] )

	## May be used to "pin" target paths into the editor, rather than
	# having it automatically follow the scene selection. A value of
	# None causes selection to be followed again.
	def setTargetPaths( self, paths ) :

		if paths == self.__targetPaths :
			return

		assert( paths is None or len( paths ) == 1 or len( paths ) == 2 )

		self.__targetPaths = paths
		self.__scheduleUpdate()

	## Returns the last value passed to setTargetPaths().
	def getTargetPaths( self ) :

		return self.__targetPaths

	@classmethod
	def registerSection( cls, section, tab ) :

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

		self.__scheduleUpdate()

	def _updateFromContext( self, modifiedItems ) :

		self.__acquirePlayback() # if context was set to different instance, we need a new playback instance

		for item in modifiedItems :
			if not item.startswith( "ui:" ) or ( item == "ui:scene:selectedPaths" and self.__targetPaths is None ) :
				self.__scheduleUpdate()
				break

	def _titleFormat( self ) :

		return GafferUI.NodeSetEditor._titleFormat( self, _maxNodes = 2, _reverseNodes = True, _ellipsis = False )

	def __plugDirtied( self, plug ) :

		if isinstance( plug, GafferScene.ScenePlug ) and plug.direction() == Gaffer.Plug.Direction.Out :
			self.__scheduleUpdate()

	def __plugParentChanged( self, plug, oldParent ) :

		# if a plug has been removed or moved to another node, then
		# we need to stop viewing it - _updateFromSet() will find the
		# next suitable plug from the current node set.
		self._updateFromSet()

	def __scheduleUpdate( self ) :

		if self.__pendingUpdate :
			return

		self.__pendingUpdate = True
		if self.visible() and self.__playback.getState() == GafferUI.Playback.State.Stopped :
			GafferUI.EventLoop.addIdleCallback( Gaffer.WeakMethod( self.__update, fallbackResult = False ) )
		else :
			# we'll do the update in self.__visibilityChanged when
			# we next become visible, or in self.__playbackStateChanged
			# when playback stops
			pass

	def __update( self ) :

		self.__pendingUpdate = False

		assert( len( self.__scenePlugs ) <= 2 )

		if self.__targetPaths is not None :
			paths = self.__targetPaths
		else :
			paths = self.getContext().get( "ui:scene:selectedPaths", [] )
		paths = paths[:2] if len( self.__scenePlugs ) < 2 else paths[:1]
		if not paths :
			paths = [ "/" ]

		targets = []
		for scene in self.__scenePlugs :
			for path in paths :
				if not GafferScene.exists( scene, path ) :
					# selection may not be valid for both scenes,
					# and we can't inspect invalid paths.
					path = None
				targets.append( self.Target( scene, path ) )

		if next( (target.path for target in targets if target.path is not None), None ) is None :
			# all target paths have become invalid - if we're
			# in a popup window then close it.
			window = self.ancestor( _SectionWindow )
			if window is not None :
				window.parent().removeChild( window )

		with self.getContext() :
			for section in self.__sections :
				section.update( targets )

		return False # remove idle callback

	def __visibilityChanged( self, widget ) :

		assert( widget is self )

		if self.__pendingUpdate and self.visible() :
			self.__update()

	def __acquirePlayback( self ) :

		if self.__playback is None or not self.__playback.context().isSame( self.getContext() ) :
			self.__playback = GafferUI.Playback.acquire( self.getContext() )
			self.__playbackStateChangedConnection = self.__playback.stateChangedSignal().connect( Gaffer.WeakMethod( self.__playbackStateChanged ) )

	def __playbackStateChanged( self, playback ) :

		assert( playback is self.__playback )

		if self.__pendingUpdate and self.visible() and playback.getState() == playback.State.Stopped :
			self.__update()

GafferUI.EditorWidget.registerType( "SceneInspector", SceneInspector )

##########################################################################
# Diff
##########################################################################

## Abstract base class for widgets which display 0-2 values of
# the same type, highlighting the differences in some way when
# displaying 2 different values.
class Diff( GafferUI.Widget ) :

	def __init__( self, topLevelWidget, **kw ) :

		GafferUI.Widget.__init__( self, topLevelWidget, **kw )

	## Must be implemented to update the UI for the given
	# values.
	def update( self, values ) :

		raise NotImplementedError

# Base class for showing side-by-side diffs. It maintains two frames,
# one for each value, and in update() it displays one or both of the frames,
# with background colours appropriate to the relationship between the two
# values.
class SideBySideDiff( Diff ) :

	def __init__( self, **kw ) :

		self.__grid = GafferUI.GridContainer()
		Diff.__init__( self, self.__grid, **kw )

		with self.__grid :
			for i in range( 0, 2 ) :
				frame = GafferUI.Frame(
					borderWidth = 4,
					borderStyle = GafferUI.Frame.BorderStyle.None,
					parenting = { "index" : ( 0, i ) }
				)
				## \todo Should we provide frame types via methods on the
				# Frame class? Are DiffA/DiffB types for a frame a bit too
				# specialised?
				frame._qtWidget().setObjectName( "gafferDiffA" if i == 0 else "gafferDiffB" )

	def frame( self, index ) :

		return self.__grid[0,index]

	def setCornerWidget( self, index, widget ) :

		self.__grid.addChild(
			widget, index = ( 1, index ),
			alignment = ( GafferUI.HorizontalAlignment.Left, GafferUI.VerticalAlignment.Top )
		)

	def getCornerWidget( self, index ) :

		return self.__grid[1,index]

	## Updates the UI to reflect the relationship between the values.
	# If they are equal or if there is only one, then only the first
	# frame is shown, with a default background colour. If there are
	# two and they differ, then both frames are shown, with red and
	# green backgrounds respectively. Derived classes are expected to
	# override this method to additionally edit widgets inside the
	# frames to display the actual values.
	def update( self, values ) :

		assert( len( values ) <= 2 )

		# have to compare types before comparing values to avoid exceptions from
		# poor VectorTypedData.__cmp__ implementation.
		different = len( values ) > 1 and ( type( values[0] ) != type( values[1] ) or values[0] != values[1] )

		visibilities = [
			len( values ) > 0 and values[0] is not None,
			len( values ) > 1 and values[1] is not None and different
		]

		for i in range( 0, 2 ) :
			self.frame( i ).setVisible( visibilities[i] )
			cornerWidget = self.getCornerWidget( i )
			if cornerWidget is not None :
				cornerWidget.setVisible( visibilities[i] )

		name =  "gafferDiffA" if different else ""
		if name != self.frame( 0 )._qtWidget().objectName() :
			self.frame( 0 )._qtWidget().setObjectName( name )
			self.frame( 0 )._repolish()

class TextDiff( SideBySideDiff ) :

	def __init__( self, highlightDiffs=True, **kw ) :

		SideBySideDiff.__init__( self, **kw )

		self.__connections = []
		for i in range( 0, 2 ) :
			label = GafferUI.Label()
			self.__connections.append( label.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) ) )
			self.__connections.append( label.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) ) )
			self.__connections.append( label.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )	)
			self.frame( i ).setChild( label )

		self.__highlightDiffs = highlightDiffs

	def update( self, values ) :

		SideBySideDiff.update( self, values )

		self.__values = values

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
		elif isinstance( values[0], ( IECore.V3f, IECore.V3i, IECore.V2f, IECore.V2i ) ) :
			return self.__formatVectors( values )
		elif isinstance( values[0], ( IECore.M44f, IECore.M44d ) ) :
			return self.__formatMatrices( values )
		elif isinstance( values[0], ( IECore.Box3f, IECore.Box3d, IECore.Box3i, IECore.Box2f, IECore.Box2d, IECore.Box2i ) ) :
			return self.__formatBoxes( values )
		elif isinstance( values[0], IECore.ObjectVector ) :
			return self.__formatShaders( values )
		elif isinstance( values[0], ( float, int ) ) :
			return self.__formatNumbers( values )
		elif isinstance( values[0], basestring ) :
			return self.__formatStrings( [ str( v ) for v in values ] )
		else :
			return [ cgi.escape( str( v ) ) for v in values ]

	def __formatVectors( self, vectors ) :

		arrays = [ [ v ] for v in vectors ]
		return self.__formatNumberArrays( arrays )

	def __formatMatrices( self, matrices ) :

		arrays = []
		for matrix in matrices :
			array = []
			for i in range( 0, matrix.dimensions()[0] ) :
				array.append( [ matrix[i,j] for j in range( 0, matrix.dimensions()[1] ) ] )
			arrays.append( array )

		return self.__formatNumberArrays( arrays )

	def __formatBoxes( self, boxes ) :

		if any( b.isEmpty() for b in boxes ) :
			# We can't diff empty boxes against non-empty, because they're formatted differently.
			return [ self.__formatBoxes( [ b ] )[0] if not b.isEmpty() else "Empty" for b in boxes ]

		arrays = []
		for box in boxes :
			arrays.append( [ box.min, box.max ] )

		return self.__formatNumberArrays( arrays )

	def __formatNumbers( self, values ) :

		values = self.__numbersToAlignedStrings( values )
		values = self.__highlightFromFirstDifference( values )
		return [ "<pre>" + v + "</pre>" for v in values ]

	def __formatNumberArrays( self, values ) :

		# values is a list of 2d arrays of numbers.
		# stack one atop the other, and then format all
		# the values for each column together, so that they
		# are aligned.

		rows = itertools.chain( *values )
		columns = zip( *(row for row in rows) )
		formattedColumns = [ self.__numbersToAlignedStrings( c ) for c in columns ]

		# transform back into a list of 2d arrays of
		# formatted strings.
		formattedRows = zip( *formattedColumns )
		values = zip( *( [ iter( formattedRows ) ] * len( values[0] ) ) )

		# build the tables. it'd be nice to control cellspacing
		# in the stylesheet, but qt doesn't seem to support that.
		result = [ "<table cellspacing=2>" ] * len( values )
		for row in range( 0, len( values[0] ) ) :
			result = [ r + "<tr>" for r in result ]
			for column in range( 0, len( values[0][row] ) ) :
				cellValues = self.__highlightFromFirstDifference( [ v[row][column] for v in values ] )
				cells = [ "<td><pre>" + v + "</pre></td>" for v in cellValues ]
				for resultIndex, cell in enumerate( cells ) :
					result[resultIndex] += cell
			result = [ r + "</tr>" for r in result ]
		result = [ r + "</table>" for r in result ]

		return result

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

		if len( strings ) == 1 or strings[0] == strings[1] or not self.__highlightDiffs :
			return [ cgi.escape( s ) for s in strings ]

		a = strings[0]
		b = strings[1]

		aFormatted = ""
		bFormatted = ""
		for op, a1, a2, b1, b2 in difflib.SequenceMatcher( None, a, b ).get_opcodes() :

			if op == "equal" :
				aFormatted += cgi.escape( a[a1:a2] )
				bFormatted += cgi.escape( b[b1:b2] )
			elif op == "replace" :
				aFormatted += '<span class="diffA">' + cgi.escape( a[a1:a2] ) + "</span>"
				bFormatted += '<span class="diffB">' + cgi.escape( b[b1:b2] ) + "</span>"
			elif op == "delete" :
				aFormatted += '<span class="diffA">' + cgi.escape( a[a1:a2] ) + "</span>"
			elif op == "insert" :
				bFormatted += '<span class="diffB">' + cgi.escape( b[b1:b2] ) + "</span>"

		return [ aFormatted, bFormatted ]

	def __numbersToAlignedStrings( self, values ) :

		if isinstance( values[0], int ) :
			values = [ "%d" % v for v in values ]
		else :
			# the funky comparison with 0.0 converts -0.0 to 0.0
			values = [ "%.4f" % ( v if v != 0.0 else 0.0 ) for v in values ]

		if len( values ) > 1 :
			maxLength = max( len( v ) for v in values )
			values = [ v.rjust( maxLength ) for v in values ]

		return values

	def __highlightFromFirstDifference( self, values ) :

		if len( values ) < 2 or not self.__highlightDiffs :
			return values

		# d is the index of the first differing digit, or -1 if there is no difference
		d = next( ( i for i in xrange( 0, len( values[0] ) ) if values[0][i] != values[1][i] ), -1 )
		if d < 0 :
			return values

		return [
			values[0][:d] + "<span class=diffA>" + values[0][d:] + "</span>",
			values[1][:d] + "<span class=diffB>" + values[1][d:] + "</span>",
		]

	def __buttonPress( self, widget, event ) :

		return event.buttons == event.Buttons.Left

	def __dragBegin( self, widget, event ) :

		if event.buttons != event.Buttons.Left :
			return None

		GafferUI.Pointer.setCurrent( "values" )
		return self.__values[0] if self.frame( 0 ).isAncestorOf( widget ) else self.__values[1]

	def __dragEnd( self, widget, event ) :

		GafferUI.Pointer.setCurrent( None )

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

## A class to simplify the process of making rows with alternating colours.
class Row( GafferUI.Widget ) :

	def __init__( self, borderWidth = 4, alternate = False, **kw ) :

		self.__frame = GafferUI.Frame( borderWidth = borderWidth )

		GafferUI.Widget.__init__( self, self.__frame, **kw )

		self.__frame.setChild(
			 GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		)

		self.__alternate = None
		self.setAlternate( alternate )

	def listContainer( self ) :

		return self.__frame.getChild()

	def setAlternate( self, alternate ) :

		if alternate == self.__alternate :
			return

		self.__alternate = alternate
		self.__frame._qtWidget().setObjectName( "gafferLighter" if alternate else "" )
		self.__frame._repolish()

	def getAlternate( self ) :

		return self.__alternate

##########################################################################
# Inspector
##########################################################################

## Abstract class for a callable which inspects a Target and returns
# a value. Inspectors are key to allowing the UI to perform the same
# query over multiple targets to generate history and inheritance
# queries.
class Inspector( object ) :

	## Must be implemented to return a descriptive name
	# for what is being inspected.
	def name( self ) :

		raise NotImplementedError

	## Should return True if the Inspector's results
	# are based on attributes - this will enable inheritance
	# queries for the inspector.
	def inspectsAttributes( self ) :

		return False

	## Must be implemented to inspect the target and return
	# a value to be displayed. When inspectsAttributes()==True,
	# this method must accept an ignoreInheritance keyword
	# argument (defaulting to False).
	def __call__( self, target, **kw ) :

		raise NotImplementedError

	## May be implemented to return a list of "child" inspectors -
	# this is used by the DiffColumn to obtain an inspector per row.
	def children( self, target ) :

		return []

##########################################################################
# DiffRow
##########################################################################

## A row which displays a diff from values generated by an Inspector.
class DiffRow( Row ) :

	def __init__( self, inspector, diffCreator = TextDiff, alternate = False, **kw ) :

		assert( isinstance( inspector, Inspector ) )

		Row.__init__( self, alternate=alternate, **kw )

		with self.listContainer() :

			label = GafferUI.Label(
				inspector.name(),
				horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right,
				verticalAlignment = GafferUI.Label.VerticalAlignment.Top
			)
			label._qtWidget().setFixedWidth( 150 )

			diff = diffCreator()
			self.listContainer().append( diff )

			if inspector.inspectsAttributes() and isinstance( diff, SideBySideDiff ) :

				diff.setCornerWidget( 0, GafferUI.Label( "<sup>Inherited</sup>") )
				diff.setCornerWidget( 1, GafferUI.Label( "<sup>Inherited</sup>") )

			self.__diffConnections = []
			diffWidgets = [ diff.frame( 0 ), diff.frame( 1 ) ] if isinstance( diff, SideBySideDiff ) else [ diff ]
			for diffWidget in diffWidgets :
				self.__diffConnections.extend( [
					diffWidget.enterSignal().connect( Gaffer.WeakMethod( self.__enter ) ),
					diffWidget.leaveSignal().connect( Gaffer.WeakMethod( self.__leave ) ),
					diffWidget.contextMenuSignal().connect( Gaffer.WeakMethod( self.__contextMenu ) ),
				] )

			GafferUI.Spacer( IECore.V2i( 0 ), expand = True )

		self.__inspector = inspector
		self.__diffCreator = diffCreator

	def update( self, targets ) :

		self.__targets = targets
		self.__values = [ self.__inspector( target ) for target in targets ]
		self.__diff().update( self.__values )

		if self.__inspector.inspectsAttributes() :
			localValues = [ self.__inspector( target, ignoreInheritance=True ) for target in targets ]
			for i, value in enumerate( localValues ) :
				if value is not None and isinstance( self.__diff(), SideBySideDiff ) :
					self.__diff().getCornerWidget( i ).setVisible( False )

	def __label( self ) :

		return self.listContainer()[0]

	def __diff( self ) :

		return self.listContainer()[1]

	def __enter( self, widget ) :

		GafferUI.Pointer.setCurrent( "contextMenu" )

	def __leave( self, widget ) :

		GafferUI.Pointer.setCurrent( None )

	def __contextMenu( self, widget ) :

		GafferUI.Pointer.setCurrent( None )
		self.__menu = GafferUI.Menu( IECore.curry( Gaffer.WeakMethod( self.__menuDefinition ), widget ) )
		self.__menu.popup()

	def __menuDefinition( self, widget ) :

		diff = self.__diff()
		if isinstance( diff, SideBySideDiff ) :
			# For SideBySideDiffs, we know which target the user has clicked on
			# and only present menu items for that target.
			targets = [ self.__targets[ 0 if widget is diff.frame( 0 ) else 1 ] ]
		else :
			# But for other Diff types we don't know, and so present menu items
			# for any target which has a value.
			targets = [ t for i, t in enumerate( self.__targets ) if self.__values[i] is not None ]

		m = IECore.MenuDefinition()

		for i, target in enumerate( targets ) :

			if len( targets ) == 2 :
				labelSuffix = "/For " + ( "A", "B" )[i]
			else :
				labelSuffix = ""

			m.append(
				"/Show History" + labelSuffix,
				{
					"command" : IECore.curry( Gaffer.WeakMethod( self.__showHistory ), target ),
				}
			)

			if self.__inspector.inspectsAttributes() :

				m.append(
					"/Show Inheritance" + labelSuffix,
					{
						"command" : IECore.curry( Gaffer.WeakMethod( self.__showInheritance ), target ),
					}
				)

		return m

	def __showInheritance( self, target ) :

		w = _SectionWindow(
			target.scene.node().getName() + " : " + self.__label().getText(),
			_InheritanceSection( self.__inspector, self.__diffCreator ),
			target
		)

		self.ancestor( GafferUI.Window ).addChildWindow( w, removeOnClose = True )
		w.setVisible( True )

	def __showHistory( self, target ) :

		w = _SectionWindow(
			target.scene.node().getName() + " : " + self.__label().getText(),
			_HistorySection( self.__inspector, self.__diffCreator ),
			target
		)

		self.ancestor( GafferUI.Window ).addChildWindow( w, removeOnClose = True )
		w.setVisible( True )

##########################################################################
# DiffColumn
##########################################################################

## Class for displaying a column of DiffRows.
class DiffColumn( GafferUI.ListContainer ) :

	def __init__( self, inspector, diffCreator = TextDiff, **kw ) :

		GafferUI.ListContainer.__init__( self )

		assert( isinstance( inspector, Inspector ) )

		self.__inspector = inspector
		self.__rows = {} # mapping from row name to row
		self.__diffCreator = diffCreator

	def update( self, targets ) :

		inspectors = {}
		for target in targets :
			inspectors.update( { i.name() : i for i in self.__inspector.children( target ) } )

		rowNames = sorted( inspectors.keys() )

		rows = []
		for rowName in rowNames :

			row = self.__rows.get( rowName )
			if row is None :
				row = DiffRow( inspectors[rowName], self.__diffCreator )
				self.__rows[rowName] = row

			row.update( targets )
			row.setAlternate( len( rows ) % 2 )
			rows.append( row )

		self[:] = rows

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
SceneInspector.Diff = Diff
SceneInspector.SideBySideDiff = SideBySideDiff
SceneInspector.TextDiff = TextDiff
SceneInspector.Row = Row
SceneInspector.Inspector = Inspector
SceneInspector.DiffRow = DiffRow
SceneInspector.DiffColumn = DiffColumn
SceneInspector.Section = Section

##########################################################################
# Section window
##########################################################################

class _SectionWindow( GafferUI.Window ) :

	def __init__( self, title, section, target ) :

		GafferUI.Window.__init__( self, title, borderWidth = 4 )

		editor = SceneInspector( target.scene.ancestor( Gaffer.ScriptNode ), sections = [ section ] )
		editor.setTargetPaths( [ target.path ] )
		editor.setNodeSet( Gaffer.StandardSet( [ target.scene.node() ] ) )

		self.setChild( editor )

		self.__nodeSetMemberRemovedConnection = editor.getNodeSet().memberRemovedSignal().connect( Gaffer.WeakMethod( self.__nodeSetMemberRemoved ) )

	def __nodeSetMemberRemoved( self, set, node ) :

		self.parent().removeChild( self )

##########################################################################
# Inheritance section
##########################################################################

QtGui = GafferUI._qtImport( "QtGui" )

class _Rail( GafferUI.ListContainer ) :

	Type = IECore.Enum.create( "Top", "Middle", "Gap", "Bottom", "Single" )

	def __init__( self, type, **kw ) :

		GafferUI.ListContainer.__init__( self, **kw )

		with self :

			if type != self.Type.Top and type != self.Type.Single :
				image = GafferUI.Image( "railLine.png" )
				## \todo Decide how we do this via the public API.
				# Perhaps by putting the image in a Sizer? Or by
				# adding stretch methods to the Image class?
				image._qtWidget().setSizePolicy( QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred )
				image._qtWidget().setScaledContents( True )
			else :
				GafferUI.Spacer( IECore.V2i( 1 ) )

			GafferUI.Image( "rail" + str( type ) + ".png" )

			if type != self.Type.Bottom and type != self.Type.Single :
				image = GafferUI.Image( "railLine.png" )
				image._qtWidget().setSizePolicy( QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred )
				image._qtWidget().setScaledContents( True )
			else :
				GafferUI.Spacer( IECore.V2i( 1 ) )

class _InheritanceSection( Section ) :

	def __init__( self, inspector, diffCreator = TextDiff, **kw ) :

		Section.__init__( self, collapsed = None, **kw )

		self.__inspector = inspector
		self.__diffCreator = diffCreator

	def update( self, targets ) :

		self.__target = targets[0]
		self.__connections = []

		if self.__target.path is None :
			return

		rows = []

		fullPath = self.__target.path.split( "/" )[1:] if self.__target.path != "/" else []
		prevValue = None # local value from last iteration
		prevDisplayedValue = None # the last value we displayed
		fullValue = None # full value taking into account inheritance
		for i in range( 0, len( fullPath ) + 1 ) :

			path = "/" + "/".join( fullPath[:i] )
			value = self.__inspector( SceneInspector.Target( self.__target.scene, path ), ignoreInheritance=True )
			fullValue = value if value is not None else fullValue

			atEitherEnd = ( i == 0 or i == len( fullPath ) )

			if value is not None or atEitherEnd or prevValue is not None or i == 1 :

				row = Row( borderWidth = 0, alternate = len( rows ) % 2 )
				rows.append( row )
				with row.listContainer() :

					if atEitherEnd :
						_Rail( _Rail.Type.Top if i == 0 else _Rail.Type.Bottom )
					else :
						_Rail( _Rail.Type.Middle if value is not None else _Rail.Type.Gap )

					if atEitherEnd or value is not None :
						label = GafferUI.Label( path )
						label.setToolTip( "Click to select \"%s\"" % path )
						self.__connections.extend( [
							label.enterSignal().connect( lambda gadget : gadget.setHighlighted( True ) ),
							label.leaveSignal().connect( lambda gadget : gadget.setHighlighted( False ) ),
							label.buttonPressSignal().connect( IECore.curry( Gaffer.WeakMethod( self.__labelButtonPress ) ) ),
						] )
					else :
						GafferUI.Label( "..." )

					GafferUI.Spacer( IECore.V2i( 0 ), parenting = { "expand" : True } )

					if atEitherEnd or value is not None :
						d = self.__diffCreator()
						d.update( ( prevDisplayedValue, fullValue ) )
						if prevDisplayedValue != fullValue and isinstance( d, SideBySideDiff ) :
							d.frame( 0 ).setVisible( False )

				prevDisplayedValue = fullValue

			prevValue = value

		self._mainColumn()[:] = rows

	def __labelButtonPress( self, label, event ) :

		script = self.__target.scene.ancestor( Gaffer.ScriptNode )
		script.context()["ui:scene:selectedPaths"] = IECore.StringVectorData( [ label.getText() ] )

##########################################################################
# History section
##########################################################################

class _HistorySection( Section ) :

	__HistoryItem = collections.namedtuple( "__HistoryItem", [ "target", "value" ] )

	def __init__( self, inspector, diffCreator = TextDiff, **kw ) :

		Section.__init__( self, collapsed = None, **kw )

		self.__inspector = inspector
		self.__diffCreator = diffCreator

	def update( self, targets ) :

		self.__target = targets[0]
		self.__connections = []

		if self.__target.path is None :
			return

		history = []
		target = self.__target
		while target is not None :
			history.append( self.__HistoryItem( target, self.__inspector( target ) ) )
			target = self.__sourceTarget( target )
		history.reverse()

		rows = []
		for i in range( 0, len( history ) ) :

			if i >= 2 and history[i].value == history[i-1].value and history[i].value == history[i-2].value :
				if i != len( history ) - 1 :
					# if the last line we output was a gap, and this one would be too, then
					# just skip it.
					continue

			row = Row( borderWidth = 0, alternate = len( rows ) % 2 )
			rows.append( row )

			with row.listContainer() :

				if i == 0 :
					_Rail( _Rail.Type.Top if len( history ) > 1 else _Rail.Type.Single )
				elif i == len( history ) - 1 :
					_Rail( _Rail.Type.Bottom )
				else :
					if history[i-1].value == history[i].value :
						_Rail( _Rail.Type.Gap )
					else :
						_Rail( _Rail.Type.Middle )

				if i == 0 or i == ( len( history ) - 1 ) or history[i-1].value != history[i].value :
					GafferUI.NameLabel( history[i].target.scene.node(), formatter = lambda l : ".".join( x.getName() for x in l ) )
				else :
					GafferUI.Label( "..." )

				GafferUI.Spacer( IECore.V2i( 0 ), parenting = { "expand" : True } )

				diff = self.__diffCreator()
				diff.update( [
					history[i-1].value if i > 0 else None,
					history[i].value
				] )

				if (i == 0 or history[i-1].value != history[i].value) and isinstance( diff, SideBySideDiff ) :
					diff.frame( 0 if history[i].value is not None else 1 ).setVisible( False )

		self._mainColumn()[:] = rows

	def __sourceTarget( self, target ) :

		if isinstance( target.scene.node(), Gaffer.DependencyNode ) :

			sourceScene = target.scene.node().correspondingInput( target.scene )
			if sourceScene is None :
				return None

			sourceScene = sourceScene.source()
			if sourceScene.node() == target.scene.node() :
				return None

			if not GafferScene.exists( sourceScene, target.path ) :
				return None

			return SceneInspector.Target( sourceScene, target.path )

		return None

SceneInspector.HistorySection = _HistorySection ## REMOVE ME!!

##########################################################################
# Node section
##########################################################################

class __NodeSection( Section ) :

	def __init__( self ) :

		Section.__init__( self, collapsed = None )

		with self._mainColumn() :
			self.__row = DiffRow( self.__Inspector(), diffCreator = functools.partial( TextDiff, highlightDiffs = False ) )

	def update( self, targets ) :

		self.__row.update( targets )

	class __Inspector( Inspector ) :

		def name( self ) :

			return "Node Name"

		def __call__( self, target ) :

			node = target.scene.node()
			return node.relativeName( node.scriptNode() )

SceneInspector.registerSection( __NodeSection, tab = None )

##########################################################################
# Path section
##########################################################################

class __PathSection( Section ) :

	def __init__( self ) :

		Section.__init__( self, collapsed = None )

		with self._mainColumn() :
			self.__row = DiffRow( self.__Inspector(), functools.partial( TextDiff, highlightDiffs = False ) )

	def update( self, targets ) :

		self.__row.update( targets )

	class __Inspector( Inspector ) :

		def name( self ) :

			return "Location"

		def __call__( self, target ) :

			return target.path or "Invalid"

SceneInspector.registerSection( __PathSection, tab = "Selection" )

##########################################################################
# Transform section
##########################################################################

class __TransformSection( Section ) :

	def __init__( self ) :

		Section.__init__( self, collapsed = True, label = "Transform" )

		with self._mainColumn() :
			index = 0
			for transform in ( "transform", "fullTransform" )  :

				inspector = self.__Inspector( transform )
				DiffRow(
					inspector,
					alternate = index % 2,
				)
				index += 1

				for component in ( "t", "r", "s", "h" ) :

					DiffRow(
						self.__Inspector( transform, component ),
						diffCreator = functools.partial( self.__diffCreator, name = inspector.name() ),
						alternate = index % 2,
					)
					index += 1

	def update( self, targets ) :

		for row in self._mainColumn() :
			if isinstance( row, DiffRow ) :
				row.update( targets )

	@staticmethod
	def __diffCreator( name ) :

		diff = TextDiff()
		for i in range( 0, 2 ) :
			diff.setCornerWidget( i, GafferUI.Label( "<sup>From " + name + "</sup>" ) )

		return diff

	class __Inspector( Inspector ) :

		def __init__( self, accessor, component = None ) :

			self.__accessor = accessor
			self.__component = component

		def name( self ) :

			result = "Local" if self.__accessor == "transform" else "World"
			result += {
				"t" : " Translate",
				"r" : " Rotate",
				"s" : " Scale",
				"h" : " Shear",
				None : " Matrix",
			}[self.__component]

			return result

		def __call__( self, target ) :

			if target.path is None :
				return None

			matrix = getattr( target.scene, self.__accessor )( target.path )
			if self.__component is None :
				return matrix

			try :
				components = dict( zip( "shrt", matrix.extractSHRT() ) )
			except :
				# decomposition can fail if we have 0 scale.
				return "Unavailable"

			if self.__component == "r" :
				return components[self.__component] * 180.0 / math.pi
			else :
				return components[self.__component]

SceneInspector.registerSection( __TransformSection, tab = "Selection" )

##########################################################################
# Bound section
##########################################################################

class __BoundSection( Section ) :

	def __init__( self ) :

		Section.__init__( self, collapsed = True, label = "Bounding box" )

		with self._mainColumn() :
			self.__localBoundRow = DiffRow( self.__Inspector() )
			self.__worldBoundRow = DiffRow( self.__Inspector( world = True ), alternate = True )

	def update( self, targets ) :

		self.__localBoundRow.update( targets )
		self.__worldBoundRow.update( targets )

	class __Inspector( Inspector ) :

		def __init__( self, world=False ) :

			self.__world = world

		def name( self ) :

			return "World" if self.__world else "Local"

		def __call__( self, target ) :

			if target.path is None :
				return None

			bound = target.scene.bound( target.path )
			if self.__world :
				transform = target.scene.fullTransform( target.path )
				bound = bound.transform( transform )

			return bound

SceneInspector.registerSection( __BoundSection, tab = "Selection" )

##########################################################################
# Attributes section
##########################################################################

class __AttributesSection( Section ) :

	def __init__( self ) :

		Section.__init__( self, collapsed = True, label = "Attributes" )

		with self._mainColumn() :
			self.__diffColumn = DiffColumn( self.__Inspector() )

	def update( self, targets ) :

		self.__diffColumn.update( targets )

	class __Inspector( Inspector ) :

		def __init__( self, attributeName = None ) :

			self.__attributeName = attributeName

		def name( self ) :

			return self.__attributeName or ""

		def inspectsAttributes( self ) :

			return True

		def __call__( self, target, ignoreInheritance = False ) :

			if target.path is None :
				return None

			## \todo Investigate caching the results of these calls so that
			# not every Inspector instance is making the same call - maybe the target
			# could provide this service?
			if ignoreInheritance :
				attributes = target.scene.attributes( target.path )
			else :
				attributes = target.scene.fullAttributes( target.path )

			return attributes.get( self.__attributeName )

		def children( self, target ) :

			attributeNames = target.scene.fullAttributes( target.path ).keys() if target.path else []
			return [ self.__class__( attributeName ) for attributeName in attributeNames ]

SceneInspector.registerSection( __AttributesSection, tab = "Selection" )

##########################################################################
# Object section
##########################################################################

class __ObjectSection( Section ) :

	def __init__( self ) :

		Section.__init__( self, collapsed = True, label = "Object" )

		with self._mainColumn() :
			self.__typeRow = DiffRow( self.__TypeInspector() )
			self.__uniformRow = DiffRow( self.__SizeInspector( IECore.PrimitiveVariable.Interpolation.Uniform ), alternate = True )
			self.__vertexRow = DiffRow( self.__SizeInspector( IECore.PrimitiveVariable.Interpolation.Vertex )  )
			self.__varyingRow = DiffRow( self.__SizeInspector( IECore.PrimitiveVariable.Interpolation.Varying ), alternate = True )
			self.__faceVaryingRow = DiffRow( self.__SizeInspector( IECore.PrimitiveVariable.Interpolation.FaceVarying ) )
			self.__variablesRow = DiffRow( self.__VariablesInspector(), alternate = True )

	def update( self, targets ) :

		## \todo Since most section update calls now seem to just be calling update
		# on a bunch of rows, can we make that happen automatically?
		for row in self._mainColumn() :
			row.update( targets )

	class __TypeInspector( Inspector ) :

		def name( self ) :

			return "Type"

		def __call__( self, target ) :

			if target.path is None :
				return None

			## \todo Investigate caching the result of scene.object() on the target.
			object = target.scene.object( target.path )
			return object.typeName() if not isinstance( object, IECore.NullObject ) else None

	class __SizeInspector( Inspector ) :

		def __init__( self, interpolation ) :

			self.__interpolation = interpolation

		def name( self ) :

			return str( self.__interpolation )

		def __call__( self, target ) :

			if target.path is None :
				return None

			object = target.scene.object( target.path )
			return object.variableSize( self.__interpolation ) if isinstance( object, IECore.Primitive ) else None

	class __VariablesInspector( Inspector ) :

		def name( self ) :

			return "Variables"

		def __call__( self, target ) :

			if target.path is None :
				return None

			object = target.scene.object( target.path )
			return " ".join( sorted( object.keys() ) ) if isinstance( object, IECore.Primitive ) else None

SceneInspector.registerSection( __ObjectSection, tab = "Selection" )

##########################################################################
# Set Membership section
##########################################################################

class _SetMembershipDiff( SideBySideDiff ) :

	def __init__( self, **kw ) :

		SideBySideDiff.__init__( self, **kw )

		for i in range( 0, 2 ) :
			self.frame( i )._qtWidget().layout().setContentsMargins( 2, 2, 2, 2 )
			self.frame( i ).setChild( GafferUI.Image( "setMembershipDot.png" ) )

class __SetMembershipSection( Section ) :

	def __init__( self ) :

		Section.__init__( self, collapsed = True, label = "Set Membership" )

		with self._mainColumn() :
			self.__diffColumn = DiffColumn( self.__Inspector(), _SetMembershipDiff )

	def update( self, targets ) :

		self.__diffColumn.update( targets )

	class __Inspector( Inspector ) :

		def __init__( self, setName = None ) :

			self.__setName = setName

		def name( self ) :

			if self.__setName == "__lights" :
				return "Lights"
			elif self.__setName == "__cameras" :
				return "Cameras"
			else :
				return self.__setName or ""

		def inspectsAttributes( self ) :

			# strictly speaking we're not actually inspecting attributes,
			# but we can support ignoreInheritance arguments in __call__,
			# which is what we're really being asked about.
			return True

		def __call__( self, target, ignoreInheritance = False ) :

			if target.path is None :
				return None

			globals = target.scene["globals"].getValue()
			sets = globals.get( "gaffer:sets", {} )
			set = sets.get( self.__setName )
			if set is None :
				return None

			m = set.value.match( target.path )
			if m & GafferScene.Filter.Result.ExactMatch :
				return True

			if (not ignoreInheritance) and (m & GafferScene.Filter.Result.AncestorMatch) :
				return True

			return None

		def children( self, target ) :

			if not target.path :
				return []

			sets = target.scene["globals"].getValue().get( "gaffer:sets", {} )
			return [ self.__class__( setName ) for setName in sorted( sets.keys() ) ]

SceneInspector.registerSection( __SetMembershipSection, tab = "Selection" )

##########################################################################
# Global Options and Attributes section
##########################################################################

class __GlobalsSection( Section ) :

	def __init__( self, prefix, label ) :

		Section.__init__( self, collapsed = True, label = label )

		with self._mainColumn() :
			self.__diffColumn = DiffColumn( self.__Inspector( prefix ) )

	def update( self, targets ) :

		self.__diffColumn.update( targets )

	class __Inspector( Inspector ) :

		def __init__( self, prefix, key = None ) :

			self.__prefix = prefix
			self.__key = key

		def name( self ) :

			return self.__key[len(self.__prefix):] if self.__key else ""

		def __call__( self, target ) :

			## \todo Investigate caching the globals on the target.
			globals = target.scene["globals"].getValue()
			return globals.get( self.__key )

		def children( self, target ) :

			globals = target.scene["globals"].getValue()
			keys = [ k for k in globals.keys() if k.startswith( self.__prefix ) ]

			return [ self.__class__( self.__prefix, key ) for key in keys ]

SceneInspector.registerSection( lambda : __GlobalsSection( "option:", "Options" ), tab = "Globals" )
SceneInspector.registerSection( lambda : __GlobalsSection( "attribute:", "Attributes" ), tab = "Globals" )

##########################################################################
# Outputs section
##########################################################################

class _OutputRow( Row ) :

	def __init__( self, name, **kw ) :

		Row.__init__( self, **kw )

		with self.listContainer() :
			with GafferUI.ListContainer() :

				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal ) :
					collapseButton = GafferUI.Button( image = "collapsibleArrowRight.png", hasFrame=False )
					collapseButton.__clickedConnection = collapseButton.clickedSignal().connect( Gaffer.WeakMethod( self.__collapseButtonClicked ) )
					self.__label = TextDiff()
					GafferUI.Spacer( IECore.V2i( 1 ), parenting = { "expand" : True } )

				self.__diffColumn = DiffColumn( self.__Inspector( name ) )
				self.__diffColumn.setVisible( False )

		self.__name = name

	def update( self, targets ) :

		outputs = [ target.scene["globals"].getValue().get( self.__name ) for target in targets ]
		self.__label.update( [ self.__name[7:] if output else None for output in outputs ] )
		self.__diffColumn.update( targets )

	def __collapseButtonClicked( self, button ) :

		visible = not self.__diffColumn.getVisible()
		self.__diffColumn.setVisible( visible )
		button.setImage( "collapsibleArrowDown.png" if visible else "collapsibleArrowRight.png" )

	class __Inspector( Inspector ) :

		def __init__( self, outputName, parameterName = None ) :

			self.__outputName = outputName
			self.__parameterName = parameterName

		def name( self ) :

			return self.__parameterName or ""

		def __call__( self, target ) :

			output = target.scene["globals"].getValue().get( self.__outputName )
			if output is None :
				return None

			if self.__parameterName == "fileName" :
				return output.getName()
			elif self.__parameterName == "type" :
				return output.getType()
			elif self.__parameterName == "data" :
				return output.getData()
			else :
				return output.parameters().get( self.__parameterName )

		def children( self, target ) :

			output = target.scene["globals"].getValue().get( self.__outputName )
			if output is None :
				return []

			return [ self.__class__( self.__outputName, p ) for p in output.parameters().keys() + [ "fileName", "type", "data" ] ]

class __OutputsSection( Section ) :

	def __init__( self ) :

		Section.__init__( self, collapsed = True, label = "Outputs" )

		self.__rows = {} # mapping from output name to row

	def update( self, targets ) :

		outputNames = set()
		for target in targets :
			g = target.scene["globals"].getValue()
			outputNames.update( [ k for k in g.keys() if k.startswith( "output:" ) ] )

		rows = []
		outputNames = sorted( outputNames )
		for outputName in outputNames :

			row = self.__rows.get( outputName )
			if row is None :
				row = _OutputRow( outputName )
				self.__rows[outputName] = row

			row.update( targets )
			row.setAlternate( len( rows ) % 2 )
			rows.append( row )

		self._mainColumn()[:] = rows

SceneInspector.registerSection( __OutputsSection, tab = "Globals" )

##########################################################################
# Sets section
##########################################################################

class _SetDiff( Diff ) :

	def __init__( self, **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		Diff.__init__( self, self.__row, **kw )

		self.__connections = []
		with self.__row :
			for i, name in enumerate( [ "gafferDiffA", "gafferDiffCommon", "gafferDiffB" ] ) :
				with GafferUI.Frame( borderWidth = 5 ) as frame :

					frame._qtWidget().setObjectName( name )
					frame._qtWidget().setProperty( "gafferRounded", True )

					self.__connections.extend( [
						frame.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) ),
						frame.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ) ),
						frame.enterSignal().connect( lambda widget : widget.setHighlighted( True ) ),
						frame.leaveSignal().connect( lambda widget : widget.setHighlighted( False ) ),
						frame.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) ),
						frame.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) ),
					] )

					GafferUI.Label( "" )

	def update( self, values ) :

		paths = [ v.value.paths() if v is not None else [] for v in values ]
		if len( paths ) == 1 :
			self.__updateField( 0, [] )
			self.__updateField( 1, paths[0] )
			self.__updateField( 2, [] )
		else :
			paths = [ set( p ) for p in paths ]
			aOnly = paths[0] - paths[1]
			bOnly = paths[1] - paths[0]
			intersection = paths[0] & paths[1]
			self.__updateField( 0, paths[0] - paths[1], "-" )
			self.__updateField( 1, paths[0] & paths[1], "" )
			self.__updateField( 2, paths[1] - paths[0], " +" )

		self.__updateCorners()

	def __updateField( self, i, paths, prefix = "" ) :

		self.__row[i].paths = paths

		if not len( paths ) :
			self.__row[i].setVisible( False )
			return

		self.__row[i].getChild().setText( prefix + str( len( paths ) ) )
		self.__row[i].setVisible( True )

	def __updateCorners( self ) :

		## \todo It feels like it might be nice to have a Container that
		# did this automatically. Perhaps a ButtonRow or something like that?
		flatLeft = False
		flatRight = False
		for i in range( 0, len( self.__row ) ) :
			widgetLeft = self.__row[i]
			widgetRight = self.__row[-1-i]
			if widgetLeft.getVisible() :
				widgetLeft._qtWidget().setProperty( "gafferFlatLeft", flatLeft )
				flatLeft = True
			if widgetRight.getVisible() :
				widgetRight._qtWidget().setProperty( "gafferFlatRight", flatRight )
				flatRight = True

	def __buttonPress( self, widget, event ) :

		return event.buttons == event.Buttons.Left

	def __buttonRelease( self, widget, event ) :

		if event.buttons != event.Buttons.None or event.button != event.Buttons.Left :
			return False

		section = self.ancestor( _SetsSection )
		editor = section.ancestor( SceneInspector )

		context = editor.getContext()
		context["ui:scene:selectedPaths"] = IECore.StringVectorData( widget.paths )

		return True

	def __dragBegin( self, widget, event ) :

		if event.buttons != event.Buttons.Left :
			return None

		GafferUI.Pointer.setCurrent( "objects" )
		return IECore.StringVectorData( widget.paths )

	def __dragEnd( self, widget, event ) :

		GafferUI.Pointer.setCurrent( None )

class _SetsSection( Section ) :

	def __init__( self ) :

		Section.__init__( self, collapsed = True, label = "Sets" )

		with self._mainColumn() :
			self.__diffColumn = DiffColumn( self.__Inspector(), _SetDiff )

	def update( self, targets ) :

		self.__diffColumn.update( targets )

	class __Inspector( Inspector ) :

		def __init__( self, setName = None ) :

			self.__setName = setName

		def name( self ) :

			if self.__setName == "__lights" :
				return "Lights"
			elif self.__setName == "__cameras" :
				return "Cameras"
			else :
				return self.__setName or ""

		def __call__( self, target ) :

			globals = target.scene["globals"].getValue()
			sets = globals.get( "gaffer:sets", {} )
			return sets.get( self.__setName )

		def children( self, target ) :

			sets = target.scene["globals"].getValue().get( "gaffer:sets", {} )
			return [ self.__class__( setName ) for setName in sorted( sets.keys() ) ]

SceneInspector.SetsSection = _SetsSection

SceneInspector.registerSection( _SetsSection, tab = "Globals" )
