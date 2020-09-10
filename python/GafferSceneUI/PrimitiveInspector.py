##########################################################################
#
#  Copyright (c) 2018, Don Boogert. All rights reserved.
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
#      * Neither the name of Don Boogert nor the names of
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

import Gaffer
import GafferScene

import IECore
import IECoreScene

import GafferUI
import GafferSceneUI

import collections


def _getPrimvarToolTip( primVarName, primvar ) :
	toolTip = primVarName + " : "

	_type = type( primvar.data )

	if primvar.indices :
		toolTip += "indexed "

	if IECore.isSequenceDataType( primvar.data ) :
		_type = IECore.valueTypeFromSequenceType( _type )
		toolTip += "array "

	toolTip += _type.__name__

	try :
		toolTip += " (" + str( primvar.data.getInterpretation() ) + ")"
	except :
		pass

	return toolTip

def _nodeLabelFormatter( graphComponentList ):
	return ".".join( [ graphComponent.getName() for graphComponent in graphComponentList ] )

def _orderPrimitiveVariables( primVarNames ) :
	priorityOrder = ['P', 'N', 'uv', 'Pref']

	# primvars in priority order
	result = [pv for pv in priorityOrder if pv in primVarNames]

	# all remaining primvars in alphabetical order
	result.extend( sorted( [pv for pv in primVarNames if pv not in priorityOrder] ) )

	return result


def conditionPrimvar( primvar ) :
	scalarToVector = {
		IECore.TypeId.BoolData : IECore.BoolVectorData,
		IECore.TypeId.FloatData : IECore.FloatVectorData,
		IECore.TypeId.DoubleData : IECore.DoubleVectorData,
		IECore.TypeId.IntData : IECore.IntVectorData,
		IECore.TypeId.UIntData : IECore.UIntVectorData,
		IECore.TypeId.CharData : IECore.CharVectorData,
		IECore.TypeId.UCharData : IECore.UCharVectorData,
		IECore.TypeId.ShortData : IECore.ShortVectorData,
		IECore.TypeId.UShortData : IECore.UShortVectorData,
		IECore.TypeId.Int64Data : IECore.Int64VectorData,
		IECore.TypeId.UInt64Data : IECore.UInt64VectorData,
		IECore.TypeId.StringData : IECore.StringVectorData,
		IECore.TypeId.InternedStringData : IECore.InternedStringVectorData,
		IECore.TypeId.HalfData : IECore.HalfVectorData,

		IECore.TypeId.V2iData : IECore.V2iVectorData,
		IECore.TypeId.V2fData : IECore.V2fVectorData,
		IECore.TypeId.V2dData : IECore.V2dVectorData,

		IECore.TypeId.V3iData : IECore.V3iVectorData,
		IECore.TypeId.V3fData : IECore.V3fVectorData,
		IECore.TypeId.V3dData : IECore.V3dVectorData,

		IECore.TypeId.Color3fData : IECore.Color3fVectorData,
		IECore.TypeId.Color4fData : IECore.Color4fVectorData,

		IECore.TypeId.Box2iData : IECore.Box2iVectorData,
		IECore.TypeId.Box2fData : IECore.Box2fVectorData,
		IECore.TypeId.Box2dData : IECore.Box2dVectorData,

		IECore.TypeId.Box3iData : IECore.Box3iVectorData,
		IECore.TypeId.Box3fData : IECore.Box3fVectorData,
		IECore.TypeId.Box3dData : IECore.Box3dVectorData,

		IECore.TypeId.M33fData : IECore.M33fVectorData,
		IECore.TypeId.M33dData : IECore.M33dVectorData,

		IECore.TypeId.M44fData : IECore.M44fVectorData,
		IECore.TypeId.M44dData : IECore.M44dVectorData,

		IECore.TypeId.QuatfData : IECore.QuatfVectorData,
		IECore.TypeId.QuatdData : IECore.QuatdVectorData
	}

	c = scalarToVector.get( primvar.data.typeId(), None )

	if c :
		return c( [primvar.data.value] )

	return primvar.expandedData()


class PrimitiveInspector( GafferUI.NodeSetEditor ) :

	def __init__( self, scriptNode, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 8, spacing = 8 )

		self.__tabbedContainer = GafferUI.TabbedContainer()

		nodeAndLocationContainer = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, borderWidth = 8, spacing = 8 )
		nodeAndLocationContainer.append( GafferUI.Label( "Node" ) )

		self.__nodeLabel = GafferUI.NameLabel( None )
		self.__nodeLabel.setFormatter( _nodeLabelFormatter )

		self.__nodeFrame = GafferUI.Frame(
			borderWidth = 4,
			borderStyle = GafferUI.Frame.BorderStyle.None,
			child = self.__nodeLabel
		)

		self.__nodeFrame._qtWidget().setObjectName( "gafferNodeFrame" )
		self.__nodeFrame._qtWidget().setProperty( "gafferDiff", "Other" )

		nodeAndLocationContainer.append( self.__nodeFrame )

		nodeAndLocationContainer.append( GafferUI.Label( "Location" ) )
		self.__locationLabel = GafferUI.Label( "Select a location to inspect" )

		self.__locationFrame = GafferUI.Frame(
			borderWidth = 4,
			borderStyle = GafferUI.Frame.BorderStyle.None,
			child = self.__locationLabel
		)

		self.__locationFrame._qtWidget().setObjectName( "gafferLocationFrame" )
		self.__locationFrame._qtWidget().setProperty( "gafferDiff", "Other" )

		nodeAndLocationContainer.append( self.__locationFrame )

		column.append( nodeAndLocationContainer )

		column.append( self.__tabbedContainer )

		self.__dataWidgets = { }
		self.__tabbedChildWidgets = { }

		def listContainer( child ) :
			l = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 8, spacing = 8 )
			l.append( child )
			return l

		vectorDataWidgetOptions = {
			"editable" : False, "header" : True,
			"horizontalScrollMode" : GafferUI.ScrollMode.Automatic,
			"verticalScrollMode" : GafferUI.ScrollMode.Automatic
		}

		self.__dataWidgets[IECoreScene.PrimitiveVariable.Interpolation.Constant] = GafferUI.VectorDataWidget( **vectorDataWidgetOptions )
		self.__dataWidgets[IECoreScene.PrimitiveVariable.Interpolation.Uniform] = GafferUI.VectorDataWidget( **vectorDataWidgetOptions )
		self.__dataWidgets[IECoreScene.PrimitiveVariable.Interpolation.Vertex] = GafferUI.VectorDataWidget( **vectorDataWidgetOptions )
		self.__dataWidgets[IECoreScene.PrimitiveVariable.Interpolation.Varying] = GafferUI.VectorDataWidget( **vectorDataWidgetOptions )
		self.__dataWidgets[IECoreScene.PrimitiveVariable.Interpolation.FaceVarying] = GafferUI.VectorDataWidget( **vectorDataWidgetOptions )

		self.__tabbedChildWidgets[IECoreScene.PrimitiveVariable.Interpolation.Constant] = listContainer(
			self.__dataWidgets[IECoreScene.PrimitiveVariable.Interpolation.Constant] )
		self.__tabbedChildWidgets[IECoreScene.PrimitiveVariable.Interpolation.Uniform] = listContainer(
			self.__dataWidgets[IECoreScene.PrimitiveVariable.Interpolation.Uniform] )
		self.__tabbedChildWidgets[IECoreScene.PrimitiveVariable.Interpolation.Vertex] = listContainer(
			self.__dataWidgets[IECoreScene.PrimitiveVariable.Interpolation.Vertex] )
		self.__tabbedChildWidgets[IECoreScene.PrimitiveVariable.Interpolation.Varying] = listContainer(
			self.__dataWidgets[IECoreScene.PrimitiveVariable.Interpolation.Varying] )
		self.__tabbedChildWidgets[IECoreScene.PrimitiveVariable.Interpolation.FaceVarying] = listContainer(
			self.__dataWidgets[IECoreScene.PrimitiveVariable.Interpolation.FaceVarying] )

		self.__tabbedContainer.append( self.__tabbedChildWidgets[IECoreScene.PrimitiveVariable.Interpolation.Constant], "Constant" )
		self.__tabbedContainer.append( self.__tabbedChildWidgets[IECoreScene.PrimitiveVariable.Interpolation.Uniform], "Uniform" )
		self.__tabbedContainer.append( self.__tabbedChildWidgets[IECoreScene.PrimitiveVariable.Interpolation.Vertex], "Vertex" )
		self.__tabbedContainer.append( self.__tabbedChildWidgets[IECoreScene.PrimitiveVariable.Interpolation.Varying], "Varying" )
		self.__tabbedContainer.append( self.__tabbedChildWidgets[IECoreScene.PrimitiveVariable.Interpolation.FaceVarying], "FaceVarying" )

		GafferUI.NodeSetEditor.__init__( self, column, scriptNode, **kw )

		self._updateFromSet()

	def __repr__( self ) :

		return "GafferSceneUI.PrimitiveInspector( scriptNode )"

	def _updateFromSet( self ) :
		GafferUI.NodeSetEditor._updateFromSet( self )

		self.__scenePlug = None
		self.__plugDirtiedConnections = []
		self.__parentChangedConnections = []

		node = self._lastAddedNode()

		if node :
			self.__scenePlug = next( GafferScene.ScenePlug.RecursiveOutputRange( node ), None )
			if self.__scenePlug :
				self.__plugDirtiedConnections.append( node.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ) ) )
				self.__parentChangedConnections.append( self.__scenePlug.parentChangedSignal().connect( Gaffer.WeakMethod( self.__plugParentChanged ) ) )

		self.__updateLazily()

	def _updateFromContext( self, modifiedItems ) :

		for item in modifiedItems :
			if not item.startswith( "ui:" ) or GafferSceneUI.ContextAlgo.affectsSelectedPaths( item ) :
				self.__updateLazily()
				break

	def __plugDirtied( self, plug ) :

		if self.__scenePlug is not None and isinstance( plug, Gaffer.ObjectPlug ) and plug == self.__scenePlug["object"]:
			self.__updateLazily()

	def __plugParentChanged( self, plug, oldParent ) :

		# if a plug has been removed or moved to another node, then
		# we need to stop viewing it - _updateFromSet() will find the
		# next suitable plug from the current node set.
		self._updateFromSet()

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __updateLazily( self ) :
		self.__update()

	def __update( self ) :

		with self.getContext() :

			self.__locationFrame._qtWidget().setProperty( "gafferDiff", "Other" )
			self.__locationFrame._repolish()
			self.__nodeFrame._qtWidget().setProperty( "gafferDiff", "Other" )
			self.__nodeFrame._repolish()

			headers = collections.OrderedDict()
			primVars = collections.OrderedDict()
			toolTips = collections.OrderedDict()

			haveData = False

			if self.__scenePlug :

				self.__nodeLabel.setFormatter( _nodeLabelFormatter )
				self.__nodeLabel.setGraphComponent( self.__scenePlug.node() )
				self.__nodeFrame._qtWidget().setProperty( "gafferDiff", "AB" )
				self.__nodeFrame._repolish()

				targetPath = GafferSceneUI.ContextAlgo.getLastSelectedPath( self.getContext() )

				if targetPath :

					if self.__scenePlug.exists( targetPath ) :

						self.__locationLabel.setText( targetPath )
						self.__locationFrame._qtWidget().setProperty( "gafferDiff", "AB" )
						self.__locationFrame._repolish()

						obj = self.__scenePlug.object( targetPath )
						if isinstance( obj, IECoreScene.Primitive ) :

							haveData = True

							for primvarName in _orderPrimitiveVariables( obj.keys() ) :
								primvar = obj[primvarName]
								if not primvar.interpolation in primVars :
									headers[primvar.interpolation] = []
									primVars[primvar.interpolation] = []
									toolTips[primvar.interpolation] = []

								headers[primvar.interpolation].append( primvarName )
								primVars[primvar.interpolation].append( conditionPrimvar( primvar ) )
								toolTips[primvar.interpolation].append( _getPrimvarToolTip( primvarName, primvar ) )

							for interpolation in primVars.keys() :

								pv = primVars.get( interpolation, None )
								h = headers.get( interpolation, None )
								t = toolTips.get( interpolation, None )

								self.__tabbedContainer.setLabel( self.__tabbedChildWidgets[interpolation],
									"{0} ({1})".format( str( interpolation ), len( pv ) ) )

								self.__dataWidgets[interpolation].setToolTips( t )
								self.__dataWidgets[interpolation].setHeader( h )
								self.__dataWidgets[interpolation].setData( pv )
					else :

						self.__locationLabel.setText( 'Location %s does not exist' % targetPath )

				else :

					self.__locationLabel.setText( "Select a location to inspect" )

			else:

				self.__nodeLabel.setFormatter( lambda x : "Select a node to inspect" )

			if not haveData :

				for interpolation in [IECoreScene.PrimitiveVariable.Interpolation.Constant, IECoreScene.PrimitiveVariable.Interpolation.Uniform,
					IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECoreScene.PrimitiveVariable.Interpolation.Varying,
					IECoreScene.PrimitiveVariable.Interpolation.FaceVarying] :

					self.__dataWidgets[interpolation].setData( None )
					self.__dataWidgets[interpolation].setToolTips( [] )
					self.__tabbedContainer.setLabel( self.__tabbedChildWidgets[interpolation], str( interpolation ) )

GafferUI.Editor.registerType( "PrimitiveInspector", PrimitiveInspector )
