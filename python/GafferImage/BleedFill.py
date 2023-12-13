##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import inspect

import IECore

import imath

import Gaffer
import GafferImage

class BleedFill( GafferImage.ImageProcessor ) :

	def __init__(self, name = 'BleedFill' ) :

		GafferImage.ImageProcessor.__init__( self, name )

		self.addChild( Gaffer.BoolPlug( "expandDataWindow" ) )

		self.addChild( Gaffer.IntPlug( "__blurIterations" ) )
		self['__blurIterations'].setFlags(Gaffer.Plug.Flags.Serialisable, False)

		self['__formatQuery'] = GafferImage.FormatQuery()
		self['__formatQuery']["image"].setInput( self["in"] )
		self['__formatQuery']["view"].setValue( "default" )

		self["__blurIterationsExpression"] = Gaffer.Expression()
		self["__blurIterationsExpression"].setExpression( inspect.cleandoc(
			"""
			import math
			f = parent["__formatQuery"]["format"]
			parent["__blurIterations"] = int( math.log( min( f.width(), f.height() ), 2 ) )
			"""
		), "python" )

		self["__displayWindowConstant"] = GafferImage.Constant()
		self["__displayWindowConstant"]["color"].setValue( imath.Color4f( 0, 0, 0, 0 ) )

		self["__displayWindowExpression"] = Gaffer.Expression()
		self["__displayWindowExpression"].setExpression( 'parent["__displayWindowConstant"]["format"] = parent["__formatQuery"]["format"]', "python" )

		self["__expandMerge"] = GafferImage.Merge()
		self["__expandMerge"]["in"][0].setInput( self["in"] )
		self["__expandMerge"]["in"][1].setInput( self["__displayWindowConstant"]["out"] )
		self["__expandMerge"]["operation"].setValue( GafferImage.Merge.Operation.Over )

		self["__expandSwitch"] = Gaffer.Switch()
		self["__expandSwitch"].setup( self["in"] )
		self["__expandSwitch"]["in"][0].setInput( self["in"] )
		self["__expandSwitch"]["in"][1].setInput( self["__expandMerge"]["out"] )
		self["__expandSwitch"]["index"].setInput( self["expandDataWindow"] )

		# First blur via repeated downsampling
		self["__blurLoop"] = GafferImage.ImageLoop()
		self["__blurLoop"]["iterations"].setInput( self["__blurIterations"] )
		self["__blurLoop"]["in"].setInput( self["__expandSwitch"]["out"] )

		self["__downsample"] = GafferImage.Resize()
		self["__downsample"]["in"].setInput( self["__blurLoop"]["previous"] )
		self["__downsample"]["filter"].setValue( "sharp-gaussian" )

		self["__downsampleExpression"] = Gaffer.Expression()
		self["__downsampleExpression"].setExpression( inspect.cleandoc(
			"""
			import GafferImage
			import IECore

			f = parent["__formatQuery"]["format"]

			divisor = 2 <<  context.get("loop:index", 0)

			parent["__downsample"]["format"] =  GafferImage.Format( imath.Box2i( f.getDisplayWindow().min() / divisor, f.getDisplayWindow().max() / divisor ), 1.0 )
			"""
		), "python" )

		# Multiply each successive octave by a falloff factor so that we prioritize higher frequencies when they exist
		self["__grade"] = GafferImage.Grade( "Grade" )
		self["__grade"]['channels'].setValue( "*" )
		self["__grade"]['multiply'].setValue( imath.Color4f( 0.1 ) )
		self["__grade"]['blackClamp'].setValue( False )
		self["__grade"]["in"].setInput( self["__downsample"]["out"] )

		self["__blurLoop"]["next"].setInput( self["__grade"]["out"] )


		self["__reverseLoopContext"] = GafferImage.ImageContextVariables()
		self["__reverseLoopContext"]["in"].setInput( self["__blurLoop"]["previous"] )
		self["__reverseLoopContext"]["variables"].addChild( Gaffer.NameValuePlug( "loop:index", IECore.IntData( 0 ), "loopIndex" ) )

		self["__reverseLoopExpression"] = Gaffer.Expression()
		self["__reverseLoopExpression"].setExpression( inspect.cleandoc(
			"""
			parent["__reverseLoopContext"]["variables"]["loopIndex"]["value"] = parent["__blurIterations"] - context.get( "loop:index", 0 )
			"""
		), "python" )

		# Loop through image resolution levels combining the most downsampled image with less downsampled versions,
		# one level at a time
		self["__combineLoop"] = GafferImage.ImageLoop()

		self["__combineLoopExpression"] = Gaffer.Expression()
		self["__combineLoopExpression"].setExpression(
			'parent["__combineLoop"]["iterations"] = parent["__blurIterations"] + 1',
			"python"
		)

		self["__upsample"] = GafferImage.Resize()
		self["__upsample"]["in"].setInput( self["__combineLoop"]["previous"] )
		self["__upsample"]["filter"].setValue( "smoothGaussian" )

		self["__upsampleExpression"] = Gaffer.Expression()
		self["__upsampleExpression"].setExpression( inspect.cleandoc(
			"""
			import GafferImage
			import IECore

			f = parent["__formatQuery"]["format"]

			divisor = 1 <<  (  parent["__blurIterations"] - context.get("loop:index", 0) )

			parent["__upsample"]["format"] =  GafferImage.Format( imath.Box2i( f.getDisplayWindow().min() / divisor, f.getDisplayWindow().max() / divisor ), 1.0 )
			"""
		), "python" )

		self["__merge"] = GafferImage.Merge()
		self["__merge"]["operation"].setValue( GafferImage.Merge.Operation.Over )
		self["__merge"]["in"][0].setInput( self["__upsample"]["out"] )
		self["__merge"]["in"][1].setInput( self["__reverseLoopContext"]["out"] )

		self["__combineLoop"]["next"].setInput( self["__merge"]["out"] )

		# When downsampling to target display window sizes with a non-square image,
		# the data window size gets rounded up to the nearest integer, potentially introducing
		# a small error in data window size that gets amplified during repeated upsampling.
		# To fix this, crop to the data window after scaling.
		self["__restoreDataSize"] = GafferImage.Crop()
		self["__restoreDataSize"]["in"].setInput( self["__combineLoop"]["out"] )
		self["__restoreDataSize"]["affectDisplayWindow"].setValue( False )

		self["__restoreDataExpression"] = Gaffer.Expression()
		self["__restoreDataExpression"].setExpression(
			'parent["__restoreDataSize"]["area"] = parent["__expandSwitch"]["out"]["dataWindow"]', "python"
		)

		self["__unpremult"] = GafferImage.Unpremultiply()
		self["__unpremult"]['channels'].setValue( "*" )
		self["__unpremult"]["in"].setInput( self["__restoreDataSize"]["out"] )

		self["__resetAlpha"] = GafferImage.Shuffle()
		self["__resetAlpha"]["shuffles"].addChild( Gaffer.ShufflePlug( "__white", "A" ) )
		self["__resetAlpha"]["in"].setInput( self["__unpremult"]["out"] )

		self["__disableSwitch"] = Gaffer.Switch()
		self["__disableSwitch"].setup( self["in"] )
		self["__disableSwitch"]["in"][0].setInput( self["in"] )
		self["__disableSwitch"]["in"][1].setInput( self["__resetAlpha"]["out"] )
		self["__disableSwitch"]["index"].setInput( self["enabled"] )

		self['out'].setFlags(Gaffer.Plug.Flags.Serialisable, False)
		self["out"].setInput( self["__disableSwitch"]["out"] )

IECore.registerRunTimeTyped( BleedFill, typeName = "GafferImage::BleedFill" )
