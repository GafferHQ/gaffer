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

import enum
import math
import difflib
import html
import itertools
import collections
import functools

import imath

import IECore
import IECoreScene
import IECoreVDB

import Gaffer
import GafferScene
import GafferUI
import GafferSceneUI

class SceneInspector( GafferSceneUI.SceneEditor ) :

	## Simple class to specify the target of an inspection,
	# and provide cached queries for that target.
	class Target( object ) :

		def __init__( self, scene, path ) :

			self.__scene = scene
			self.__path = path
			self.__bound = None
			self.__transform = None
			self.__fullTransform = None
			self.__attributes = None
			self.__fullAttributes = None
			self.__object = None
			self.__globals = None
			self.__setNames = None
			self.__sets = {}

		@property
		def scene( self ) :

			return self.__scene

		@property
		def path( self ) :

			return self.__path

		def bound( self ) :

			if self.__bound is None :
				self.__bound = self.scene.bound( self.path )

			return self.__bound

		def transform( self ) :

			if self.__transform is None :
				self.__transform = self.scene.transform( self.path )

			return self.__transform

		def fullTransform( self ) :

			if self.__fullTransform is None :
				self.__fullTransform = self.scene.fullTransform( self.path )

			return self.__fullTransform

		def attributes( self ) :

			if self.__attributes is None :
				self.__attributes = self.scene.attributes( self.path )

			return self.__attributes

		def fullAttributes( self ) :

			if self.__fullAttributes is None :
				self.__fullAttributes = self.scene.fullAttributes( self.path )

			return self.__fullAttributes

		def object( self ) :

			if self.__object is None :
				self.__object = self.scene.object( self.path )

			return self.__object

		def globals( self ) :

			if self.__globals is None :
				self.__globals = self.scene["globals"].getValue()

			return self.__globals

		def setNames( self ) :

			if self.__setNames is None :
				self.__setNames = self.scene["setNames"].getValue()

			return self.__setNames

		def set( self, setName ) :

			if setName not in self.__sets :
				self.__sets[setName] = self.scene.set( setName )

			return self.__sets[setName]

	class Settings( GafferSceneUI.SceneEditor.Settings ) :

		def __init__( self ) :

			GafferSceneUI.SceneEditor.Settings.__init__( self, numInputs = 2 )

	IECore.registerRunTimeTyped( Settings, typeName = "GafferSceneUI::SceneInspector::Settings" )

	## A list of Section instances may be passed to create a custom inspector,
	# otherwise all registered Sections will be used.
	def __init__( self, scriptNode, sections = None, **kw ) :

		mainColumn = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 8 )

		GafferSceneUI.SceneEditor.__init__( self, mainColumn, scriptNode, **kw )

		self.__sections = []

		if sections is not None :

			for section in sections :
				mainColumn.append( section )
				self.__sections.append( section )

			mainColumn.append( GafferUI.Spacer( imath.V2i( 0 ) ), expand = True )

		else :

			columns = {}
			with mainColumn :
				columns[None] = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 8, borderWidth = 5 )
				tabbedContainer = GafferUI.TabbedContainer()

			for registration in self.__sectionRegistrations :
				section = registration.section()
				column = columns.get( registration.tab )
				if column is None :
					with tabbedContainer :
						with GafferUI.ScrolledContainer( horizontalMode = GafferUI.ScrollMode.Automatic, parenting = { "label" : registration.tab } ) :
							column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 4, spacing = 8 )
							columns[registration.tab] = column
				column.append( section )
				self.__sections.append( section )

			for tab, column in columns.items() :
				if tab is not None :
					column.append( GafferUI.Spacer( imath.V2i( 0 ) ), expand = True )

		self.__targetPaths = None
		self._updateFromSet()

	## May be used to "pin" target paths into the editor, rather than
	# having it automatically follow the scene selection. A value of
	# None causes selection to be followed again.
	def setTargetPaths( self, paths ) :

		if paths == self.__targetPaths :
			return

		assert( paths is None or len( paths ) == 1 or len( paths ) == 2 )

		self.__targetPaths = paths
		self.__updateLazily()

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

	def _updateFromSettings( self, plug ) :

		if plug.isSame( self.settings()["in"] ) :
			self.__updateLazily()

	def _updateFromContext( self, modifiedItems ) :

		for item in modifiedItems :
			if not item.startswith( "ui:" ) or ( GafferSceneUI.ContextAlgo.affectsSelectedPaths( item ) and self.__targetPaths is None ) :
				self.__updateLazily()
				break

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __updateLazily( self ) :

		self.__update()

	def __update( self ) :

		# The SceneInspector's internal context is not necessarily bound at this point, which can lead to errors
		# if nodes in the graph are expecting special context variables, so we make sure it is:
		with self.context():

			scenes = [ s.getInput() for s in self.settings()["in"] if s.getInput() is not None ]
			assert( len( scenes ) <= 2 )

			paths = [ None ]
			if self.__targetPaths is not None :
				paths = self.__targetPaths
			else :
				lastSelectedPath = GafferSceneUI.ContextAlgo.getLastSelectedPath( self.context() )
				if lastSelectedPath :
					paths = [ lastSelectedPath ]
					selectedPaths = GafferSceneUI.ContextAlgo.getSelectedPaths( self.context() ).paths()
					if len( selectedPaths ) > 1 :
						paths.insert( 0, next( p for p in selectedPaths if p != lastSelectedPath ) )

			if len( scenes ) > 1 :
				paths = [ paths[-1] ]

			targets = []
			for scene in scenes :
				for path in paths :
					if path is not None and not scene.exists( path ) :
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

			for section in self.__sections :
				section.update( targets )

			return False # remove idle callback

GafferUI.Editor.registerType( "SceneInspector", SceneInspector )

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

# Base class for showing side-by-side diffs. It houses two widgets,
# one for each value, and in update() it displays one or both of them,
# with background colours appropriate to the relationship between the two.
class SideBySideDiff( Diff ) :

	Background = enum.Enum( "Background", [ "A", "B", "AB", "Other" ] )

	def __init__( self, **kw ) :

		self.__grid = GafferUI.GridContainer()
		Diff.__init__( self, self.__grid, **kw )

		with self.__grid :
			for i in range( 0, 2 ) :
				frame = GafferUI.Frame(
					borderWidth = 4,
					borderStyle = GafferUI.Frame.BorderStyle.None_,
					parenting = { "index" : ( 0, i ) }
				)

	def setValueWidget( self, index, widget ) :

		self.__frame( index ).setChild( widget )

	def getValueWidget( self, index ) :

		return self.__frame( index ).getChild()

	def setCornerWidget( self, index, widget ) :

		self.__grid.addChild(
			widget, index = ( 1, index ),
			alignment = ( GafferUI.HorizontalAlignment.Left, GafferUI.VerticalAlignment.Top )
		)

	def getCornerWidget( self, index ) :

		return self.__grid[1,index]

	## Updates the UI to reflect the relationship between the values.
	# If they are equal or if there is only one, then only the first
	# value is shown, with a default background colour. If there are
	# two and they differ, then both values are shown, with red and
	# green backgrounds respectively.
	#
	# The visibilities argument can be passed a sequence containing
	# a boolean per value to override the default visibility. This
	# is used by the history and inheritance sections. Likewise, the
	# backgrounds argument can be passed to override the default
	# background styles.
	#
	# Derived classes are expected to override this method to additionally
	# edit the value widgets to display the actual values.
	def update( self, values, visibilities = None, backgrounds = None ) :

		assert( len( values ) <= 2 )

		# have to compare types before comparing values to avoid exceptions from
		# poor VectorTypedData.__cmp__ implementation.
		different = len( values ) > 1 and ( type( values[0] ) != type( values[1] ) or values[0] != values[1] )

		if visibilities is None :
			visibilities = [
				len( values ) > 0 and values[0] is not None,
				len( values ) > 1 and values[1] is not None and different
			]

		if backgrounds is None :
			backgrounds = [
				self.Background.A if different else self.Background.AB,
				self.Background.B if different else self.Background.AB,
			]

		for i in range( 0, 2 ) :

			frame = self.__frame( i )
			frame.setVisible( visibilities[i] )
			cornerWidget = self.getCornerWidget( i )
			if cornerWidget is not None :
				cornerWidget.setVisible( visibilities[i] )

			if not visibilities[i] :
				continue

			repolish = False
			if backgrounds[i].name != frame._qtWidget().property( "gafferDiff" ) :
				frame._qtWidget().setProperty( "gafferDiff", backgrounds[i].name )
				repolish = True

			if i == 0 :
				if frame._qtWidget().property( "gafferAdjoinedBottom" ) != visibilities[1] :
					frame._qtWidget().setProperty( "gafferAdjoinedBottom", visibilities[1] )
					repolish = True
			elif i == 1 :
				if frame._qtWidget().property( "gafferAdjoinedTop" ) != visibilities[0] :
					frame._qtWidget().setProperty( "gafferAdjoinedTop", visibilities[0] )
					repolish = True

			if repolish :
				frame._repolish()


	def __frame( self, index ) :

		return self.__grid[0,index]

class TextDiff( SideBySideDiff ) :

	def __init__( self, highlightDiffs=True, **kw ) :

		SideBySideDiff.__init__( self, **kw )

		for i in range( 0, 2 ) :
			label = GafferUI.Label()
			label._qtWidget().setSizePolicy( QtWidgets.QSizePolicy( QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed ) )
			label.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
			label.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
			label.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )
			self.setValueWidget( i, label )

		self.__highlightDiffs = highlightDiffs

	def update( self, values, **kw ) :

		SideBySideDiff.update( self, values, **kw )

		self.__values = values

		formattedValues = self._formatValues( values )
		for i, value in enumerate( formattedValues ) :
			self.getValueWidget( i ).setText( self.__htmlHeader + value + self.__htmlFooter )

	def _formatValues( self, values ) :

		if len( values ) == 0 :
			return []
		elif len( values ) == 2 and type( values[0] ) != type( values[1] ) :
			# different types - format each separately
			return self._formatValues( [ values[0] ] ) + self._formatValues( [ values[1] ] )
		elif isinstance( values[0], IECore.Data ) and hasattr( values[0], "value" ) :
			return self._formatValues( [ v.value for v in values ] )
		elif isinstance( values[0], ( imath.V3f, imath.V3i, imath.V2f, imath.V2i, imath.Color4f ) ) :
			return self.__formatVectors( values )
		elif isinstance( values[0], ( imath.M44f, imath.M44d ) ) :
			return self.__formatMatrices( values )
		elif isinstance( values[0], ( imath.Box3f, imath.Box3d, imath.Box3i, imath.Box2f, imath.Box2d, imath.Box2i ) ) :
			return self.__formatBoxes( values )
		elif isinstance( values[0], ( IECoreScene.Shader, IECoreScene.ShaderNetwork ) ) :
			return self.__formatShaders( values )
		elif isinstance( values[0], ( float, int ) ) :
			return self.__formatNumbers( values )
		elif isinstance( values[0], str ) :
			return self.__formatStrings( [ str( v ) for v in values ] )
		else :
			return [ html.escape( str( v ) ) for v in values ]

	def __formatVectors( self, vectors ) :

		arrays = [ [ v ] for v in vectors ]
		return self.__formatNumberArrays( arrays )

	def __formatMatrices( self, matrices ) :

		arrays = []
		for matrix in matrices :
			array = []
			for i in range( 0, len( matrix ) ) :
				array.append( [ matrix[i][j] for j in range( 0, len( matrix[i] ) ) ] )
			arrays.append( array )

		return self.__formatNumberArrays( arrays )

	def __formatBoxes( self, boxes ) :

		if any( b.isEmpty() for b in boxes ) :
			# We can't diff empty boxes against non-empty, because they're formatted differently.
			return [ self.__formatBoxes( [ b ] )[0] if not b.isEmpty() else "Empty" for b in boxes ]

		arrays = []
		for box in boxes :
			arrays.append( [ box.min(), box.max() ] )

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
		values = list( zip( *( [ iter( formattedRows ) ] * len( values[0] ) ) ) )

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

			shader = value.outputShader() if isinstance( value, IECoreScene.ShaderNetwork ) else value
			if not shader:
				formattedValues.append( "Missing output shader" )
				continue
			shaderName = shader.name
			nodeName = shader.blindData().get( "label", shader.blindData().get( "gaffer:nodeName", None ) )

			formattedValue = "<table cellspacing=2><tr>"
			if nodeName is not None :
				nodeColor = shader.blindData().get( "gaffer:nodeColor", None )
				if nodeColor is not None :
					nodeColor = GafferUI.Widget._qtColor( nodeColor.value ).name()
				else :
					nodeColor = "#000000"
				formattedValue += "<td bgcolor=%s>%s</td>" % ( nodeColor, html.escape( nodeName.value ) )
				formattedValue += "<td>(" + html.escape( shaderName ) + ")</td>"
			else :
				formattedValue += "<td>" + html.escape( shaderName ) + "</td>"

			formattedValue += "</tr></table>"

			formattedValues.append( formattedValue )

		return formattedValues

	def __formatStrings( self, strings ) :

		if len( strings ) == 1 or strings[0] == strings[1] or not self.__highlightDiffs :
			return [ html.escape( s ) for s in strings ]

		a = strings[0]
		b = strings[1]

		aFormatted = ""
		bFormatted = ""
		for op, a1, a2, b1, b2 in difflib.SequenceMatcher( None, a, b ).get_opcodes() :

			if op == "equal" :
				aFormatted += html.escape( a[a1:a2] )
				bFormatted += html.escape( b[b1:b2] )
			elif op == "replace" :
				aFormatted += '<span class="diffA">' + html.escape( a[a1:a2] ) + "</span>"
				bFormatted += '<span class="diffB">' + html.escape( b[b1:b2] ) + "</span>"
			elif op == "delete" :
				aFormatted += '<span class="diffA">' + html.escape( a[a1:a2] ) + "</span>"
			elif op == "insert" :
				bFormatted += '<span class="diffB">' + html.escape( b[b1:b2] ) + "</span>"

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
		d = next( ( i for i in range( 0, len( values[0] ) ) if values[0][i] != values[1][i] ), -1 )
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
		return self.__values[0] if widget is self.getValueWidget( 0 ) else self.__values[1]

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

		self.__frame = GafferUI.Frame( borderWidth = borderWidth, borderStyle = GafferUI.Frame.BorderStyle.None_ )

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
		self.__frame._qtWidget().setProperty( "gafferAlternate", bool(alternate) )
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
	# can meaningfully be tracked back up through the
	# node graph.
	def supportsHistory( self ) :

		return True

	## Should return True if the Inspector's results
	# may be inherited from parent locations - this will
	# enable inheritance queries for the inspector.
	def supportsInheritance( self ) :

		return False

	## Must be implemented to inspect the target and return
	# a value to be displayed. When supportsInheritance()==True,
	# this method must accept an ignoreInheritance keyword
	# argument (defaulting to False).
	def __call__( self, target, **kw ) :

		raise NotImplementedError

	## May be implemented to return a list of "child" inspectors -
	# this is used by the DiffColumn to obtain an inspector per row.
	def children( self, target ) :

		return []

	def _useBackgroundThread( self ) :

		return False

##########################################################################
# DiffRow
##########################################################################

## A row which displays a diff from values generated by an Inspector.
## \todo This would probably be more accurately described as an InspectorRow
class DiffRow( Row ) :

	def __init__( self, inspector, diffCreator = TextDiff, alternate = False, **kw ) :

		assert( isinstance( inspector, Inspector ) )

		Row.__init__( self, alternate=alternate, **kw )

		with self.listContainer() :

			label = GafferUI.Label(
				inspector.name(),
				horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right,
				verticalAlignment = GafferUI.Label.VerticalAlignment.Top,
				toolTip = inspector.name()
			)
			label._qtWidget().setFixedWidth( 150 )

			diff = diffCreator()

			if inspector.supportsInheritance() and isinstance( diff, SideBySideDiff ) :

				diff.setCornerWidget( 0, GafferUI.Label( "" ) )
				diff.setCornerWidget( 1, GafferUI.Label( "" ) )

			diffWidgets = [ diff.getValueWidget( 0 ), diff.getValueWidget( 1 ) ] if isinstance( diff, SideBySideDiff ) else [ diff ]
			for diffWidget in diffWidgets :
				diffWidget.enterSignal().connect( Gaffer.WeakMethod( self.__enter ), scoped = False )
				diffWidget.leaveSignal().connect( Gaffer.WeakMethod( self.__leave ), scoped = False )
				diffWidget.contextMenuSignal().connect( Gaffer.WeakMethod( self.__contextMenu ), scoped = False )

			if inspector._useBackgroundThread() :
				GafferUI.BusyWidget( size = 22, busy = False )

			GafferUI.Spacer( imath.V2i( 1, 20 ), parenting = { "expand" : True } )

			GafferUI.MenuButton(
				image = "gear.png",
				hasFrame = False,
				menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) )
			)

			label.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
			label.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
			label.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )

		self.__inspector = inspector
		self.__diffCreator = diffCreator

	def inspector( self ) :

		return self.__inspector

	def update( self, targets ) :

		self.__targets = targets
		if self.__inspector._useBackgroundThread() :
			self.__lazyBackgroundContext = Gaffer.Context( Gaffer.Context.current() )
			self.__lazyBackgroundUpdate()
		else :
			self.__updateFromValues( *self.__valuesFromTargets() )

	@GafferUI.LazyMethod()
	def __lazyBackgroundUpdate( self ) :

		with self.__lazyBackgroundContext :
			self.__backgroundUpdate()

	@GafferUI.BackgroundMethod()
	def __backgroundUpdate( self ) :

		return self.__valuesFromTargets()

	@__backgroundUpdate.preCall
	def __backgroundUpdatePreCall( self ) :

		self.__diff().setVisible( False )
		self.__busyWidget().setBusy( True )
		self.__menuButton().setEnabled( False )

	@__backgroundUpdate.postCall
	def __backgroundUpdatePostCall( self, backgroundResult ) :

		if isinstance( backgroundResult, IECore.Cancelled ) :
			# Cancellation. This could be due to any of the
			# following :
			#
			# - This widget being hidden.
			# - A graph edit that will affect the target and will have
			#   triggered a call to update().
			# - A graph edit that won't trigger a call to update().
			#
			# LazyMethod takes care of all this for us. If we're hidden,
			# it waits till we're visible. If `update()` has already
			# called `__lazyBackgroundUpdate()`, our call will just replace the
			# pending call.
			self.__lazyBackgroundUpdate()
		elif isinstance( backgroundResult, Exception ) :
			# Computation error. For now we leave it to the GraphEditor
			# to display this.
			pass
		else :
			# Success.
			self.__updateFromValues( *backgroundResult )
			self.__diff().setVisible( True )
			self.__menuButton().setEnabled( True )

		self.__busyWidget().setBusy( False )

	@__backgroundUpdate.plug
	def __script( self ) :

		return self.__targets[0].scene

	def __valuesFromTargets( self ) :

		values = [ self.__inspector( target ) for target in self.__targets ]
		if self.__inspector.supportsInheritance() and isinstance( self.__diff(), SideBySideDiff ) :
			localValues = [ self.__inspector( target, ignoreInheritance=True ) for target in self.__targets ]
		else :
			localValues = None

		return values, localValues

	def __updateFromValues( self, values, localValues ) :

		self.__values = values
		self.__diff().update( self.__values )
		if localValues is not None :
			for i, value in enumerate( localValues ) :
				self.__diff().getCornerWidget( i ).setText( "<sup>Inherited</sup>" if value is None else "" )

	def __label( self ) :

		return self.listContainer()[0]

	def __diff( self ) :

		return self.listContainer()[1]

	def __busyWidget( self ) :

		if self.__inspector._useBackgroundThread() :
			return self.listContainer()[2]
		return None

	def __menuButton( self ) :

		return self.listContainer()[-1]

	def __enter( self, widget ) :

		if self.__inspector.supportsInheritance() or self.__inspector.supportsHistory() :
			GafferUI.Pointer.setCurrent( "contextMenu" )

	def __leave( self, widget ) :

		GafferUI.Pointer.setCurrent( None )

	def __contextMenu( self, widget ) :

		GafferUI.Pointer.setCurrent( None )
		self.__menu = GafferUI.Menu( functools.partial( Gaffer.WeakMethod( self.__menuDefinition ), widget ) )
		self.__menu.popup()

	def __menuDefinition( self, widget = None ) :

		diff = self.__diff()
		if isinstance( diff, SideBySideDiff ) and widget is not None :
			# For SideBySideDiffs, we know which target the user has clicked on
			# and only present menu items for that target.
			targets = [ self.__targets[ 0 if widget is diff.getValueWidget( 0 ) else 1 ] ]
		else :
			# But for other Diff types we don't know, and so present menu items
			# for any target which has a value. The same applies when the user
			# has raised the menu via the tool button rather than a right click.
			targets = [ t for i, t in enumerate( self.__targets ) if self.__values[i] is not None ]

		m = IECore.MenuDefinition()

		targetsAreShaders = []

		for i, target in enumerate( targets ) :

			attribute = self.__inspector( target )
			targetsAreShaders.append( isinstance( attribute, IECoreScene.ShaderNetwork ) and len( attribute ) )

			if len( targets ) == 2 :
				labelSuffix = "/For " + ( "A", "B" )[i]
			else :
				labelSuffix = ""

			if self.__inspector.supportsHistory() :

				m.append(
					"/Show History" + labelSuffix,
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__showHistory ), target ),
					}
				)

			if self.__inspector.supportsInheritance() :

				m.append(
					"/Show Inheritance" + labelSuffix,
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__showInheritance ), target ),
					}
				)

			if targetsAreShaders[i] :
				m.append(
					"/Show Shader" + labelSuffix,
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__showShader ), [ target ] )
					}
				)

		if len( targetsAreShaders ) == 2 and all( targetsAreShaders ) :
			m.append(
				"/Show Shader/Compare A and B",
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__showShader ), targets )
				}
			)

		return m

	def __showInheritance( self, target ) :

		w = _SectionWindow(
			self.__label().getText(),
			_InheritanceSection( self.__inspector, self.__diffCreator ),
			[ target ]
		)

		self.ancestor( GafferUI.Window ).addChildWindow( w, removeOnClose = True )
		w.setVisible( True )

	def __showHistory( self, target ) :

		w = _SectionWindow(
			self.__label().getText(),
			_HistorySection( self.__inspector, self.__diffCreator ),
			[ target ]
		)

		self.ancestor( GafferUI.Window ).addChildWindow( w, removeOnClose = True )
		w.setVisible( True )

	def __showShader( self, targets ) :

		w = _SectionWindow(
			self.__label().getText(),
			_ShaderSection( self.__inspector, self.__diffCreator ),
			targets
		)

		self.ancestor( GafferUI.Window ).addChildWindow( w, removeOnClose = True )
		w.setVisible( True )

	def __buttonPress( self, widget, event ) :

		return event.buttons == event.Buttons.Left

	def __dragBegin( self, widget, event ) :

		if event.buttons != event.Buttons.Left :
			return None

		GafferUI.Pointer.setCurrent( "values" )
		return self.__inspector.name() if self.__inspector else ""

	def __dragEnd( self, widget, event ) :

		GafferUI.Pointer.setCurrent( None )

##########################################################################
# DiffColumn
##########################################################################

## Class for displaying a column of DiffRows.
## \todo This would probably be more accurately described as an InspectorColumn
class DiffColumn( GafferUI.Widget ) :

	def __init__( self, inspector, diffCreator = TextDiff, label = None, filterable = False, **kw ) :

		outerColumn = GafferUI.ListContainer()
		GafferUI.Widget.__init__( self, outerColumn, **kw )

		assert( isinstance( inspector, Inspector ) )

		self.__inspector = inspector
		self.__rows = {} # mapping from row name to row
		self.__diffCreator = diffCreator

		with outerColumn :
			with GafferUI.Frame( borderWidth = 4, borderStyle = GafferUI.Frame.BorderStyle.None_ ) as self.__header :
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
					if label is not None :
						l = GafferUI.Label(
							"<b>" + label + "</b>",
							horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right,
						)
						l._qtWidget().setFixedWidth( 150 )
					self.__filterWidget = None
					if filterable :
						self.__filterWidget = GafferUI.TextWidget()
						self.__filterWidget.setPlaceholderText( "Filter..." )
						self.__filterWidget.textChangedSignal().connect(
							Gaffer.WeakMethod( self.__filterTextChanged ), scoped = False
						)

			self.__rowContainer = GafferUI.ListContainer()

	@GafferUI.LazyMethod()
	def update( self, targets ) :

		# this doesn't always get called by SceneInspector.__update(), so we grab the
		# context from the ancestor NodeSetEditor if it exists, and make it current:
		nodeSetEditor = self.ancestor( GafferUI.NodeSetEditor )
		context = nodeSetEditor.context() if nodeSetEditor else Gaffer.Context.current()

		with context:

			inspectors = {}
			for target in targets :
				inspectors.update( { i.name() : i for i in self.__inspector.children( target ) } )

			# mark all rows as invalid
			for row in self.__rowContainer :
				row.__valid = False

			# iterate over the fields we want to display,
			# creating/updating the rows that are to be valid.
			for rowName in inspectors.keys() :

				row = self.__rows.get( rowName )
				if row is None :
					row = DiffRow( inspectors[rowName], self.__diffCreator )
					self.__rows[rowName] = row

				row.update( targets )
				row.__valid = True

			# update the rowContainer with _all_ rows (both
			# valid and invalid) in the correct order. this
			# is a no-op except when adding new rows. it is
			# much quicker to hide invalid rows than it is
			# to reparent widgets so that the container only
			# contains the valid ones.
			self.__rowContainer[:] = sorted( self.__rows.values(), key = lambda r : r.inspector().name() )

			# show only the currently valid ones.
			self.__updateRowVisibility()

	def __updateRowVisibility( self ) :

		patterns = self.__filterWidget.getText() if self.__filterWidget is not None else ""
		if not patterns :
			patterns = "*"
		else :
			patterns = [ p.lower() for p in patterns.split() ]
			patterns = " ".join( "*" + p + "*" if "*" not in p else p for p in patterns )

		numValidRows = 0
		numVisibleRows = 0
		for row in self.__rowContainer :

			visible = False
			if row.__valid :
				numValidRows += 1
				if IECore.StringAlgo.matchMultiple( row.inspector().name().lower(), patterns ) :
					visible = True

			row.setVisible( visible )
			if visible :
				row.setAlternate( numVisibleRows % 2 )
				numVisibleRows += 1

		self.__header.setVisible( numValidRows )

	def __filterTextChanged( self, filterWidget ) :

		self.__updateRowVisibility()

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

	## Should be implemented by derived classes to update the
	# UI to reflect the state of the targets. Implementations should
	# first call the base class implementation.
	def update( self, targets ) :

		self.setEnabled( bool( targets ) )

		if self.__collapsible is None :
			return

		label = self.__collapsible.getCornerWidget()
		summary = self._summary( targets )
		if summary is None and label is None :
			return

		if label is None :
			label = GafferUI.Label()
			label._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed )
			self.__collapsible.setCornerWidget( label, True )

		if summary :
			summary = "<small>" + "&nbsp;( " + summary + " ) </small>"

		label.setText( summary )

	## May be implemented by derived classes to provide
	# a short summary of the contents.
	def _summary( self, targets ) :

		return None

	def _mainColumn( self ) :

		return self.__mainColumn

## Base class for sections which display information about
#  scene locations.
class LocationSection( Section ) :

	def __init__( self, collapsed = False, label = None, **kw ) :

		Section.__init__( self, collapsed, label, **kw )

	def update( self, targets ) :

		Section.update( self, targets )

		self.setEnabled( bool( [ t.path for t in targets if t.path is not None ] ) )

##########################################################################
# Export classes for use in custom sections
##########################################################################

SceneInspector.Diff = Diff
SceneInspector.SideBySideDiff = SideBySideDiff
SceneInspector.TextDiff = TextDiff
SceneInspector.Row = Row
SceneInspector.Inspector = Inspector
SceneInspector.DiffRow = DiffRow
SceneInspector.DiffColumn = DiffColumn
SceneInspector.Section = Section
SceneInspector.LocationSection = LocationSection

##########################################################################
# Section window
##########################################################################

class _SectionWindow( GafferUI.Window ) :

	def __init__( self, label, section, targets ) :

		title = ' '.join( [ target.scene.node().getName() for target in targets ] ) + " : " + label

		GafferUI.Window.__init__( self, title, borderWidth = 4 )

		container = GafferUI.ScrolledContainer( horizontalMode = GafferUI.ScrolledContainer.ScrollMode.Never )

		with container :

			editor = SceneInspector( targets[0].scene.ancestor( Gaffer.ScriptNode ), sections = [ section ] )
			editor.setTargetPaths( [ target.path for target in targets ] )
			editor.setNodeSet( Gaffer.StandardSet( [ target.scene.node() for target in targets ] ) )

		self.setChild( container )

		## \todo Drive the size by the sized needed by the section. This is
		# tricky because sections resize lazily when they are first shown.
		self._qtWidget().resize( 400, 250 )

		editor.getNodeSet().memberRemovedSignal().connect( Gaffer.WeakMethod( self.__nodeSetMemberRemoved ), scoped = False )

	def __nodeSetMemberRemoved( self, set, node ) :

		self.parent().removeChild( self )

##########################################################################
# Inheritance section
##########################################################################

from Qt import QtWidgets

class _Rail( GafferUI.ListContainer ) :

	Type = enum.Enum( "Type", [ "Top", "Middle", "Gap", "Bottom", "Single" ] )

	def __init__( self, type, **kw ) :

		GafferUI.ListContainer.__init__( self, **kw )

		with self :

			if type != self.Type.Top and type != self.Type.Single :
				image = GafferUI.Image( "railLine.png" )
				## \todo Decide how we do this via the public API.
				# Perhaps by putting the image in a Sizer? Or by
				# adding stretch methods to the Image class?
				image._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred )
				image._qtWidget().setScaledContents( True )
			else :
				GafferUI.Spacer( imath.V2i( 1 ) )

			GafferUI.Image( "rail" + type.name + ".png" )

			if type != self.Type.Bottom and type != self.Type.Single :
				image = GafferUI.Image( "railLine.png" )
				image._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred )
				image._qtWidget().setScaledContents( True )
			else :
				GafferUI.Spacer( imath.V2i( 1 ) )

class _InheritanceSection( Section ) :

	def __init__( self, inspector, diffCreator = TextDiff, **kw ) :

		Section.__init__( self, collapsed = None, **kw )

		self.__inspector = inspector
		self.__diffCreator = diffCreator

	def update( self, targets ) :

		Section.update( self, targets )

		self.__target = targets[0]

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
						label.enterSignal().connect( lambda gadget : gadget.setHighlighted( True ), scoped = False )
						label.leaveSignal().connect( lambda gadget : gadget.setHighlighted( False ), scoped = False )
						label.buttonPressSignal().connect( Gaffer.WeakMethod( self.__labelButtonPress ), scoped = False )
					else :
						GafferUI.Label( "..." )

					GafferUI.Spacer( imath.V2i( 0 ), parenting = { "expand" : True } )

					if atEitherEnd or value is not None :
						diff = self.__diffCreator()
						diffKW = {}
						if prevDisplayedValue != fullValue and isinstance( diff, SideBySideDiff ) :
							diffKW["visibilities"] = [ False, True ]
						diff.update( ( prevDisplayedValue, fullValue ), **diffKW )

				prevDisplayedValue = fullValue

			prevValue = value

		self._mainColumn()[:] = rows

	def __labelButtonPress( self, label, event ) :

		script = self.__target.scene.ancestor( Gaffer.ScriptNode )
		GafferSceneUI.ContextAlgo.setSelectedPaths( script.context(), IECore.PathMatcher( [ label.getText() ] ) )


##########################################################################
# Shader section
##########################################################################

class _ShaderSection( LocationSection ) :

	class __NameAndTypeInspector( Inspector ) :

		Name, Type = range( 2 )

		def __init__( self, inspector, mode = None ) :

			self.__inspector = inspector
			self.__mode = mode

			Inspector.__init__( self )

		def name( self ) :

			if self.__mode == self.Name :
				return "Name"

			elif self.__mode == self.Type :
				return "Type"

		def children( self, target ) :

			if self.__mode is not None :
				return []

			result = [ self.__class__( self.__inspector, mode = self.Name ),
					   self.__class__( self.__inspector, mode = self.Type ) ]

			return result

		def __call__( self, target ) :

			network = self.__inspector( target )
			if not network or not isinstance( network, IECoreScene.ShaderNetwork ) :
				return None

			shader = network.outputShader()
			if not shader :
				return None

			if self.__mode == self.Name :
				return shader.name

			elif self.__mode == self.Type :
				return shader.type

	class __Inspector( Inspector ) :

		def __init__( self, inspector, parameterName = None ) :

			Inspector.__init__( self )

			self.__inspector = inspector
			self.__parameterName = parameterName

		def name( self ) :

			return self.__parameterName

		def __call__( self, target ) :

			parameters = self.__parameters( target )
			if parameters is None :
				return None

			return parameters.get( self.__parameterName )

		def children( self, target ) :

			parameters = self.__parameters( target )
			if parameters is None :
				return []

			return [ self.__class__( self.__inspector, parameterName = p ) for p in parameters.keys() if not p == '__handle' ]

		def __parameters( self, target ) :

			if target.path is None :
				return None

			network = self.__inspector( target )
			if not network :
				return None

			return network.outputShader().parameters

	def __init__( self, inspector, diffCreator = TextDiff, **kw ) :

		LocationSection.__init__( self, collapsed = None, **kw )

		self.__diffCreator = diffCreator

		with self._mainColumn() :

			self.__nameTypeDiffColumn = DiffColumn( self.__NameAndTypeInspector( inspector ), label = "Shader", filterable = False, diffCreator = self.__diffCreator )
			self.__diffColumn = DiffColumn( self.__Inspector( inspector ), label = "Parameters", filterable = True, diffCreator = self.__diffCreator )

	def update( self, targets ) :

		LocationSection.update( self, targets )

		self.__nameTypeDiffColumn.update( targets )
		self.__diffColumn.update( targets )

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

		Section.update( self, targets )

		self.__target = targets[0]

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
					GafferUI.NameLabel(
						history[i].target.scene.node(),
						formatter = lambda l : ".".join( x.getName() for x in l ),
						numComponents = self.__distance( history[i].target.scene.node().scriptNode(), history[i].target.scene.node() )
					)
					editButton = GafferUI.Button( image = "editOn.png", hasFrame = False )
					if not Gaffer.MetadataAlgo.readOnly( history[i].target.scene.node() ) :
						editButton.clickedSignal().connect(
							functools.partial( _HistorySection.__editClicked, node = history[i].target.scene.node() ),
							scoped = False
						)
					else :
						editButton.setEnabled( False )
				else :
					GafferUI.Label( "..." )

				GafferUI.Spacer( imath.V2i( 0 ), parenting = { "expand" : True } )

				values = [ history[i-1].value if i > 0 else None, history[i].value ]

				diff = self.__diffCreator()
				diffKW = {}
				if isinstance( diff, SideBySideDiff ) :
					if values[0] != values[1] :
						# We don't want to show both values, just the one
						# representative of the change at this point in the
						# history.
						diffKW["visibilities"] = [ False, True ] if values[1] is not None else [ True, False ]
				diff.update( values, **diffKW )

		self._mainColumn()[:] = rows

	def __sourceTarget( self, target ) :

		if isinstance( target.scene.node(), Gaffer.DependencyNode ) :

			sourceScene = target.scene.node().correspondingInput( target.scene )
			if sourceScene is None :
				return None

			sourceScene = sourceScene.source()
			if sourceScene.node() == target.scene.node() :
				return None

			if not sourceScene.exists( target.path ) :
				return None

			return SceneInspector.Target( sourceScene, target.path )

		return None

	@staticmethod
	def __editClicked( button, node ) :

		GafferUI.NodeEditor.acquire( node, floating = True )
		return True

	@staticmethod
	## \todo This might make sense as part of a future GraphComponentAlgo.
	def __distance( ancestor, descendant ) :

		result = 0
		while descendant is not None and descendant != ancestor :
			result += 1
			descendant = descendant.parent()

		return result

SceneInspector.HistorySection = _HistorySection ## REMOVE ME!!

##########################################################################
# Node section
##########################################################################

class __NodeSection( Section ) :

	def __init__( self ) :

		Section.__init__( self, collapsed = None )

		with self._mainColumn() :
			with Row().listContainer() :

				label = GafferUI.Label(
					"Node",
					horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right,
				)
				label._qtWidget().setFixedWidth( 150 )

				self.__diff = SideBySideDiff()
				for i in range( 0, 2 ) :
					label = GafferUI.NameLabel( None )
					label._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed )
					self.__diff.setValueWidget( i, label )

				GafferUI.Spacer( imath.V2i( 0 ), parenting = { "expand" : True } )

	def update( self, targets ) :

		Section.update( self, targets )

		values = [ target.scene.node() for target in targets ]
		backgrounds = None
		if len( values ) == 0 :
			values.append( "Select a node to inspect" )
			backgrounds = [ SideBySideDiff.Background.Other, SideBySideDiff.Background.Other ]
		elif len( values ) == 1 :
			values.append( "Select a second node to inspect differences" )
			backgrounds = [ SideBySideDiff.Background.AB, SideBySideDiff.Background.Other ]

		self.__diff.update( values, backgrounds = backgrounds )

		for index, value in enumerate( values ) :
			widget = self.__diff.getValueWidget( index )
			if isinstance( value, Gaffer.Node ) :
				widget.setFormatter( lambda x : ".".join( [ n.getName() for n in x ] ) )
				widget.setGraphComponent( value )
				widget.setEnabled( True )
			else :
				widget.setFormatter( lambda x : value )
				widget.setGraphComponent( None )
				widget.setEnabled( False )

SceneInspector.registerSection( __NodeSection, tab = None )

##########################################################################
# Path section
##########################################################################

class __PathSection( LocationSection ) :

	def __init__( self ) :

		LocationSection.__init__( self, collapsed = None )

		with self._mainColumn() :
			with Row().listContainer() :

				label = GafferUI.Label(
					"Location",
					horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right,
				)
				label._qtWidget().setFixedWidth( 150 )

				self.__diff = TextDiff( highlightDiffs = False )

				GafferUI.Spacer( imath.V2i( 0 ), parenting = { "expand" : True } )

	def update( self, targets ) :

		LocationSection.update( self, targets )

		numValidPaths = len( set( [ t.path for t in targets if t.path is not None ] ) )
		backgrounds = None
		if numValidPaths == 0 :
			labels = [ "Select a location to inspect" ]
			backgrounds = [ SideBySideDiff.Background.Other, SideBySideDiff.Background.Other ]
		else :
			labels = [ t.path if t.path is not None else "Invalid" for t in targets ]
			if numValidPaths == 1 and len( targets ) == 1 :
				labels.append( "Select a second location to inspect differences" )
				backgrounds = [ SideBySideDiff.Background.AB, SideBySideDiff.Background.Other ]

		self.__diff.update( labels, backgrounds = backgrounds )

		for i in range( 0, 2 ) :
			self.__diff.getValueWidget( i ).setEnabled(
				len( labels ) > i and labels[i].startswith( "/" )
			)

SceneInspector.registerSection( __PathSection, tab = "Selection" )

##########################################################################
# Transform section
##########################################################################

class __TransformSection( LocationSection ) :

	def __init__( self ) :

		LocationSection.__init__( self, collapsed = True, label = "Transform" )

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

		LocationSection.update( self, targets )

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
				components = { x : imath.V3f() for x in "shrt" }
				matrix.extractSHRT( components["s"], components["h"], components["r"], components["t"] )
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

class __BoundSection( LocationSection ) :

	def __init__( self ) :

		LocationSection.__init__( self, collapsed = True, label = "Bounding box" )

		with self._mainColumn() :
			self.__localBoundRow = DiffRow( self.__Inspector() )
			self.__worldBoundRow = DiffRow( self.__Inspector( world = True ), alternate = True )

	def update( self, targets ) :

		LocationSection.update( self, targets )

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

			bound = target.bound()
			if self.__world :
				bound = bound * target.fullTransform()

			return bound

SceneInspector.registerSection( __BoundSection, tab = "Selection" )

##########################################################################
# Attributes section
##########################################################################

class __AttributesSection( LocationSection ) :

	def __init__( self ) :

		LocationSection.__init__( self, collapsed = True, label = "Attributes" )

		with self._mainColumn() :
			self.__diffColumn = DiffColumn( self.__Inspector(), filterable=True )

	def update( self, targets ) :

		LocationSection.update( self, targets )

		self.__diffColumn.update( targets )

	class __Inspector( Inspector ) :

		def __init__( self, attributeName = None ) :

			self.__attributeName = attributeName

		def name( self ) :

			return self.__attributeName or ""

		def supportsInheritance( self ) :

			return True

		def __call__( self, target, ignoreInheritance = False ) :

			if target.path is None :
				return None

			if ignoreInheritance :
				attributes = target.attributes()
			else :
				attributes = target.fullAttributes()

			return attributes.get( self.__attributeName )

		def children( self, target ) :

			attributeNames = target.fullAttributes().keys() if target.path else []
			return [ self.__class__( attributeName ) for attributeName in attributeNames ]

SceneInspector.registerSection( __AttributesSection, tab = "Selection" )

##########################################################################
# Object section
##########################################################################

class _VDBGridInspector( Inspector ) :

	def __init__( self, gridName, metadataName ) :
		Inspector.__init__(self)
		self.__gridName = gridName
		self.__metadataName = metadataName

	def name( self ) :
		return "{0} : {1}".format(self.__gridName, self.__metadataName)

	def __call__(self, target):
		if target.path is None:
			return None

		object = target.object()
		if not isinstance( object, IECoreVDB.VDBObject ):
			return None

		if self.__gridName == None or  self.__metadataName == None:
			return None

		return object.metadata(self.__gridName)[self.__metadataName]

	def children ( self, target ) :
		return []

class _PrimitiveVariableTextDiff( TextDiff ) :

	def __init__( self, highlightDiffs=True, **kw ) :

		TextDiff.__init__( self, highlightDiffs, **kw )

	def _formatValues( self, values ) :

		result = []
		for value in values :

			if value is not None :

				s = str( value["interpolation"] )
				s += " " + value["data"].typeName()
				if hasattr( value["data"], "getInterpretation" ) :
					s += " (" + str( value["data"].getInterpretation() ) + ")"

				if value["indices"] :
					numElements = len( value["data"] )
					s += " ( Indexed : {0} element{1} )".format( numElements, '' if numElements == 1 else 's' )

			else :

				s = ""

			result.append( s )

		return result

class _SubdivisionTextDiff( TextDiff ) :

	def __init__( self, highlightDiffs=True, **kw ) :

		TextDiff.__init__( self, highlightDiffs, **kw )

	def _formatValues( self, values ) :

		if isinstance( values[0], IECore.CompoundData ) :
			return TextDiff._formatValues( self, [ len( v["sharpnesses"] ) for v in values ] )

		return TextDiff._formatValues( self, values )

class __ObjectSection( LocationSection ) :

	def __init__( self ) :

		LocationSection.__init__( self, collapsed = True, label = "Object" )

		with self._mainColumn() :

			DiffColumn(
				self.__TopologyInspector(),
				label = "Topology"
			)

			DiffColumn(
				self.__ParametersInspector(),
				label = "Parameters"
			)

			DiffColumn(
				self.__PrimitiveVariablesInspector(),
				diffCreator = _PrimitiveVariableTextDiff,
				label = "Primitive Variables"
			)

			DiffColumn(
				self.__SubdivisionInspector(),
				diffCreator = _SubdivisionTextDiff,
				label = "Subdivision"
			)

			DiffColumn(
				self.__VDBObjectInspector(),
				label = "VDB"
			)

	def update( self, targets ) :

		LocationSection.update( self, targets )

		for diffColumn in self._mainColumn() :
			diffColumn.update( targets )

	def _summary( self, targets ) :

		if not len( targets ) :
			return ""

		objects = [
			target.object() if target.path is not None else IECore.NullObject.defaultNullObject()
			for target in targets
		]

		def friendlyTypeName( o ) :
			annotatedTypeName = o.typeName().split( ":" )[-1]
			if isinstance( o, IECoreScene.CurvesPrimitive ) :
				annotatedTypeName += " - " + str( o.basis().standardBasis() )
			elif isinstance( o, IECoreScene.MeshPrimitive ) :
				annotatedTypeName += " - " + str( o.interpolation )

			return annotatedTypeName

		typeNames = [friendlyTypeName( o ) for o in objects]
		typeNames = [ "None" if t == "NullObject" else t for t in typeNames ]

		if len( typeNames ) == 1 or typeNames[0] == typeNames[1] :
			return typeNames[0] if typeNames[0] != "None" else ""
		else :
			return " / ".join( typeNames )

	class __TopologyInspector( Inspector ) :

		def __init__( self, interpolation = None, property = None ) :

			Inspector.__init__( self )

			self.__interpolation = interpolation
			self.__property = property

		def name( self ) :

			if self.__interpolation is not None :
				return str( self.__interpolation )
			else :
				return IECore.CamelCase.toSpaced( self.__property )

		def __call__( self, target ) :

			if target.path is None :
				return None

			object = target.object()
			if isinstance( object, IECore.NullObject ) :
				return None

			if self.__interpolation is not None :
				return object.variableSize( self.__interpolation ) if isinstance( object, IECoreScene.Primitive ) else None
			else :
				return getattr( object, self.__property, None )

		def children( self, target ) :

			if target.path is None :
				return []

			object = target.object()
			if not isinstance( object, IECoreScene.Primitive ) :
				return []

			result = []

			for i in [
				IECoreScene.PrimitiveVariable.Interpolation.Constant,
				IECoreScene.PrimitiveVariable.Interpolation.Uniform,
				IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECoreScene.PrimitiveVariable.Interpolation.Varying,
				IECoreScene.PrimitiveVariable.Interpolation.FaceVarying,
			] :
				result.append( self.__class__( interpolation = i ) )

			return result

	class __ParametersInspector( Inspector ) :

		def __init__( self, parameterName = None ) :

			Inspector.__init__( self )

			self.__parameterName = parameterName

		def name( self ) :

			return self.__parameterName

		def __call__( self, target ) :

			parameters = self.__parameters( target )
			if parameters is None :
				return None

			return parameters.get( self.__parameterName )

		def children( self, target ) :

			parameters = self.__parameters( target )
			if parameters is None :
				return []

			return [ self.__class__( p ) for p in parameters.keys() ]

		def __parameters( self, target ) :

			if target.path is None :
				return None

			object = target.object()
			if isinstance( object, ( IECoreScene.Camera, IECoreScene.ExternalProcedural ) ) :
				return object.parameters()

			return None

	class __VDBObjectInspector( Inspector ) :

		def __init__( self ) :
			Inspector.__init__(self)

		def name( self ) :
			return "VDB"

		def __call__(self, target):
			if target.path is None:
				return None

			object = target.object()
			if not isinstance( object, IECoreVDB.VDBObject ):
				return None

			return ""

		def children ( self, target ) :

			if target.path is None :
				return []

			object = target.object()
			if not isinstance( object, IECoreVDB.VDBObject ) :
				return []

			childInspectors = []
			for gridName in object.gridNames():
				for metadataName in object.metadata(gridName).keys():
					childInspectors.append(_VDBGridInspector( gridName, metadataName ) )

			return childInspectors

	class __PrimitiveVariablesInspector( Inspector ) :

		def __init__( self, primitiveVariableName = None ) :

			Inspector.__init__( self )

			self.__primitiveVariableName = primitiveVariableName

		def name( self ) :

			return self.__primitiveVariableName

		def __call__( self, target ) :

			if target.path is None :
				return None

			object = target.object()
			if not isinstance( object, IECoreScene.Primitive ) :
				return None

			if self.__primitiveVariableName not in object :
				return None

			primitiveVariable = object[self.__primitiveVariableName]

			return IECore.CompoundData(
				{
					"interpolation" : str( primitiveVariable.interpolation ),
					"data" : primitiveVariable.data,
					"indices" : primitiveVariable.indices
				}
			)

		def children( self, target ) :

			if target.path is None :
				return []

			object = target.object()
			if not isinstance( object, IECoreScene.Primitive ) :
				return []

			return [ self.__class__( k ) for k in object.keys() ]


	class __SubdivisionInspector( Inspector ) :

		def __init__( self, subdivisionVariableName = None ) :

			Inspector.__init__( self )

			self.__subdivisionVariableName = subdivisionVariableName

		def name( self ) :

			return self.__subdivisionVariableName

		def __call__( self, target ) :

			if target.path is None :
				return None

			object = target.object()
			if not isinstance( object, ( IECoreScene.MeshPrimitive, IECoreScene.CurvesPrimitive ) ) :
				return None

			if self.__subdivisionVariableName == "Corners" :
				return IECore.CompoundData( { "sharpnesses" : object.cornerSharpnesses(), "ids" : object.cornerIds() } )

			elif self.__subdivisionVariableName == "Creases" :
				return IECore.CompoundData( { "sharpnesses" : object.creaseSharpnesses(), "ids" : object.creaseIds(), "lengths" : object.creaseLengths() } )

			elif self.__subdivisionVariableName == "Interpolation":
				if isinstance( object, IECoreScene.CurvesPrimitive ) :
					return str( object.basis().standardBasis() )
				return object.interpolation

		def children( self, target ) :

			if target.path is None :
				return []

			object = target.object()
			if not isinstance( object, ( IECoreScene.MeshPrimitive, IECoreScene.CurvesPrimitive ) ) :
				return []

			result = [ self.__class__( "Interpolation" ) ]

			if isinstance( object, IECoreScene.MeshPrimitive ) and hasattr( object, "creaseIds" ):
				result.append( self.__class__( "Corners" ) )
				result.append( self.__class__( "Creases" ) )

			return result

SceneInspector.registerSection( __ObjectSection, tab = "Selection" )

##########################################################################
# Set Membership section
##########################################################################

class _SetMembershipDiff( SideBySideDiff ) :

	def __init__( self, **kw ) :

		SideBySideDiff.__init__( self, **kw )

		for i in range( 0, 2 ) :
			self.setValueWidget( i, GafferUI.Image( "setMembershipDot.png" ) )

class __SetMembershipSection( LocationSection ) :

	def __init__( self ) :

		LocationSection.__init__( self, collapsed = True, label = "Set Membership" )

		with self._mainColumn() :
			self.__diffColumn = DiffColumn( self.__Inspector(), _SetMembershipDiff, filterable = True )

	def update( self, targets ) :

		LocationSection.update( self, targets )

		self.__diffColumn.update( targets )

	class __Inspector( Inspector ) :

		def __init__( self, setName = None ) :

			self.__setName = setName

		def name( self ) :

			return self.__setName or ""

		def supportsInheritance( self ) :

			return True

		def __call__( self, target, ignoreInheritance = False ) :

			if target.path is None :
				return None

			set = target.set( self.__setName )

			m = set.value.match( target.path )
			if m & IECore.PathMatcher.Result.ExactMatch :
				return True

			if (not ignoreInheritance) and (m & IECore.PathMatcher.Result.AncestorMatch) :
				return True

			return None

		def children( self, target ) :

			if not target.path :
				return []

			setNames = sorted( [ str( n ) for n in target.setNames() ] )
			return [ self.__class__( setName ) for setName in setNames ]

		def _useBackgroundThread( self ) :

			return True

SceneInspector.registerSection( __SetMembershipSection, tab = "Selection" )

##########################################################################
# Global Options and Attributes section
##########################################################################

class __GlobalsSection( Section ) :

	def __init__( self, prefix, label ) :

		Section.__init__( self, collapsed = True, label = label )

		with self._mainColumn() :
			self.__diffColumn = DiffColumn( self.__Inspector( prefix ), filterable=True )

	def update( self, targets ) :

		Section.update( self, targets )

		self.__diffColumn.update( targets )

	class __Inspector( Inspector ) :

		def __init__( self, prefix, key = None ) :

			self.__prefix = prefix
			self.__key = key

		def name( self ) :

			return self.__key[len(self.__prefix):] if self.__key else ""

		def __call__( self, target ) :

			globals = target.globals()
			return globals.get( self.__key )

		def children( self, target ) :

			globals = target.globals()
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
					collapseButton.clickedSignal().connect( Gaffer.WeakMethod( self.__collapseButtonClicked ), scoped = False )
					self.__label = TextDiff()
					GafferUI.Spacer( imath.V2i( 1 ), parenting = { "expand" : True } )

				self.__diffColumn = DiffColumn( self.__Inspector( name ) )
				self.__diffColumn.setVisible( False )

		self.__name = name

	def update( self, targets ) :

		outputs = [ target.globals().get( self.__name ) for target in targets ]
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

			output = target.globals().get( self.__outputName )
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

			output = target.globals().get( self.__outputName )
			if output is None :
				return []

			return [ self.__class__( self.__outputName, p ) for p in output.parameters().keys() + [ "fileName", "type", "data" ] ]

class __OutputsSection( Section ) :

	def __init__( self ) :

		Section.__init__( self, collapsed = True, label = "Outputs" )

		self.__rows = {} # mapping from output name to row

	def update( self, targets ) :

		Section.update( self, targets )

		outputNames = set()
		for target in targets :
			g = target.globals()
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

		with self.__row :
			for i, diffName in enumerate( [ "A", "AB", "B" ] ) :
				with GafferUI.Frame( borderWidth = 5, borderStyle = GafferUI.Frame.BorderStyle.None_ ) as frame :

					frame._qtWidget().setProperty( "gafferDiff", diffName )

					frame.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
					frame.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ), scoped = False )
					frame.enterSignal().connect( lambda widget : widget.setHighlighted( True ), scoped = False )
					frame.leaveSignal().connect( lambda widget : widget.setHighlighted( False ), scoped = False )
					frame.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
					frame.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )

					GafferUI.Label( "" )

	def update( self, values ) :

		values = [
			v.value if v is not None else IECore.PathMatcher()
			for v in values
		]

		if len( values ) == 1 :
			self.__updateField( 0, IECore.PathMatcher() )
			self.__updateField( 1, values[0] )
			self.__updateField( 2, IECore.PathMatcher() )
		else :
			assert( len( values ) == 2 )

			aOnly = IECore.PathMatcher( values[0] )
			aOnly.removePaths( values[1] )

			bOnly = IECore.PathMatcher( values[1] )
			bOnly.removePaths( values[0] )

			intersection = values[0].intersection( values[1] )

			self.__updateField( 0, aOnly, "-" )
			self.__updateField( 1, intersection, "" )
			self.__updateField( 2, bOnly, " +" )

		GafferUI.WidgetAlgo.joinEdges( self.__row )

	def __updateField( self, i, paths, prefix = "" ) :

		self.__row[i].paths = paths

		if paths.isEmpty() :
			self.__row[i].setVisible( False )
			return

		## \todo Remove fallback to slow `paths()` method
		size = paths.size() if hasattr( paths, "size" ) else len( paths.paths() )

		self.__row[i].getChild().setText( prefix + str( size ) )
		self.__row[i].setVisible( True )

	def __buttonPress( self, widget, event ) :

		return event.buttons == event.Buttons.Left

	def __buttonRelease( self, widget, event ) :

		if event.buttons != event.Buttons.None_ or event.button != event.Buttons.Left :
			return False

		editor = self.ancestor( SceneInspector )

		context = editor.context()
		GafferSceneUI.ContextAlgo.setSelectedPaths( context, widget.paths )

		return True

	def __dragBegin( self, widget, event ) :

		if event.buttons != event.Buttons.Left :
			return None

		GafferUI.Pointer.setCurrent( "objects" )
		return IECore.StringVectorData( widget.paths.paths() )

	def __dragEnd( self, widget, event ) :

		GafferUI.Pointer.setCurrent( None )

class _SetsSection( Section ) :

	def __init__( self ) :

		Section.__init__( self, collapsed = True, label = "Sets" )

		with self._mainColumn() :
			self.__diffColumn = DiffColumn( self.__Inspector(), _SetDiff, filterable = True )

	def update( self, targets ) :

		Section.update( self, targets )

		self.__diffColumn.update( targets )

	class __Inspector( Inspector ) :

		def __init__( self, setName = None ) :

			self.__setName = setName

		def name( self ) :

			return self.__setName or ""

		def __call__( self, target ) :

			return target.set( self.__setName )

		def children( self, target ) :

			setNames = sorted( [ str( n ) for n in target.setNames() ] )
			return [ self.__class__( setName ) for setName in setNames ]

		def _useBackgroundThread( self ) :

			return True

SceneInspector.SetsSection = _SetsSection

SceneInspector.registerSection( _SetsSection, tab = "Globals" )
