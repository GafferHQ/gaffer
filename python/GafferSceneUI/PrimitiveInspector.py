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

	toolTip = primVarName + " : " + primvar.data.typeName()
	if hasattr( primvar.data, "getInterpretation" ) :
		toolTip += " (" + str( primvar.data.getInterpretation() ) + ")"

	if primvar.indices :
		numElements = len( primvar.data )
		toolTip += " ( Indexed : {0} element{1} )".format( numElements, "" if numElements == 1 else "s" )

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


class PrimitiveInspector( GafferSceneUI.SceneEditor ) :

	def __init__( self, scriptNode, **kw ) :

		column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, borderWidth = 8, spacing = 8 )

		self.__tabbedContainer = GafferUI.TabbedContainer()

		nodeAndLocationContainer = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, borderWidth = 8, spacing = 8 )
		nodeAndLocationContainer.append( GafferUI.Label( "Node" ) )

		self.__nodeLabel = GafferUI.NameLabel( None )
		self.__nodeLabel.setFormatter( _nodeLabelFormatter )

		self.__nodeFrame = GafferUI.Frame(
			borderWidth = 4,
			borderStyle = GafferUI.Frame.BorderStyle.None_,
			child = self.__nodeLabel
		)

		self.__nodeFrame._qtWidget().setObjectName( "gafferNodeFrame" )
		self.__nodeFrame._qtWidget().setProperty( "gafferDiff", "Other" )

		nodeAndLocationContainer.append( self.__nodeFrame )

		nodeAndLocationContainer.append( GafferUI.Label( "Location" ) )
		self.__locationLabel = GafferUI.Label( "Select a location to inspect" )

		self.__locationFrame = GafferUI.Frame(
			borderWidth = 4,
			borderStyle = GafferUI.Frame.BorderStyle.None_,
			child = self.__locationLabel
		)

		self.__locationFrame._qtWidget().setObjectName( "gafferLocationFrame" )
		self.__locationFrame._qtWidget().setProperty( "gafferDiff", "Other" )

		nodeAndLocationContainer.append( self.__locationFrame )

		self.__busyWidget = GafferUI.BusyWidget( size = 20 )
		nodeAndLocationContainer.append( self.__busyWidget )

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

		GafferSceneUI.SceneEditor.__init__( self, column, scriptNode, **kw )

		GafferSceneUI.ScriptNodeAlgo.selectedPathsChangedSignal( scriptNode ).connect(
			Gaffer.WeakMethod( self.__selectedPathsChanged )
		)

		self._updateFromSet()

	def __repr__( self ) :

		return "GafferSceneUI.PrimitiveInspector( scriptNode )"

	def _updateFromContext( self, modifiedItems ) :

		for item in modifiedItems :
			if not item.startswith( "ui:" ) :
				self.__updateLazily()
				break

	def _updateFromSettings( self, plug ) :

		if plug.isSame( self.settings()["in"]["object"] ) or plug.isSame( self.settings()["in"]["exists"] ) :
			self.__updateLazily()

	def __selectedPathsChanged( self, scriptNode ) :

		self.__updateLazily()

	@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
	def __updateLazily( self ) :

		with self.context() :
			self.__backgroundUpdate( GafferSceneUI.ScriptNodeAlgo.getLastSelectedPath( self.scriptNode() ) )

	@GafferUI.BackgroundMethod()
	def __backgroundUpdate( self, targetPath ) :

		if not targetPath :
			return None

		if not self.settings()["in"].exists( targetPath ) :
			return None

		return self.settings()["in"].object( targetPath )

	@__backgroundUpdate.plug
	def __backgroundUpdatePlug( self ) :

		return self.settings()["in"]

	@__backgroundUpdate.preCall
	def __backgroundUpdatePreCall( self ) :

		self.__busyWidget.setBusy( True )
		for (k,widget) in self.__dataWidgets.items():
			widget.setEnabled( False )

		if self.settings()["in"].getInput() is not None :
			self.__nodeLabel.setFormatter( _nodeLabelFormatter )
			self.__nodeLabel.setGraphComponent( self.settings()["in"].getInput().node() )
			self.__nodeFrame._qtWidget().setProperty( "gafferDiff", "AB" )
		else:
			self.__nodeLabel.setFormatter( lambda x : "Select a node to inspect" )
			self.__nodeFrame._qtWidget().setProperty( "gafferDiff", "Other" )
		self.__nodeFrame._repolish()

		if self.settings()["in"].getInput() is None :
			self.__locationLabel.setText( "" )
			self.__locationFrame._qtWidget().setProperty( "gafferDiff", "Other" )
		else:
			targetPath = GafferSceneUI.ScriptNodeAlgo.getLastSelectedPath( self.scriptNode() )
			if targetPath :
				self.__locationLabel.setText( targetPath )
				self.__locationFrame._qtWidget().setProperty( "gafferDiff", "AB" )
			else:
				self.__locationLabel.setText( "Select a location to inspect" )
				self.__locationFrame._qtWidget().setProperty( "gafferDiff", "Other" )
		self.__locationFrame._repolish()

	@__backgroundUpdate.postCall
	def __backgroundUpdatePostCall( self, backgroundResult ) :

		for (k,widget) in self.__dataWidgets.items():
			widget.setEnabled( True )

		self.__busyWidget.setBusy( False )

		if self.settings()["in"].getInput() is not None :
			targetPath = GafferSceneUI.ScriptNodeAlgo.getLastSelectedPath( self.scriptNode() )
			if targetPath:
				if backgroundResult is not None :
					self.__locationLabel.setText( targetPath )
				else:
					self.__locationFrame._qtWidget().setProperty( "gafferDiff", "Other" )
					self.__locationFrame._repolish()
					self.__locationLabel.setText( "Location %s does not exist" % targetPath )

		if isinstance( backgroundResult, IECoreScene.Primitive ) :
			headers = collections.OrderedDict()
			primVars = collections.OrderedDict()
			toolTips = collections.OrderedDict()

			for primvarName in _orderPrimitiveVariables( backgroundResult.keys() ) :
				primvar = backgroundResult[primvarName]
				if not primvar.interpolation in primVars :
					headers[primvar.interpolation] = []
					primVars[primvar.interpolation] = []
					toolTips[primvar.interpolation] = []

				headers[primvar.interpolation].append( primvarName )
				primVars[primvar.interpolation].append( conditionPrimvar( primvar ) )
				toolTips[primvar.interpolation].append( _getPrimvarToolTip( primvarName, primvar ) )

			for interpolation in self.__dataWidgets.keys() :

				pv = primVars.get( interpolation, None )
				h = headers.get( interpolation, None )
				t = toolTips.get( interpolation, [] )

				self.__tabbedContainer.setLabel( self.__tabbedChildWidgets[interpolation],
					str( interpolation ) + ( " ({0})".format( len( pv ) ) if pv else "" ) )

				self.__dataWidgets[interpolation].setToolTips( t )
				self.__dataWidgets[interpolation].setHeader( h )
				self.__dataWidgets[interpolation].setData( pv )

		else:

			for interpolation in self.__dataWidgets.keys():

				self.__dataWidgets[interpolation].setData( None )
				self.__dataWidgets[interpolation].setToolTips( [] )
				self.__tabbedContainer.setLabel( self.__tabbedChildWidgets[interpolation], str( interpolation ) )

GafferUI.Editor.registerType( "PrimitiveInspector", PrimitiveInspector )
