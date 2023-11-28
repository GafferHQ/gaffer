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

import os
import pathlib
import inspect
import unittest

import imath

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest
import GafferArnold
import GafferImage
import GafferOSL
import GafferDispatch

class ArnoldTextureBakeTest( GafferSceneTest.SceneTestCase ) :

	class SimpleEdgeDetect( GafferImage.ImageProcessor ):

		def __init__( self, name = "SimpleEdgeDetect" ) :
			GafferImage.ImageProcessor.__init__( self, name )

			self["HorizTransform"] = GafferImage.ImageTransform()
			self["HorizTransform"]["in"].setInput( self["in"] )
			self["HorizTransform"]["transform"]["translate"].setValue( imath.V2f( 1, 0 ) )

			self["HorizDiff"] = GafferImage.Merge()
			self["HorizDiff"]["in"]["in0"].setInput( self["HorizTransform"]["out"] )
			self["HorizDiff"]["in"]["in1"].setInput( self["in"] )
			self["HorizDiff"]["operation"].setValue( 10 )

			self["VertTransform"] = GafferImage.ImageTransform()
			self["VertTransform"]["in"].setInput( self["in"] )
			self["VertTransform"]["transform"]["translate"].setValue( imath.V2f( 0, 1 ) )

			self["VertDiff"] = GafferImage.Merge()
			self["VertDiff"]["in"]["in0"].setInput( self["VertTransform"]["out"] )
			self["VertDiff"]["in"]["in1"].setInput( self["in"] )
			self["VertDiff"]["operation"].setValue( 10 )

			self["Max"] = GafferImage.Merge()
			self["Max"]["in"]["in0"].setInput( self["HorizDiff"]["out"] )
			self["Max"]["in"]["in1"].setInput( self["VertDiff"]["out"] )
			self["Max"]["operation"].setValue( 13 )

			self["out"].setInput( self["Max"]["out"] )
			self["out"].setFlags( Gaffer.Plug.Flags.Serialisable, False )

	def testManyImages( self ):

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ '/...' ] ) )

		sphere = GafferScene.Sphere()
		sphere["transform"]["translate"].setValue( imath.V3f( -3, 0, 0 ) )

		standardSurface = GafferArnold.ArnoldShader()
		standardSurface.loadShader( "standard_surface" )

		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["in"].setInput( sphere["out"] )
		shaderAssignment["filter"].setInput( allFilter["out"] )
		shaderAssignment["shader"].setInput( standardSurface["out"] )

		uvScaleCode = GafferOSL.OSLCode()
		uvScaleCode["out"].addChild( Gaffer.V3fPlug( "uvScaled", direction = Gaffer.Plug.Direction.Out ) )
		uvScaleCode["code"].setValue( 'uvScaled = vector( u * 2, v * 2, 0 );' )

		outUV = GafferOSL.OSLShader()
		outUV.loadShader( "ObjectProcessing/OutUV" )
		outUV["parameters"]["value"].setInput( uvScaleCode["out"]["uvScaled"] )

		outObject2 = GafferOSL.OSLShader()
		outObject2.loadShader( "ObjectProcessing/OutObject" )
		outObject2["parameters"]["in0"].setInput( outUV["out"]["primitiveVariable"] )

		uvScaleOSL = GafferOSL.OSLObject()
		uvScaleOSL["in"].setInput( shaderAssignment["out"] )
		uvScaleOSL["filter"].setInput( allFilter["out"] )
		uvScaleOSL["shader"].setInput( outObject2["out"]["out"] )
		uvScaleOSL["interpolation"].setValue( 5 )


		mapOffset = GafferScene.MapOffset()
		mapOffset["in"].setInput( uvScaleOSL["out"] )
		mapOffset["filter"].setInput( allFilter["out"] )
		mapOffset["udim"].setValue( 1033 )

		offsetGroup = GafferScene.Group()
		offsetGroup["in"]["in0"].setInput( mapOffset["out"] )
		offsetGroup["name"].setValue( 'offset' )
		offsetGroup["transform"]["translate"].setValue( imath.V3f( 6, 0, 3 ) )

		combineGroup = GafferScene.Group()
		combineGroup["in"]["in0"].setInput( uvScaleOSL["out"] )
		combineGroup["in"]["in1"].setInput( offsetGroup["out"] )

		lights = []
		for color, rotate in [
			( ( 1, 0, 0 ), ( 0, 0, 0) ),
			( ( 0, 1, 0 ), ( 0, 90, 0 ) ),
			( ( 0, 0, 1 ), ( -90, 0, 0 ) )
		] :
			light = GafferArnold.ArnoldLight()
			light.loadShader( "distant_light" )
			light["parameters"]["color"].setValue( imath.Color3f( *color ) )
			light["transform"]["rotate"].setValue( imath.V3f( *rotate ) )
			combineGroup["in"][-1].setInput( light["out"] )
			lights.append( light )

		arnoldOptions = GafferArnold.ArnoldOptions()
		arnoldOptions["in"].setInput( combineGroup["out"] )
		arnoldOptions["options"]["giDiffuseDepth"]["enabled"].setValue( True )
		arnoldOptions["options"]["giDiffuseDepth"]["value"].setValue( 0 )
		arnoldOptions["options"]["giSpecularDepth"]["enabled"].setValue( True )
		arnoldOptions["options"]["giSpecularDepth"]["value"].setValue( 0 )

		arnoldTextureBake = GafferArnold.ArnoldTextureBake()
		arnoldTextureBake["in"].setInput( arnoldOptions["out"] )
		arnoldTextureBake["filter"].setInput( allFilter["out"] )
		arnoldTextureBake["bakeDirectory"].setValue( self.temporaryDirectory() / 'bakeSpheres' )
		arnoldTextureBake["defaultResolution"].setValue( 32 )
		arnoldTextureBake["aovs"].setValue( 'beauty:RGBA diffuse:diffuse' )
		arnoldTextureBake["tasks"].setValue( 3 )
		arnoldTextureBake["cleanupIntermediateFiles"].setValue( True )

		# Dispatch the bake
		script = Gaffer.ScriptNode()
		script.addChild( arnoldTextureBake )
		dispatcher = GafferDispatch.LocalDispatcher( jobPool = GafferDispatch.LocalDispatcher.JobPool() )
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() )
		dispatcher.dispatch( [ arnoldTextureBake ] )

		# Test that we are writing all expected files, and that we have cleaned up all temp files
		expectedUdims = [ i + j for j in [ 1001, 1033 ] for i in [ 0, 1, 10, 11 ] ]
		self.assertEqual( sorted( [ x.name for x in ( self.temporaryDirectory() / 'bakeSpheres' ).iterdir() ] ),
			[ "beauty", "diffuse" ] )
		self.assertEqual( sorted( [ x.name for x in ( self.temporaryDirectory() / 'bakeSpheres' / 'beauty' ).iterdir() ] ),
			[ "beauty.%i.tx"%i for i in expectedUdims ] )
		self.assertEqual( sorted( [ x.name for x in ( self.temporaryDirectory() / 'bakeSpheres' / 'diffuse' ).iterdir() ] ),
			[ "diffuse.%i.tx"%i for i in expectedUdims ] )


		# Read back in the 4 udim tiles of a sphere

		reader = GafferImage.ImageReader()

		imageTransform = GafferImage.ImageTransform()
		imageTransform["in"].setInput( reader["out"] )

		exprBox = Gaffer.Box()
		expression = Gaffer.Expression()
		exprBox.addChild( reader )
		exprBox.addChild( imageTransform )
		exprBox.addChild( expression )
		expression.setExpression( inspect.cleandoc(
			f"""
			i = context.get( "loop:index", 0 )
			layer = context.get( "collect:layerName", "beauty" )
			x = i % 2
			y = i // 2
			parent["ImageReader"]["fileName"] = '{(self.temporaryDirectory() / "bakeSpheres" / "%s" / "%s.%i.tx").as_posix()}' % ( layer, layer, 1001 + x + y * 10 )

			parent["ImageTransform"]["transform"]["translate"] = imath.V2f( 32 * x, 32 * y )
			"""
		), "python" )

		udimLoop = Gaffer.Loop()
		udimLoop.setup( GafferImage.ImagePlug() )
		udimLoop["iterations"].setValue( 4 )

		udimMerge = GafferImage.Merge()
		udimMerge["in"]["in0"].setInput( imageTransform["out"] )
		udimMerge["in"]["in1"].setInput( udimLoop["previous"] )

		udimLoop["next"].setInput( udimMerge["out"] )

		aovCollect = GafferImage.CollectImages()
		aovCollect["in"].setInput( udimLoop["out"] )
		aovCollect["rootLayers"].setValue( IECore.StringVectorData( [ 'beauty', 'diffuse' ] ) )


		# We have a little reference image for how the diffuse should look
		imageReaderRef = GafferImage.ImageReader()
		imageReaderRef["fileName"].setValue( pathlib.Path( __file__ ).parent / "images" / "sphereLightBake.exr" )

		resizeRef = GafferImage.Resize()
		resizeRef["in"].setInput( imageReaderRef["out"] )
		resizeRef["format"].setValue( GafferImage.Format( 64, 64, 1.000 ) )

		shuffleRef = GafferImage.Shuffle()
		shuffleRef["in"].setInput( resizeRef["out"] )
		for layer in [ "beauty", "diffuse" ]:
			for channel in [ "R", "G", "B" ]:
				shuffleRef["channels"].addChild( GafferImage.Shuffle.ChannelPlug() )
				shuffleRef["channels"][-1]["in"].setValue( channel )
				shuffleRef["channels"][-1]["out"].setValue( layer + "." + channel )

		differenceMerge = GafferImage.Merge()
		differenceMerge["in"]["in0"].setInput( aovCollect["out"] )
		differenceMerge["in"]["in1"].setInput( shuffleRef["out"] )
		differenceMerge["operation"].setValue( GafferImage.Merge.Operation.Difference )

		stats = GafferImage.ImageStats()
		stats["in"].setInput( differenceMerge["out"] )
		stats["area"].setValue( imath.Box2i( imath.V2i( 0, 0 ), imath.V2i( 64, 64 ) ) )

		# We should get a very close match to our single tile low res reference bake
		stats["channels"].setValue( IECore.StringVectorData( [ 'diffuse.R', 'diffuse.G', 'diffuse.B', 'diffuse.A' ] ) )
		for i in range( 3 ):
			self.assertLess( stats["average"].getValue()[i], 0.002 )
			self.assertLess( stats["max"].getValue()[i], 0.02 )

		# The beauty should be mostly a close match, but with a high max difference due to the spec pings
		stats["channels"].setValue( IECore.StringVectorData( [ 'beauty.R', 'beauty.G', 'beauty.B', 'beauty.A' ] ) )
		for i in range( 3 ):
			self.assertLess( stats["average"].getValue()[i], 0.1 )
			self.assertGreater( stats["max"].getValue()[i], 0.3 )

	def testTasks( self ):

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ '/...' ] ) )

		sphere = GafferScene.Sphere()
		sphere["transform"]["translate"].setValue( imath.V3f( -3, 0, 0 ) )

		uvScaleCode = GafferOSL.OSLCode()
		uvScaleCode["out"].addChild( Gaffer.V3fPlug( "uvScaled", direction = Gaffer.Plug.Direction.Out ) )
		uvScaleCode["code"].setValue( 'uvScaled = vector( u * 2, v * 2, 0 );' )

		outUV = GafferOSL.OSLShader()
		outUV.loadShader( "ObjectProcessing/OutUV" )
		outUV["parameters"]["value"].setInput( uvScaleCode["out"]["uvScaled"] )

		outObject2 = GafferOSL.OSLShader()
		outObject2.loadShader( "ObjectProcessing/OutObject" )
		outObject2["parameters"]["in0"].setInput( outUV["out"]["primitiveVariable"] )

		uvScaleOSL = GafferOSL.OSLObject()
		uvScaleOSL["in"].setInput( sphere["out"] )
		uvScaleOSL["filter"].setInput( allFilter["out"] )
		uvScaleOSL["shader"].setInput( outObject2["out"]["out"] )
		uvScaleOSL["interpolation"].setValue( 5 )

		mapOffset = GafferScene.MapOffset()
		mapOffset["in"].setInput( uvScaleOSL["out"] )
		mapOffset["filter"].setInput( allFilter["out"] )
		mapOffset["udim"].setValue( 1033 )

		offsetGroup = GafferScene.Group()
		offsetGroup["in"]["in0"].setInput( mapOffset["out"] )
		offsetGroup["name"].setValue( 'offset' )
		offsetGroup["transform"]["translate"].setValue( imath.V3f( 6, 0, 3 ) )

		combineGroup = GafferScene.Group()
		combineGroup["in"]["in0"].setInput( uvScaleOSL["out"] )
		combineGroup["in"]["in1"].setInput( offsetGroup["out"] )

		arnoldTextureBake = GafferArnold.ArnoldTextureBake()
		arnoldTextureBake["in"].setInput( combineGroup["out"] )
		arnoldTextureBake["filter"].setInput( allFilter["out"] )
		arnoldTextureBake["bakeDirectory"].setValue( self.temporaryDirectory() / 'bakeSpheres' )
		arnoldTextureBake["defaultResolution"].setValue( 1 )
		arnoldTextureBake["aovs"].setValue( 'beauty:RGBA diffuse:diffuse' )
		arnoldTextureBake["tasks"].setValue( 3 )
		arnoldTextureBake["cleanupIntermediateFiles"].setValue( False )

		# Dispatch the bake
		script = Gaffer.ScriptNode()
		script.addChild( arnoldTextureBake )
		dispatcher = GafferDispatch.LocalDispatcher( jobPool = GafferDispatch.LocalDispatcher.JobPool() )
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() )
		dispatcher.dispatch( [ arnoldTextureBake ] )

		self.assertEqual( sorted( [ x.name for x in ( self.temporaryDirectory() / 'bakeSpheres' ).iterdir() ] ),
			[ "BAKE_FILE_INDEX_0.0001.txt", "BAKE_FILE_INDEX_1.0001.txt", "BAKE_FILE_INDEX_2.0001.txt", "beauty", "diffuse" ] )
		# Make sure the 16 images that need writing get divided into very approximate thirds
		for i in range( 3 ):
			l = len( open( self.temporaryDirectory() / 'bakeSpheres' / f'BAKE_FILE_INDEX_{i}.0001.txt', encoding = "utf-8" ).readlines() )
			self.assertGreater( l, 2 )
			self.assertLess( l, 8 )

	@unittest.skipIf( GafferTest.inCI() or os.environ.get( "ARNOLD_LICENSE_ORDER" ) == "none", "Arnold license not available" )
	def testMerging( self ):

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ '/...' ] ) )

		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 20, 20 ) )

		# Assign a basic gradient shader
		uvGradientCode = GafferOSL.OSLCode()
		uvGradientCode["out"].addChild( Gaffer.Color3fPlug( "out", direction = Gaffer.Plug.Direction.Out ) )
		uvGradientCode["code"].setValue( 'out = color( u, v, 0.5 );' )

		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["in"].setInput( plane["out"] )
		shaderAssignment["filter"].setInput( allFilter["out"] )
		shaderAssignment["shader"].setInput( uvGradientCode["out"]["out"] )

		# Set up a random id from 0 - 3 on each face

		randomCode = GafferOSL.OSLCode()
		randomCode["out"].addChild( Gaffer.IntPlug( "randomId", direction = Gaffer.Plug.Direction.Out ) )
		randomCode["code"].setValue( 'randomId = int(cellnoise( P * 100 ) * 4);' )

		outInt = GafferOSL.OSLShader()
		outInt.loadShader( "ObjectProcessing/OutInt" )
		outInt["parameters"]["name"].setValue( 'randomId' )
		outInt["parameters"]["value"].setInput( randomCode["out"]["randomId"] )

		outObject = GafferOSL.OSLShader()
		outObject.loadShader( "ObjectProcessing/OutObject" )
		outObject["parameters"]["in0"].setInput( outInt["out"]["primitiveVariable"] )

		oSLObject = GafferOSL.OSLObject()
		oSLObject["in"].setInput( shaderAssignment["out"] )
		oSLObject["filter"].setInput( allFilter["out"] )
		oSLObject["shader"].setInput( outObject["out"]["out"] )
		oSLObject["interpolation"].setValue( 2 )

		# Create 4 meshes by picking each of the 4 ids

		deleteContextVariables = Gaffer.DeleteContextVariables()
		deleteContextVariables.setup( GafferScene.ScenePlug() )
		deleteContextVariables["variables"].setValue( 'collect:rootName' )
		deleteContextVariables["in"].setInput( oSLObject["out"] )

		pickCode = GafferOSL.OSLCode()
		pickCode["parameters"].addChild( Gaffer.IntPlug( "targetId" ) )
		pickCode["out"].addChild( Gaffer.IntPlug( "cull", direction = Gaffer.Plug.Direction.Out ) )
		pickCode["code"].setValue( 'int randomId; getattribute( "randomId", randomId ); cull = randomId != targetId;' )

		expression = Gaffer.Expression()
		pickCode.addChild( expression )
		expression.setExpression( 'parent.parameters.targetId = stoi( context( "collect:rootName", "0" ) );', "OSL" )

		outInt1 = GafferOSL.OSLShader()
		outInt1.loadShader( "ObjectProcessing/OutInt" )
		outInt1["parameters"]["name"].setValue( 'deleteFaces' )
		outInt1["parameters"]["value"].setInput( pickCode["out"]["cull"] )

		outObject1 = GafferOSL.OSLShader()
		outObject1.loadShader( "ObjectProcessing/OutObject" )
		outObject1["parameters"]["in0"].setInput( outInt1["out"]["primitiveVariable"] )

		oSLObject1 = GafferOSL.OSLObject()
		oSLObject1["in"].setInput( deleteContextVariables["out"] )
		oSLObject1["filter"].setInput( allFilter["out"] )
		oSLObject1["shader"].setInput( outObject1["out"]["out"] )
		oSLObject1["interpolation"].setValue( 2 )

		deleteFaces = GafferScene.DeleteFaces()
		deleteFaces["in"].setInput( oSLObject1["out"] )
		deleteFaces["filter"].setInput( allFilter["out"] )

		collectScenes = GafferScene.CollectScenes()
		collectScenes["in"].setInput( deleteFaces["out"] )
		collectScenes["rootNames"].setValue( IECore.StringVectorData( [ '0', '1', '2', '3' ] ) )
		collectScenes["sourceRoot"].setValue( '/plane' )

		# First variant:  bake everything, covering the whole 1001 UDIM

		customAttributes1 = GafferScene.CustomAttributes()
		customAttributes1["attributes"].addChild( Gaffer.NameValuePlug( 'bake:fileName', IECore.StringData( ( pathlib.Path( "${bakeDirectory}" ) / "complete" / "<AOV>" / "<AOV>.<UDIM>.exr" ).as_posix() ) ) )
		customAttributes1["in"].setInput( collectScenes["out"] )

		# Second vaiant: bake just 2 of the 4 meshes, leaving lots of holes that will need filling
		pruneFilter = GafferScene.PathFilter()
		pruneFilter["paths"].setValue( IECore.StringVectorData( [ '/2', '/3' ] ) )

		prune = GafferScene.Prune()
		prune["in"].setInput( collectScenes["out"] )
		prune["filter"].setInput( pruneFilter["out"] )


		customAttributes2 = GafferScene.CustomAttributes()
		customAttributes2["attributes"].addChild( Gaffer.NameValuePlug( 'bake:fileName', IECore.StringData( ( pathlib.Path( "${bakeDirectory}" ) / "incomplete" / "<AOV>" / "<AOV>.<UDIM>.exr" ).as_posix() ) ) )
		customAttributes2["in"].setInput( prune["out"] )


		# Third variant: bake everything, but with one mesh at a higher resolution

		customAttributes3 = GafferScene.CustomAttributes()
		customAttributes3["attributes"].addChild( Gaffer.NameValuePlug( 'bake:fileName', IECore.StringData( ( pathlib.Path( "${bakeDirectory}" ) / "mismatch" / "<AOV>" / "<AOV>.<UDIM>.exr" ).as_posix() ) ) )
		customAttributes3["in"].setInput( collectScenes["out"] )

		pathFilter2 = GafferScene.PathFilter()
		pathFilter2["paths"].setValue( IECore.StringVectorData( [ '/2' ] ) )

		customAttributes = GafferScene.CustomAttributes()
		customAttributes["attributes"].addChild( Gaffer.NameValuePlug( 'bake:resolution', IECore.IntData( 200 ) ) )
		customAttributes["filter"].setInput( pathFilter2["out"] )
		customAttributes["in"].setInput( customAttributes3["out"] )

		# Merge the 3 variants
		mergeGroup = GafferScene.Group()
		mergeGroup["in"][-1].setInput( customAttributes["out"] )
		mergeGroup["in"][-1].setInput( customAttributes1["out"] )
		mergeGroup["in"][-1].setInput( customAttributes2["out"] )

		arnoldTextureBake = GafferArnold.ArnoldTextureBake()
		arnoldTextureBake["in"].setInput( mergeGroup["out"] )
		arnoldTextureBake["filter"].setInput( allFilter["out"] )
		arnoldTextureBake["bakeDirectory"].setValue( self.temporaryDirectory() / 'bakeMerge' )
		arnoldTextureBake["defaultResolution"].setValue( 128 )

		# We want to check the intermediate results
		arnoldTextureBake["cleanupIntermediateFiles"].setValue( False )

		# Dispatch the bake
		script = Gaffer.ScriptNode()
		script.addChild( arnoldTextureBake )
		dispatcher = GafferDispatch.LocalDispatcher( jobPool = GafferDispatch.LocalDispatcher.JobPool() )
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() )
		dispatcher.dispatch( [ arnoldTextureBake ] )

		# Check results
		imageReader = GafferImage.ImageReader()

		outLayer = GafferOSL.OSLShader()
		outLayer.loadShader( "ImageProcessing/OutLayer" )
		outLayer["parameters"]["layerColor"].setInput( uvGradientCode["out"]["out"] )

		outImage = GafferOSL.OSLShader()
		outImage.loadShader( "ImageProcessing/OutImage" )
		outImage["parameters"]["in0"].setInput( outLayer["out"]["layer"] )
		oSLImage = GafferOSL.OSLImage()
		oSLImage["in"].setInput( imageReader["out"] )
		oSLImage["shader"].setInput( outImage["out"]["out"] )

		merge3 = GafferImage.Merge()
		merge3["in"]["in0"].setInput( oSLImage["out"] )
		merge3["in"]["in1"].setInput( imageReader["out"] )
		merge3["operation"].setValue( 10 )

		edgeDetect = self.SimpleEdgeDetect()
		edgeDetect["in"].setInput( imageReader["out"] )

		edgeStats = GafferImage.ImageStats()
		edgeStats["in"].setInput( edgeDetect["out"] )

		refDiffStats = GafferImage.ImageStats()
		refDiffStats["in"].setInput( merge3["out"] )

		oneLayerReader = GafferImage.ImageReader()

		grade = GafferImage.Grade()
		grade["in"].setInput( oneLayerReader["out"] )
		grade["channels"].setValue( '[A]' )
		grade["blackPoint"].setValue( imath.Color4f( 0, 0, 0, 0.999899983 ) )

		copyChannels = GafferImage.CopyChannels()
		copyChannels["in"]["in0"].setInput( merge3["out"] )
		copyChannels["in"]["in1"].setInput( grade["out"] )
		copyChannels["channels"].setValue( '[A]' )

		premultiply = GafferImage.Premultiply()
		premultiply["in"].setInput( copyChannels["out"] )

		refDiffCoveredStats = GafferImage.ImageStats()
		refDiffCoveredStats["in"].setInput( premultiply["out"] )

		# We are testing 3 different cases:
		# complete : Should be an exact match.
		# incomplete : Expect some mild variance of slopes and some error, because we have to
		#              reconstruct a lot of missing data.
		# mismatch : We should get a larger image, sized to the highest override on any mesh.
		#            Match won't be as perfect, because we're combining source images at
		#            different resolutions
		for name, expectedSize, maxEdge, maxRefDiff, maxMaskedDiff in [
				( "complete",   128, 0.01, 0.000001, 0.000001 ),
				( "incomplete", 128, 0.05,     0.15, 0.000001 ),
				( "mismatch",   200, 0.01,     0.01,     0.01 ) ]:
			imageReader["fileName"].setValue( self.temporaryDirectory() / "bakeMerge" / name / "beauty" / "beauty.1001.tx"  )
			oneLayerReader["fileName"].setValue( self.temporaryDirectory() / "bakeMerge" / name / "beauty" / "beauty.1001.exr"  )

			self.assertEqual( imageReader["out"]["format"].getValue().width(), expectedSize )
			self.assertEqual( imageReader["out"]["format"].getValue().height(), expectedSize )

			edgeStats["area"].setValue( imath.Box2i( imath.V2i( 1 ), imath.V2i( expectedSize - 1 ) ) )
			refDiffStats["area"].setValue( imath.Box2i( imath.V2i( 1 ), imath.V2i( expectedSize - 1 ) ) )
			refDiffCoveredStats["area"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( expectedSize ) ) )

			# Blue channel is constant, so everything should line up perfectly
			self.assertEqual( 0, edgeStats["max"].getValue()[2] )
			self.assertEqual( 0, refDiffStats["max"].getValue()[2] )
			self.assertEqual( 0, refDiffCoveredStats["max"].getValue()[2] )

			for i in range(2):

				# Make sure we've got actual data, by checking that we have some error ( we're not expecting
				# to perfectly reconstruct the gradient when the input is incomplete )
				self.assertGreater( edgeStats["max"].getValue()[i], 0.005 )
				if name == "incomplete":
					self.assertGreater( edgeStats["max"].getValue()[i], 0.03 )
					self.assertGreater( refDiffStats["max"].getValue()[i], 0.06 )

				self.assertLess( edgeStats["max"].getValue()[i], maxEdge )
				self.assertLess( refDiffStats["max"].getValue()[i], maxRefDiff )
				self.assertLess( refDiffCoveredStats["max"].getValue()[i], maxMaskedDiff )

if __name__ == "__main__":
	unittest.main()
