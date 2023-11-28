##########################################################################
#
#  Copyright (c) 2020, Image Engine Design Inc. All rights reserved.
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

import sys
import imath

import IECore

import Gaffer
import GafferImage
import GafferUI
import GafferImageUI

class DeepPixelInfo( GafferUI.Widget ) :

	def __init__( self, **kw ) :

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 )

		GafferUI.Widget.__init__( self, self.__column, **kw )

		self.__pixel = Gaffer.V2iPlug( "pixelCoordinates" )
		Gaffer.Metadata.registerValue( self.__pixel, "readOnly", True )
		self.__channels = Gaffer.StringVectorDataPlug( "channels", Gaffer.Plug.Direction.In, IECore.StringVectorData() )
		Gaffer.Metadata.registerValue( self.__channels, "readOnly", True )
		self.__autoFrame = Gaffer.BoolPlug( "autoFrame", defaultValue = True )
		self.__logarithmic = Gaffer.BoolPlug( "logarithmic" )

		# HACK for ChannelMaskPlug
		self.__inputPlugs = Gaffer.ArrayPlug( "in", element = GafferImage.ImagePlug() )

		self.__dummyNode = Gaffer.Node()
		self.__dummyNode.addChild( self.__pixel )
		self.__dummyNode.addChild( self.__channels )
		self.__dummyNode.addChild( self.__autoFrame )
		self.__dummyNode.addChild( self.__logarithmic )
		self.__dummyNode.addChild( self.__inputPlugs )

		self.__uiPlugDirtiedConnection = self.__dummyNode.plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__uiPlugDirtied ), scoped = True )

		with self.__column :
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :
				self.__busyWidget = GafferUI.BusyWidget( size = 20 )
				self.__p1 = GafferUI.PlugWidget( self.__pixel )
				self.__p2 = GafferUI.PlugWidget( GafferImageUI.RGBAChannelsPlugValueWidget( self.__channels ) )
				self.__p3 = GafferUI.PlugWidget( self.__autoFrame )
				self.__p4 = GafferUI.PlugWidget( self.__logarithmic )

			self.__gadgetWidget = GafferUI.GadgetWidget(
				bufferOptions = set( [ GafferUI.GLWidget.BufferOptions.Depth ] )
			)

			self.__deepSamplesGadget = GafferImageUI.DeepSampleGadget()
			self.__gadgetWidget.getViewportGadget().setPrimaryChild( self.__deepSamplesGadget )
			self.__gadgetWidget.getViewportGadget().setVariableAspectZoom( True )

		self.__pixelValues = [{}, {}]

	def __uiPlugDirtied( self, plug ):
		if plug == self.__logarithmic:
			self.__deepSamplesGadget.setLogarithmic( plug.getValue() )
		elif plug == self.__autoFrame:
			self.__deepSamplesGadget.setAutoFrame( plug.getValue() )

	def setSource( self, pixel, channels ):
		self.__pixel.setValue( pixel )
		self.__channels.setValue( channels )

	def updatePixelData( self, pixels ):
		self.__deepSamplesGadget.setDeepSamples( IECore.CompoundData(
			{
				"A" : pixels[0],
				"B" : pixels[1]
			}
		) )

	def setBusy( self, busy ):
		self.__busyWidget.setBusy( busy )
