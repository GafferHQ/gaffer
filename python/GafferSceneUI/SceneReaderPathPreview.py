##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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
import IECoreScene
import IECoreImage

import Gaffer
import GafferUI

import GafferScene

class SceneReaderPathPreview( GafferUI.PathPreviewWidget ) :

	def __init__( self, path ) :

		column = GafferUI.SplitContainer( GafferUI.SplitContainer.Orientation.Vertical )

		GafferUI.PathPreviewWidget.__init__( self, column, path )

		self.__script = Gaffer.ScriptNode( "scenePreview" )

		# for reading IECore.SceneInterface files (scc, lscc)
		self.__script["SceneReader"] = GafferScene.SceneReader()

		# for reading more generic single object files (cob, ptc, pdc, etc)
		## \todo: can we unify all file input to SceneReader by creating a SceneInterface that makes
		# single object scenes using Reader ops behind the scenes?
		try :
			self.__script["ObjectPreview"] = _ObjectPreview()
		except ImportError :
			pass

		# display points and curves GL style rather than disks and ribbons
		self.__script["OpenGLAttributes"] = GafferScene.OpenGLAttributes( "OpenGLAttributes" )
		self.__script["OpenGLAttributes"]["attributes"]["pointsPrimitiveUseGLPoints"]["value"].setValue( 'forAll' )
		self.__script["OpenGLAttributes"]["attributes"]["pointsPrimitiveUseGLPoints"]["enabled"].setValue( True )
		self.__script["OpenGLAttributes"]["attributes"]["curvesPrimitiveUseGLLines"]["enabled"].setValue( True )

		self.__script["camera"] = _Camera()
		self.__script["camera"]["in"].setInput( self.__script["OpenGLAttributes"]["out"] )

		self.__viewer = GafferUI.Viewer( self.__script )
		column.append( self.__viewer )
		column.append( GafferUI.Timeline( self.__script ) )

		self._updateFromPath()

	def isValid( self ) :

		path = self.getPath()
		if not isinstance( path, ( Gaffer.FileSystemPath, Gaffer.SequencePath ) ) or not path.isLeaf() :
			return False

		if isinstance( path, Gaffer.SequencePath ) :

			try :
				sequence = IECore.FileSequence( str(path) )
				ext = sequence.fileName.split( "." )[-1]
			except :
				return False

		else :
			ext = str(path).split( "." )[-1]

		supported = set( GafferScene.SceneReader.supportedExtensions() )
		if "ObjectPreview" in self.__script :
			supported.update( IECore.Reader.supportedExtensions() )
			# no reason to preview a single image as a 3D scene
			supported.difference_update( IECore.Reader.supportedExtensions( IECoreImage.ImageReader.staticTypeId() ) )

		return ext in supported

	def _updateFromPath( self ) :

		self.__script["SceneReader"]["fileName"].setValue( "" )
		if "ObjectPreview" in self.__script :
			self.__script["ObjectPreview"]["fileName"].setValue( "" )

		if not self.isValid() :
			self.__script.selection().clear()
			return

		path = self.getPath()

		if isinstance( path, Gaffer.SequencePath ) :

			try :
				sequence = IECore.FileSequence( str(path) )
			except :
				return

			fileName = str(sequence)
			ext = sequence.fileName.split( "." )[-1]
			calc = IECore.OversamplesCalculator()
			if isinstance( sequence.frameList, IECore.FrameRange ) and sequence.frameList.step == 1 :
				calc.setTicksPerSecond( 24 )

			frames = sequence.frameList.asList()
			startFrame = int( calc.ticksToFrames( min(frames) ) )
			endFrame = int( calc.ticksToFrames( max(frames) ) )

		else :
			fileName = str(path)
			ext = str(path).split( "." )[-1]
			startFrame = None
			endFrame = None

		outPlug = None

		if ext in GafferScene.SceneReader.supportedExtensions() :

			self.__script["SceneReader"]["fileName"].setValue( fileName )
			outPlug = self.__script["SceneReader"]["out"]

			scene = IECoreScene.SharedSceneInterfaces.get( fileName )
			if hasattr( scene, "numBoundSamples" ) :
				numSamples = scene.numBoundSamples()
				if numSamples > 1 :
					startFrame = int( round( scene.boundSampleTime( 0 ) * 24.0 ) )
					endFrame = int( round( scene.boundSampleTime( numSamples - 1 ) * 24.0 ) )

		elif "ObjectPreview" in self.__script and ext in IECore.Reader.supportedExtensions() :

			self.__script["ObjectPreview"]["fileName"].setValue( fileName )
			outPlug = self.__script["ObjectPreview"]["out"]

		self.__script["OpenGLAttributes"]["in"].setInput( outPlug )

		# update the timeline
		if startFrame is not None and endFrame is not None :
			self.__script.context().setFrame( startFrame )
			self.__script["frameRange"]["start"].setValue( startFrame )
			self.__script["frameRange"]["end"].setValue( endFrame )
			GafferUI.Playback.acquire( self.__script.context() ).setFrameRange( startFrame, endFrame )

		# focus the viewer
		self.__script.selection().add( self.__script["camera"] )
		with self.__script.context() :
			self.__viewer.viewGadgetWidget().getViewportGadget().frame( self.__script["OpenGLAttributes"]["out"].bound( "/" ) )

GafferUI.PathPreviewWidget.registerType( "Scene", SceneReaderPathPreview )

class _Camera( Gaffer.Node ) :

	def __init__( self, name = "_Camera" ) :

		Gaffer.Node.__init__( self, name )

		self["in"] = GafferScene.ScenePlug()
		self["addCamera"] = Gaffer.BoolPlug( defaultValue = False )
		self["lookAt"] = Gaffer.StringPlug( defaultValue = "/" )
		self["depth"] = Gaffer.FloatPlug( defaultValue = 20, minValue = 0 )
		self["angle"] = Gaffer.FloatPlug()
		self["elevation"] = Gaffer.FloatPlug( defaultValue = 10, minValue = -90, maxValue = 90 )

		self["camera"] = GafferScene.Camera()
		self["camera"]["name"].setValue( "previewCamera" )

		self["parent"] = GafferScene.Parent()
		self["parent"]["in"].setInput( self["in"] )
		self["parent"]["parent"].setValue( "/" )
		self["parent"]["children"][0].setInput( self["camera"]["out"] )

		self["cameraFilter"] = GafferScene.PathFilter()
		self["cameraFilter"]["paths"].setValue( IECore.StringVectorData( [ "/previewCamera" ] ) )

		self["parentConstraint"] = GafferScene.ParentConstraint()
		self["parentConstraint"]["in"].setInput( self["parent"]["out"] )
		self["parentConstraint"]["target"].setInput( self["lookAt"] )
		self["parentConstraint"]["targetMode"].setValue( self["parentConstraint"].TargetMode.BoundCenter )
		self["parentConstraint"]["filter"].setInput( self["cameraFilter"]["out"] )

		self["cameraRotate"] = GafferScene.Transform()
		self["cameraRotate"]["in"].setInput( self["parentConstraint"]["out"] )
		self["cameraRotate"]["transform"]["rotate"]["y"].setInput( self["angle"] )
		self["cameraRotate"]["filter"].setInput( self["cameraFilter"]["out"] )

		self["elevationExpression"] = Gaffer.Expression()
		self["elevationExpression"].setExpression( 'parent["cameraRotate"]["transform"]["rotate"]["x"] = -parent["elevation"]' )

		self["cameraTranslate"] = GafferScene.Transform()
		self["cameraTranslate"]["in"].setInput( self["cameraRotate"]["out"] )
		self["cameraTranslate"]["transform"]["translate"]["z"].setInput( self["depth"] )
		self["cameraTranslate"]["filter"].setInput( self["cameraFilter"]["out"] )

		self["options"] = GafferScene.StandardOptions()
		self["options"]["options"]["renderCamera"]["enabled"].setValue( True )
		self["options"]["options"]["renderCamera"]["value"].setValue( "/previewCamera" )
		self["options"]["in"].setInput( self["cameraTranslate"]["out"] )

		self["switch"] = Gaffer.Switch()
		self["switch"].setup( GafferScene.ScenePlug() )
		self["switch"]["in"][0].setInput( self["in"] )
		self["switch"]["in"][1].setInput( self["options"]["out"] )
		self["switch"]["index"].setInput( self["addCamera"] )

		self["out"] = GafferScene.ScenePlug( direction = Gaffer.Plug.Direction.Out )
		self["out"].setInput( self["switch"]["out"] )

IECore.registerRunTimeTyped( _Camera )

Gaffer.Metadata.registerNode(

	_Camera,

	"nodeToolbar:top:type", "GafferUI.StandardNodeToolbar.top",

	plugs = {

		"*" : [

			"toolbarLayout:section", "Top",

		],

		"in" : [

			"plugValueWidget:type", "",

		],

		"out" : [

			"plugValueWidget:type", "",

		],

		"user" : [

			"plugValueWidget:type", "",

		],

		"lookAt" : [

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",

		],

		"depth" : [

			"numericPlugValueWidget:fixedCharacterWidth", 5,

		],

		"angle" : [

			"numericPlugValueWidget:fixedCharacterWidth", 5,

		],

		"elevation" : [

			"numericPlugValueWidget:fixedCharacterWidth", 5,

		],

	}

)

# Utility node for previewing single objects from a file or
# sequence (cob, ptc, pdc, etc), as though they were a scene
class _ObjectPreview( Gaffer.Node ) :

	def __init__( self, name = "_ObjectPreview" ) :

		Gaffer.Node.__init__( self, name )

		import GafferCortex

		self["fileName"] = Gaffer.StringPlug( defaultValue = "", substitutions = IECore.StringAlgo.Substitutions.NoSubstitutions )
		self["frameRate"] = Gaffer.FloatPlug( defaultValue = 24.0 )
		self["samplesPerFrame"] = Gaffer.IntPlug( defaultValue = 1, minValue = 1 )

		# single object scenes using Reader ops behind the scenes?
		self["ObjectReader"] = GafferCortex.ObjectReader()
		self["ObjectReaderExpression"] = Gaffer.Expression( "Expression" )
		self["ObjectReaderExpression"].setExpression(
'''
import IECore

fileName = parent['fileName']

try :
	sequence = IECore.FileSequence( fileName )
	calc = IECore.OversamplesCalculator( frameRate = parent["frameRate"], samplesPerFrame = parent["samplesPerFrame"] )
	if isinstance( sequence.frameList, IECore.FrameRange ) and sequence.frameList.step == 1 :
		calc.setTicksPerSecond( 24 )

	result = sequence.fileNameForFrame( calc.framesToTicks( context['frame'] ) )

except :
	result = fileName

parent['ObjectReader']['fileName'] = result
'''
		)
		self["ObjectToScene"] = GafferScene.ObjectToScene( "ObjectToScene" )
		self["ObjectToScene"]["object"].setInput( self["ObjectReader"]["out"] )

		self["out"] = GafferScene.ScenePlug( direction = Gaffer.Plug.Direction.Out )
		self["out"].setInput( self["ObjectToScene"]["out"] )

IECore.registerRunTimeTyped( _ObjectPreview )
