##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

# Registers MCPServer tools that depend on GafferImage.

import pathlib
import tempfile

import imath

import IECore

import Gaffer
import GafferImage

class CaptureImageTool( Gaffer.MCP.BasicTool ) :

	def __init__( self ) :

		Gaffer.MCP.BasicTool.__init__(

			self,

			"captureImage",

			"""
			Captures the image output from a node and returns it as a PNG.
			Doesn't modify the script.
			""",

			{
				"plug" :
				"""
				Path to an image plug relative to the script, for example `Catalogue.out`.
				The image is computed in the target's context, and the default OpenColorIO
				display and view transforms are applied.
				""",

				"layer" :
				"""
				Image layer to capture. Defaults to the primary RGB layer.
				""",

				"maxSize" :
				"""
				Maximum width or height of the returned image. Larger images are scaled down.
				""",
			}

		)

	def _call( self, target, plug: str, layer = "", maxSize = 1024 ) :

		imagePlug = target.scriptNode().descendant( plug )
		if not isinstance( imagePlug, GafferImage.ImagePlug ) :
			return self.errorResult( "\"{}\" is not an image plug".format( plug ) )

		## \todo When running in the UI, could/should we use the ContextTracker's context?
		with target.scriptNode().context(), IECore.CapturingMessageHandler() as messageHandler :

			try :

				channelNames = GafferImage.ImageAlgo.sortedChannelNames( imagePlug.channelNames() )
				layerNames = GafferImage.ImageAlgo.layerNames( channelNames )
				if layer not in layerNames :
					return self.errorResult(
						'Layer "{}" does not exist. Available layers : {}'.format(
							layer, ", ".join( f'"{l}"' for l in layerNames )
						)
					)

				channels = [ c for c in channelNames if GafferImage.ImageAlgo.layerName( c ) == layer ]
				pngData, originalSize, size = self.__captureImagePlug( imagePlug, channels[:3], maxSize )

			except Exception as e :

				return self.errorResult( "Failed to compute \"{}\" : {}".format( plug, e ) )

		text = "Captured \"{}\" ({}x{}), returned at {}x{}".format( plug, originalSize.x, originalSize.y, size.x, size.y )
		for message in messageHandler.messages :
			if message.level <= IECore.Msg.Level.Warning :
				text += "\n{} : {} : {}".format( IECore.Msg.levelAsString( message.level ), message.context, message.message )

		return self.imageResult( text, pngData )

	@staticmethod
	def __captureImagePlug( plug, channels, maxSize ) :

		# Resize to fit within `maxSize`, and produce an image
		# with square pixel aspect.

		format = plug.format()
		if format.getDisplayWindow().isEmpty() :
			raise ValueError( "Display window is empty" )

		inputSize = imath.V2i( round( format.width() * format.getPixelAspect() ), format.height() )
		scale = min( 1.0, maxSize / max( inputSize.x, inputSize.y ) )
		size = imath.V2i( max( 1, round( inputSize.x * scale ) ), max( 1, round( inputSize.y * scale ) ) )

		resize = GafferImage.Resize()
		resize["in"].setInput( plug )
		resize["format"].setValue( GafferImage.Format( size.x, size.y ) )
		resize["fitMode"].setValue( GafferImage.Resize.FitMode.Distort )

		# Shuffle the requested channels into RGB, since that's the
		# only thing the ImageWriter can put in a PNG.

		shuffle = GafferImage.Shuffle()
		shuffle["in"].setInput( resize["out"] )
		for source, destination in zip( channels, "RGB" ) :
			shuffle["shuffles"].addChild( Gaffer.ShufflePlug( source, destination ) )

		# Bake the display transform into the image, because models are typically
		# trained on display-referred data.

		config = GafferImage.OpenColorIOAlgo.currentConfig()
		display = config.getDefaultDisplay()

		displayTransform = GafferImage.DisplayTransform()
		displayTransform["in"].setInput( shuffle["out"] )
		displayTransform["display"].setValue( display )
		displayTransform["view"].setValue( config.getDefaultView( display ) )

		# Write to disk using ImageWriter, and read data back.

		writer = GafferImage.ImageWriter()
		writer["in"].setInput( displayTransform["out"] )
		writer["channels"].setValue( "R G B" )
		# The display transform has already been applied, so we don't
		# want the writer to apply any further conversion.
		writer["colorSpace"].setValue( GafferImage.OpenColorIOAlgo.getWorkingSpace( Gaffer.Context.current() ) )

		# Write in PNG format, since it is lossless and commonly understood
		# by the models we're talking to.
		with tempfile.TemporaryDirectory() as directory :
			writer["fileName"].setValue( pathlib.Path( directory ) / "capture.png" )
			writer["task"].execute()
			with open( writer["fileName"].getValue(), "rb" ) as f :
				pngData = f.read()

		return pngData, inputSize, size

Gaffer.MCP.Tool.registerTool( CaptureImageTool() )
