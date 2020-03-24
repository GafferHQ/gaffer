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

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferArnold
import GafferDispatch
import GafferImage

import imath
import inspect

class ArnoldTextureBake( GafferDispatch.TaskNode ) :

	class __CameraSetup( GafferScene.FilteredSceneProcessor ) :

		def __init__( self, name = "__CameraSetup" ) :

			GafferScene.FilteredSceneProcessor.__init__( self, name )

			# Public plugs
			self["cameraGroup"] = Gaffer.StringPlug( "cameraGroup", Gaffer.Plug.Direction.In, "__TEXTUREBAKE_CAMERAS" )
			self["bakeDirectory"] = Gaffer.StringPlug( "bakeDirectory", Gaffer.Plug.Direction.In, "" )
			self["defaultFileName"] = Gaffer.StringPlug( "defaultFileName", Gaffer.Plug.Direction.In, "${bakeDirectory}/<AOV>/<AOV>.<UDIM>.exr" )
			self["defaultResolution"] = Gaffer.IntPlug( "defaultResolution", Gaffer.Plug.Direction.In, 512 )
			self["uvSet"] = Gaffer.StringPlug( "uvSet", Gaffer.Plug.Direction.In, "uv" )
			self["normalOffset"] = Gaffer.FloatPlug( "normalOffset", Gaffer.Plug.Direction.In, 0.1 )
			self["aovs"] = Gaffer.StringPlug( "aovs", Gaffer.Plug.Direction.In, "beauty:rgba" )
			self["tasks"] = Gaffer.IntPlug( "tasks", Gaffer.Plug.Direction.In, 1 )
			self["taskIndex"] = Gaffer.IntPlug( "taskIndex", Gaffer.Plug.Direction.In, 0 )

			# Output
			self["renderFileList"] = Gaffer.StringVectorDataPlug( "renderFileList", Gaffer.Plug.Direction.Out, defaultValue = IECore.StringVectorData() )
			self["renderFileList"].setFlags( Gaffer.Plug.Flags.Serialisable, False )

			# Private internal network

			self["__udimQuery"] = GafferScene.UDIMQuery()
			self["__udimQuery"]["in"].setInput(  self["in"] )
			self["__udimQuery"]["uvSet"].setInput(  self["uvSet"] )
			self["__udimQuery"]["attributes"].setValue( "bake:resolution bake:fileName" )
			self["__udimQuery"]["filter"].setInput( self["filter"] )

			self["__chunkedBakeInfo"] = Gaffer.CompoundObjectPlug( "__chunkedBakeInfo", Gaffer.Plug.Direction.In, IECore.CompoundObject() )
			self["__chunkedBakeInfo"].setFlags( Gaffer.Plug.Flags.Serialisable, False )

			self["__chunkExpression"] = Gaffer.Expression()
			self["__chunkExpression"].setExpression( inspect.cleandoc(
				"""
				import collections
				rawInfo = parent["__udimQuery"]["out"]

				defaultFileName = parent["defaultFileName"]
				defaultResolution = parent["defaultResolution"]

				allMeshes = collections.defaultdict( lambda : [] )
				for udim, meshes in rawInfo.items():
					for mesh, extraAttributes in meshes.items():
						resolution = defaultResolution
						if "bake:resolution" in extraAttributes:
							resolution = extraAttributes["bake:resolution"].value

						fileName = defaultFileName
						if "bake:fileName" in extraAttributes:
							fileName = extraAttributes["bake:fileName"].value

						allMeshes[ (fileName, udim) ].append( { "mesh" : mesh, "resolution" : resolution } )

				fileList = sorted( allMeshes.keys() )

				info = IECore.CompoundObject()

				numTasks = min( parent["tasks"], len( fileList ) )
				taskIndex = parent["taskIndex"]

				if taskIndex < numTasks:

					chunkStart = ( taskIndex * len( fileList ) ) / numTasks
					chunkEnd = ( ( taskIndex + 1 ) * len( fileList ) ) / numTasks

					dupeCount = 0
					prevFileName = ""
					for fileNameTemplate, udim in fileList[chunkStart:chunkEnd]:
						for meshData in allMeshes[(fileNameTemplate, udim)]:
							o = IECore.CompoundObject()
							o["mesh"] = IECore.StringData( meshData["mesh"] )
							o["udim"] = IECore.IntData( int( udim ) )
							o["resolution"] = IECore.IntData( meshData["resolution"] )

							udimStr = str( udim )
							fileName = fileNameTemplate.replace( "<UDIM>", udimStr )

							if fileName == prevFileName:
								dupeCount += 1
								fileName = fileName + ".layer" + str( dupeCount )
							else:
								prevFileName = fileName
								dupeCount = 0

							o["fileName"] = IECore.StringData( fileName )

							name = o["mesh"].value.replace( "/", "_" ) + "." + udimStr
							info[ name ] = o
				parent["__chunkedBakeInfo"] = info

				fileList = []
				for name, i in info.items():
					fileName = i["fileName"].value
					for nameAndAov in parent["aovs"].strip( " " ).split( " " ):
						fileList.append( i["fileName"].value.replace( "<AOV>", nameAndAov.split(":")[0] ) )
				parent["renderFileList"] = IECore.StringVectorData( fileList )
				"""
			), "python" )



			self["__parent"] = GafferScene.Parent()
			self["__parent"]["parent"].setValue( "/" )
			for c in ['bound', 'transform', 'attributes', 'object', 'childNames', 'setNames', 'set']:
				self["__parent"]["in"][c].setInput( self["in"][c] )

			self["__outputExpression"] = Gaffer.Expression()
			self["__outputExpression"].setExpression( inspect.cleandoc(
				"""
				import IECoreScene

				# Transfer all input globals except for outputs
				inGlobals = parent["in"]["globals"]
				outGlobals = IECore.CompoundObject()
				for key, value in inGlobals.items():
					if not key.startswith( "output:" ):
						outGlobals[key] = value

				# Make our own outputs
				info = parent["__chunkedBakeInfo"]
				for cameraName, i in info.items():
					params = IECore.CompoundData()
					fileName = i["fileName"].value
					params["camera"] = IECore.StringData( "/" + parent["cameraGroup"] + "/" + cameraName )
					for nameAndAov in parent["aovs"].strip( " " ).split( " " ):
						tokens = nameAndAov.split( ":" )
						if len( tokens ) != 2:
							raise RuntimeError( "Invalid bake aov specification: %s It should contain a : between name and data." )
						( aovName, aov ) = tokens
						aovFileName = fileName.replace( "<AOV>", aovName )
						outGlobals["output:" + cameraName + "." +  aov] = IECoreScene.Output( aovFileName, "exr", aov + " RGBA", params )
				parent["__parent"]["in"]["globals"] = outGlobals
				"""
			), "python" )

			self["__camera"] = GafferScene.Camera()
			self["__camera"]["projection"].setValue( "orthographic" )

			self["__cameraTweaks"] = GafferScene.CameraTweaks()
			self["__cameraTweaks"]["in"].setInput( self["__camera"]["out"] )
			self["__cameraTweaks"]["tweaks"]["projection"] = GafferScene.TweakPlug( "projection", "uv_camera" )
			self["__cameraTweaks"]["tweaks"]["resolution"] = GafferScene.TweakPlug( "resolution", imath.V2i( 0 ) )
			self["__cameraTweaks"]["tweaks"]["u_offset"] = GafferScene.TweakPlug( "u_offset", 0.0 )
			self["__cameraTweaks"]["tweaks"]["v_offset"] = GafferScene.TweakPlug( "v_offset", 0.0 )
			self["__cameraTweaks"]["tweaks"]["mesh"] = GafferScene.TweakPlug( "mesh", "" )
			self["__cameraTweaks"]["tweaks"]["uv_set"] = GafferScene.TweakPlug( "uv_set", "" )
			self["__cameraTweaks"]["tweaks"]["extend_edges"] = GafferScene.TweakPlug( "extend_edges", False )
			self["__cameraTweaks"]["tweaks"]["offset"] = GafferScene.TweakPlug( "offset", 0.1 )

			self["__cameraTweaks"]["tweaks"]["offset"]["value"].setInput( self["normalOffset"] )

			self["__cameraTweaksFilter"] = GafferScene.PathFilter()
			self["__cameraTweaksFilter"]["paths"].setValue( IECore.StringVectorData( [ '/camera' ] ) )
			self["__cameraTweaks"]["filter"].setInput( self["__cameraTweaksFilter"]["out"] )


			self["__collectScenes"] = GafferScene.CollectScenes()
			self["__collectScenes"]["sourceRoot"].setValue( "/camera" )
			self["__collectScenes"]["rootNameVariable"].setValue( "collect:cameraName" )
			self["__collectScenes"]["in"].setInput( self["__cameraTweaks"]["out"] )

			self["__group"] = GafferScene.Group()
			self["__group"]["in"][0].setInput( self["__collectScenes"]["out"] )
			self["__group"]["name"].setInput( self["cameraGroup"] )

			self["__parent"]["children"][0].setInput( self["__group"]["out"] )

			self["__collectSceneRootsExpression"] = Gaffer.Expression()
			self["__collectSceneRootsExpression"].setExpression( inspect.cleandoc(
				"""
				info = parent["__chunkedBakeInfo"]
				parent["__collectScenes"]["rootNames"] = IECore.StringVectorData( info.keys() )
				"""
			), "python" )

			self["__cameraSetupExpression"] = Gaffer.Expression()
			self["__cameraSetupExpression"].setExpression( inspect.cleandoc(
				"""
				cameraName = context["collect:cameraName"]
				info = parent["__chunkedBakeInfo"]
				i = info[cameraName]
				udimOffset = i["udim"].value - 1001
				parent["__cameraTweaks"]["tweaks"]["resolution"]["value"] = imath.V2i( i["resolution"].value )
				parent["__cameraTweaks"]["tweaks"]["u_offset"]["value"] = -( udimOffset % 10 )
				parent["__cameraTweaks"]["tweaks"]["v_offset"]["value"] = -( udimOffset / 10 )
				parent["__cameraTweaks"]["tweaks"]["mesh"]["value"] = i["mesh"].value
				parent["__cameraTweaks"]["tweaks"]["uv_set"]["value"] = parent["uvSet"] if parent["uvSet"] != "uv" else ""
				"""
			), "python" )

			self["out"].setFlags( Gaffer.Plug.Flags.Serialisable, False )
			self["out"].setInput( self["__parent"]["out"] )

	def __init__( self, name = "ArnoldTextureBake" ) :

		GafferDispatch.TaskNode.__init__( self, name )

		self["in"] = GafferScene.ScenePlug()
		self["filter"] = GafferScene.FilterPlug()
		self["bakeDirectory"] = Gaffer.StringPlug( "bakeDirectory", defaultValue = "" )
		self["defaultFileName"] = Gaffer.StringPlug( "defaultFileName", defaultValue = "${bakeDirectory}/<AOV>/<AOV>.<UDIM>.exr" )
		self["defaultResolution"] = Gaffer.IntPlug( "defaultResolution", defaultValue = 512 )
		self["uvSet"] = Gaffer.StringPlug( "uvSet", defaultValue = 'uv' )
		self["normalOffset"] = Gaffer.FloatPlug( "offset", defaultValue = 0.1 )
		self["aovs"] = Gaffer.StringPlug( "aovs", defaultValue = 'beauty:RGBA' )
		self["tasks"] = Gaffer.IntPlug( "tasks", defaultValue = 1 )
		self["cleanupIntermediateFiles"] = Gaffer.BoolPlug( "cleanupIntermediateFiles", defaultValue = True )

		self["applyMedianFilter"] = Gaffer.BoolPlug( "applyMedianFilter", Gaffer.Plug.Direction.In, False )
		self["medianRadius"] = Gaffer.IntPlug( "medianRadius", Gaffer.Plug.Direction.In, 1 )

		# Set up connection to preTasks beforehand
		self["__PreTaskList"] = GafferDispatch.TaskList()
		self["__PreTaskList"]["preTasks"].setInput( self["preTasks"] )

		self["__CleanPreTasks"] = Gaffer.DeleteContextVariables()
		self["__CleanPreTasks"].setup( GafferDispatch.TaskNode.TaskPlug() )
		self["__CleanPreTasks"]["in"].setInput( self["__PreTaskList"]["task"] )
		self["__CleanPreTasks"]["variables"].setValue( "BAKE_WEDGE:index BAKE_WEDGE:value_unused" )

		# First, setup python commands which will dispatch a chunk of a render or image tasks as
		# immediate execution once they reach the farm - this allows us to run multiple tasks in
		# one farm process.
		self["__RenderDispatcher"] = GafferDispatch.PythonCommand()
		self["__RenderDispatcher"]["preTasks"][0].setInput( self["__CleanPreTasks"]["out"] )
		self["__RenderDispatcher"]["command"].setValue( inspect.cleandoc(
			"""
			import GafferDispatch
			# We need to access frame and "BAKE_WEDGE:index" so that the hash of render varies with the wedge index,
			# so we might as well print what we're doing
			IECore.msg( IECore.MessageHandler.Level.Info, "Bake Process", "Dispatching render task index %i for frame %i" % ( context["BAKE_WEDGE:index"], context.getFrame() ) )
			d = GafferDispatch.LocalDispatcher()
			d.dispatch( [ self.parent()["__bakeDirectoryContext"] ] )
			"""
		) )
		self["__ImageDispatcher"] = GafferDispatch.PythonCommand()
		self["__ImageDispatcher"]["preTasks"][0].setInput( self["__RenderDispatcher"]["task"] )
		self["__ImageDispatcher"]["command"].setValue( inspect.cleandoc(
			"""
			import GafferDispatch
			# We need to access frame and "BAKE_WEDGE:index" so that the hash of render varies with the wedge index,
			# so we might as well print what we're doing
			IECore.msg( IECore.MessageHandler.Level.Info, "Bake Process", "Dispatching image task index %i for frame %i" % ( context["BAKE_WEDGE:index"], context.getFrame() ) )
			d = GafferDispatch.LocalDispatcher()
			d.dispatch( [ self.parent()["__CleanUpSwitch"] ] )
			"""
		) )
		# Connect through the dispatch settings to the render dispatcher
		# ( The image dispatcher runs much quicker, and should be OK using default settings )
		self["__RenderDispatcher"]["dispatcher"].setInput( self["dispatcher"] )

		# Set up variables so the dispatcher knows that the render and image dispatches depend on
		# the file paths ( in case they are varying in a wedge )
		for redispatch in [ self["__RenderDispatcher"], self["__ImageDispatcher"] ]:
			redispatch["variables"].addChild( Gaffer.NameValuePlug( "bakeDirectory", "", "bakeDirectoryVar" ) )
			redispatch["variables"].addChild( Gaffer.NameValuePlug( "defaultFileName", "", "defaultFileNameVar" ) )

		# Connect the variables via an expression so that get expanded ( this also means that
		# if you put #### in a filename you will get per frame tasks, because the hash will depend
		# on frame number )
		self["__DispatchVariableExpression"] = Gaffer.Expression()
		self["__DispatchVariableExpression"].setExpression( inspect.cleandoc(
			"""
			parent["__RenderDispatcher"]["variables"]["bakeDirectoryVar"]["value"] = parent["bakeDirectory"]
			parent["__RenderDispatcher"]["variables"]["defaultFileNameVar"]["value"] = parent["defaultFileName"]
			parent["__ImageDispatcher"]["variables"]["bakeDirectoryVar"]["value"] = parent["bakeDirectory"]
			parent["__ImageDispatcher"]["variables"]["defaultFileNameVar"]["value"] = parent["defaultFileName"]
			"""
		), "python" )

		# Wedge based on tasks into the overall number of tasks to run.  Note that we don't know how
		# much work each task will do until we actually run the render tasks ( this is when scene
		# expansion happens ).  Because we must group all tasks that write to the same file into the
		# same task batch, if tasks is a large number, some tasks batches could end up empty
		self["__MainWedge"] = GafferDispatch.Wedge()
		self["__MainWedge"]["preTasks"][0].setInput( self["__ImageDispatcher"]["task"] )
		self["__MainWedge"]["variable"].setValue( "BAKE_WEDGE:value_unused" )
		self["__MainWedge"]["indexVariable"].setValue( "BAKE_WEDGE:index" )
		self["__MainWedge"]["mode"].setValue( 1 )
		self["__MainWedge"]["intMin"].setValue( 1 )
		self["__MainWedge"]["intMax"].setInput( self["tasks"] )

		self["task"].setInput( self["__MainWedge"]["task"] )
		self["task"].setFlags( Gaffer.Plug.Flags.Serialisable, False )

		# Now set up the render tasks.  This involves doing the actual rendering, and triggering the
		# output of the file list index file.

		# First get rid of options from the upstream scene that could mess up the bake
		self["__OptionOverrides"] = GafferScene.StandardOptions()
		self["__OptionOverrides"]["in"].setInput( self["in"] )
		self["__OptionOverrides"]["options"]["pixelAspectRatio"]["enabled"].setValue( True )
		self["__OptionOverrides"]["options"]["resolutionMultiplier"]["enabled"].setValue( True )
		self["__OptionOverrides"]["options"]["overscan"]["enabled"].setValue( True )
		self["__OptionOverrides"]["options"]["renderCropWindow"]["enabled"].setValue( True )
		self["__OptionOverrides"]["options"]["cameraBlur"]["enabled"].setValue( True )
		self["__OptionOverrides"]["options"]["transformBlur"]["enabled"].setValue( True )
		self["__OptionOverrides"]["options"]["deformationBlur"]["enabled"].setValue( True )

		self["__CameraSetup"] = self.__CameraSetup()
		self["__CameraSetup"]["in"].setInput( self["__OptionOverrides"]["out"] )
		self["__CameraSetup"]["filter"].setInput( self["filter"] )
		self["__CameraSetup"]["defaultFileName"].setInput( self["defaultFileName"] )
		self["__CameraSetup"]["defaultResolution"].setInput( self["defaultResolution"] )
		self["__CameraSetup"]["uvSet"].setInput( self["uvSet"] )
		self["__CameraSetup"]["aovs"].setInput( self["aovs"] )
		self["__CameraSetup"]["normalOffset"].setInput( self["normalOffset"] )
		self["__CameraSetup"]["tasks"].setInput( self["tasks"] )

		self["__Expression"] = Gaffer.Expression()
		self["__Expression"].setExpression( 'parent["__CameraSetup"]["taskIndex"] = context.get( "BAKE_WEDGE:index", 0 )', "python" )

		self["__indexFilePath"] = Gaffer.StringPlug()
		self["__indexFilePath"].setFlags( Gaffer.Plug.Flags.Serialisable, False )
		self["__IndexFileExpression"] = Gaffer.Expression()
		self["__IndexFileExpression"].setExpression( inspect.cleandoc(
			"""
			import os
			parent["__indexFilePath"] = os.path.join( parent["bakeDirectory"], "BAKE_FILE_INDEX_" +
				str( context.get("BAKE_WEDGE:index", 0 ) ) + ".####.txt" )
			"""
		), "python" )

		self["__outputIndexCommand"] = Gaffer.PythonCommand()
		self["__outputIndexCommand"]["variables"].addChild( Gaffer.NameValuePlug( "bakeDirectory", Gaffer.StringPlug() ) )
		self["__outputIndexCommand"]["variables"][0]["value"].setInput( self["bakeDirectory"] )
		self["__outputIndexCommand"]["variables"].addChild( Gaffer.NameValuePlug( "indexFilePath", Gaffer.StringPlug() ) )
		self["__outputIndexCommand"]["variables"][1]["value"].setInput( self["__indexFilePath"] )
		self["__outputIndexCommand"]["variables"].addChild( Gaffer.NameValuePlug( "fileList", Gaffer.StringVectorDataPlug( defaultValue = IECore.StringVectorData() ) ) )
		self["__outputIndexCommand"]["variables"][2]["value"].setInput( self["__CameraSetup"]["renderFileList"] )
		self["__outputIndexCommand"]["command"].setValue( inspect.cleandoc(
			"""
			import os
			import distutils.dir_util

			# Ensure path exists
			distutils.dir_util.mkpath( variables["bakeDirectory"] )

			f = open( variables["indexFilePath"], "w" )

			f.writelines( [ i + "\\n" for i in sorted( variables["fileList"] ) ] )
			f.close()
			IECore.msg( IECore.MessageHandler.Level.Info, "Bake Process", "Wrote list of bake files for this chunk to " + variables["indexFilePath"] )
			"""
		) )

		self["__arnoldRender"] = GafferArnold.ArnoldRender()
		self["__arnoldRender"]["preTasks"][0].setInput( self["__outputIndexCommand"]["task"] )
		self["__arnoldRender"]["dispatcher"]["immediate"].setValue( True )
		self["__arnoldRender"]["in"].setInput( self["__CameraSetup"]["out"] )

		self["__bakeDirectoryContext"] = GafferDispatch.TaskContextVariables()
		self["__bakeDirectoryContext"]["variables"].addChild( Gaffer.NameValuePlug( "bakeDirectory", Gaffer.StringPlug() ) )
		self["__bakeDirectoryContext"]["variables"][0]["value"].setInput( self["bakeDirectory"] )
		self["__bakeDirectoryContext"]["preTasks"][0].setInput( self["__arnoldRender"]["task"] )

		# Now set up the image tasks.  This involves merging all layers for a UDIM, filling in the
		# background, writing out this image, converting it to tx, and optionally deleting all the exrs

		self["__imageList"] = Gaffer.CompoundObjectPlug( "__imageList", defaultValue = IECore.CompoundObject() )
		self["__imageList"].setFlags( Gaffer.Plug.Flags.Serialisable, False )

		self["__ImageReader"] = GafferImage.ImageReader()
		self["__CurInputFileExpression"] = Gaffer.Expression()
		self["__CurInputFileExpression"].setExpression( inspect.cleandoc(
			"""
			l = parent["__imageList"]
			outFile = context["wedge:outFile"]
			loopIndex = context[ "loop:index" ]
			parent["__ImageReader"]["fileName"] = l[outFile][ loopIndex ]
			"""
		), "python" )

		# Find the max size of any input file
		self["__SizeLoop"] = Gaffer.LoopComputeNode()
		self["__SizeLoop"].setup( Gaffer.IntPlug() )

		self["__SizeMaxExpression"] = Gaffer.Expression()
		self["__SizeMaxExpression"].setExpression( inspect.cleandoc(
			"""
			f = parent["__ImageReader"]["out"]["format"]
			parent["__SizeLoop"]["next"] = max( f.width(), parent["__SizeLoop"]["previous"] )
			"""
		), "python" )

		# Loop over all input files for this output file, and merge them all together
		self["__ImageLoop"] = Gaffer.LoopComputeNode()
		self["__ImageLoop"].setup( GafferImage.ImagePlug() )

		self["__NumInputsForCurOutputExpression"] = Gaffer.Expression()
		self["__NumInputsForCurOutputExpression"].setExpression( inspect.cleandoc(
			"""
			l = parent["__imageList"]
			outFile = context["wedge:outFile"]
			numInputs = len( l[outFile] )
			parent["__ImageLoop"]["iterations"] = numInputs
			parent["__SizeLoop"]["iterations"] = numInputs
			"""
		), "python" )

		self["__Resize"] = GafferImage.Resize()
		self["__Resize"]["format"]["displayWindow"]["min"].setValue( imath.V2i( 0, 0 ) )
		self["__Resize"]['format']["displayWindow"]["max"]["x"].setInput( self["__SizeLoop"]["out"] )
		self["__Resize"]['format']["displayWindow"]["max"]["y"].setInput( self["__SizeLoop"]["out"] )
		self["__Resize"]['in'].setInput( self["__ImageReader"]["out"] )

		self["__Merge"] = GafferImage.Merge()
		self["__Merge"]["in"][0].setInput( self["__Resize"]["out"] )
		self["__Merge"]["in"][1].setInput( self["__ImageLoop"]["previous"] )
		self["__Merge"]["operation"].setValue( GafferImage.Merge.Operation.Add )

		self["__ImageLoop"]["next"].setInput( self["__Merge"]["out"] )

		# Write out the combined image, so we can immediately read it back in
		# This is just because we're doing enough image processing that we
		# could saturate the cache, and Gaffer wouldn't know that this is
		# the important result to keep
		self["__ImageIntermediateWriter"] = GafferImage.ImageWriter()
		self["__ImageIntermediateWriter"]["in"].setInput( self["__ImageLoop"]["out"] )

		self["__ImageIntermediateReader"] = GafferImage.ImageReader()

		# Now that we've merged everything together, we can use a BleedFill to fill in the background,
		# so that texture filtering across the edges will pull in colors that are at least reasonable.
		self["__BleedFill"] = GafferImage.BleedFill()
		self["__BleedFill"]["in"].setInput( self["__ImageIntermediateReader"]["out"] )

		self["__Median"] = GafferImage.Median()
		self["__Median"]["in"].setInput( self["__BleedFill"]["out"] )
		self["__Median"]["enabled"].setInput( self["applyMedianFilter"] )
		self["__Median"]["radius"]["x"].setInput( self["medianRadius"] )
		self["__Median"]["radius"]["y"].setInput( self["medianRadius"] )

		# Write out the result
		self["__ImageWriter"] = GafferImage.ImageWriter()
		self["__ImageWriter"]["in"].setInput( self["__Median"]["out"] )
		self["__ImageWriter"]["preTasks"][0].setInput( self["__ImageIntermediateWriter"]["task"] )

		# Convert result to texture
		self["__ConvertCommand"] = GafferDispatch.SystemCommand()
		# We shouldn't need a sub-shell and this prevents S.I.P on the Mac from
		# blocking the dylibs loaded by maketx.
		self["__ConvertCommand"]["shell"].setValue( False )
		self["__ConvertCommand"]["substitutions"].addChild( Gaffer.NameValuePlug( "inFile", IECore.StringData(), "member1" ) )
		self["__ConvertCommand"]["substitutions"].addChild( Gaffer.NameValuePlug( "outFile", IECore.StringData(), "member1" ) )
		self["__ConvertCommand"]["preTasks"][0].setInput( self["__ImageWriter"]["task"] )
		self["__ConvertCommand"]["command"].setValue( 'maketx --wrap clamp {inFile} -o {outFile}' )


		self["__CommandSetupExpression"] = Gaffer.Expression()
		self["__CommandSetupExpression"].setExpression( inspect.cleandoc(
			"""

			outFileBase = context["wedge:outFile"]
			intermediateExr = outFileBase + ".intermediate.exr"
			parent["__ImageIntermediateWriter"]["fileName"] = intermediateExr
			parent["__ImageIntermediateReader"]["fileName"] = intermediateExr
			tmpExr = outFileBase + ".tmp.exr"
			parent["__ImageWriter"]["fileName"] = tmpExr
			parent["__ConvertCommand"]["substitutions"]["member1"]["value"] = tmpExr
			parent["__ConvertCommand"]["substitutions"]["member2"]["value"] = outFileBase + ".tx"
			"""
		), "python" )

		self["__ImageWedge"] = GafferDispatch.Wedge()
		self["__ImageWedge"]["preTasks"][0].setInput( self["__ConvertCommand"]["task"] )
		self["__ImageWedge"]["variable"].setValue( 'wedge:outFile' )
		self["__ImageWedge"]["indexVariable"].setValue( 'wedge:outFileIndex' )
		self["__ImageWedge"]["mode"].setValue( int( Gaffer.Wedge.Mode.StringList ) )

		self["__CleanUpCommand"] = GafferDispatch.PythonCommand()
		self["__CleanUpCommand"]["preTasks"][0].setInput( self["__ImageWedge"]["task"] )
		self["__CleanUpCommand"]["variables"].addChild( Gaffer.NameValuePlug( "filesToDelete", Gaffer.StringVectorDataPlug( defaultValue = IECore.StringVectorData() ), "member1" ) )
		self["__CleanUpCommand"]["command"].setValue( inspect.cleandoc(
			"""
			import os
			for tmpFile in variables["filesToDelete"]:
				os.remove( tmpFile )
			"""
		) )

		self["__CleanUpExpression"] = Gaffer.Expression()
		self["__CleanUpExpression"].setExpression( inspect.cleandoc(
			"""

			imageList = parent["__imageList"]

			toDelete = []
			for outFileBase, inputExrs in imageList.items():
				tmpExr = outFileBase + ".tmp.exr"
				intermediateExr = outFileBase + ".intermediate.exr"
				toDelete.extend( inputExrs )
				toDelete.append( tmpExr )
				toDelete.append( intermediateExr )
			toDelete.append( parent["__indexFilePath"] )

			parent["__CleanUpCommand"]["variables"]["member1"]["value"] = IECore.StringVectorData( toDelete )
			"""
		), "python" )

		self["__CleanUpSwitch"] = GafferDispatch.TaskSwitch()
		self["__CleanUpSwitch"]["preTasks"][0].setInput( self["__ImageWedge"]["task"] )
		self["__CleanUpSwitch"]["preTasks"][1].setInput( self["__CleanUpCommand"]["task"] )
		self["__CleanUpSwitch"]["index"].setInput( self["cleanupIntermediateFiles"] )

		# Set up the list of input image files to process, and the corresponding list of
		# output files to wedge over
		self["__ImageSetupExpression"] = Gaffer.Expression()
		self["__ImageSetupExpression"].setExpression( inspect.cleandoc(
			"""
			f = open( parent["__indexFilePath"], "r" )

			fileList = f.read().splitlines()
			fileDict = {}
			for i in fileList:
				rootName = i.rsplit( ".exr", 1 )[0]
				if rootName in fileDict:
					fileDict[ rootName ].append( i )
				else:
					fileDict[ rootName ] = IECore.StringVectorData( [i] )
			parent["__imageList"] = IECore.CompoundObject( fileDict )

			parent["__ImageWedge"]["strings"] = IECore.StringVectorData( fileDict.keys() )
			"""
		), "python" )




IECore.registerRunTimeTyped( ArnoldTextureBake, typeName = "GafferArnold::ArnoldTextureBake" )

