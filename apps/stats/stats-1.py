##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
import gc
import sys
import time
import tempfile
import resource
import collections
import six

import IECore

import Gaffer

class stats( Gaffer.Application ) :

	def __init__( self ) :

		Gaffer.Application.__init__(
			self,
			"""
			Outputs statistics about a Gaffer script, including the version of
			Gaffer that created it, the values of all setting and variables and
			the types of node in use. May also be used to perform performance
			analysis of image and scene processing nodes within the script, using
			a performance monitor to generate advanced statistics.

			To output basic information about a script :

			```
			gaffer stats fileName.gfr
			```

			To run a scene processing node using the performance monitor :

			```
			gaffer stats fileName.gfr -scene NameOfNode -performanceMonitor
			```

			To run an image processing node using the performance monitor :

			```
			gaffer stats fileName.gfr -image NameOfNode -performanceMonitor
			```
			"""
		)

		self.parameters().addParameters(

			[
				IECore.FileNameParameter(
					name = "script",
					description = "The script to examine.",
					defaultValue = "",
					allowEmptyString = False,
					extensions = "gfr",
					check = IECore.FileNameParameter.CheckType.MustExist,
				),

				IECore.FileNameParameter(
					name = "postLoadScript",
					description = "A python script to run after loading `script`. This "
						"can be used to modify the node graph before stats are gathered. "
						"The root ScriptNode is accessible via a variable named `root`.",
					defaultValue = "",
					allowEmptyString = True,
					extensions = "py",
					check = IECore.FileNameParameter.CheckType.MustExist,
				),

				IECore.FileNameParameter(
					name = "outputFile",
					description = "Output the results to this file on disk rather than stdout",
					defaultValue = "",
					allowEmptyString = True,
					extensions = "",
				),

				IECore.FrameListParameter(
					name = "frames",
					description = "The frames to evaluate statistics for. The default value "
						"uses the current frame as stored in the script.",
					defaultValue = "",
					allowEmptyList = True,
				),

				IECore.BoolParameter(
					name = "nodeSummary",
					description = "Turns on a summary of nodes in the script.",
					defaultValue = True,
				),

				IECore.StringParameter(
					name = "scene",
					description = "The name of a SceneNode or ScenePlug to examine. "
						"A Render node or TaskPlug on a Render node may also be passed, "
						"to perform profiling of the render output process without "
						"performing the actual image generation.",
					defaultValue = "",
				),

				IECore.StringParameter(
					name = "location",
					description = "The path to a location in the scene. If this is specified "
						"then that single location will be generated profiled, otherwise "
						"the entire scene will generated.",
					defaultValue = "",
				),

				IECore.StringVectorParameter(
					name = "sets",
					description = "The names of scene sets to be examined.",
					defaultValue = IECore.StringVectorData(),
				),

				IECore.StringParameter(
					name = "image",
					description = "The name of an ImageNode or ImagePlug to examine.",
					defaultValue = "",
				),

				IECore.BoolParameter(
					name = "preCache",
					description = "Prepopulates the cache by evaluating the scene or image "
						"once prior to measuring the second evaluation.",
					defaultValue = False,
				),

				IECore.StringParameter(
					name = "task",
					description = "The name of a TaskNode or TaskPlug to dispatch.",
					defaultValue = "",
				),

				IECore.BoolParameter(
					name = "performanceMonitor",
					description = "Turns on a performance monitor to provide additional "
						"statistics about the operation of the node graph.",
					defaultValue = False,
				),

				IECore.IntParameter(
					name = "maxLinesPerMetric",
					description = "The maximum number of plugs to list for each metric "
						"captured by the performance monitor.",
					defaultValue = 50,
				),

				IECore.BoolParameter(
					name = "contextMonitor",
					description = "Turns on a Context monitor to provide additional "
						"statistics about the operation of the node graph.",
					defaultValue = False,
				),

				IECore.StringParameter(
					name = "contextMonitorRoot",
					description = "The name of a node or plug to provide a root for the "
						"Context monitor. Statistics will only be captured for this root "
						"downwards.",
					defaultValue = "",
				),

				IECore.FileNameParameter(
					name = "annotatedScript",
					description = "Filename used to save a copy of the script containing "
						"annotations from the performance and Context monitors.",
					defaultValue = "",
					allowEmptyString = True,
					extensions = "gfr",
				),

				IECore.BoolParameter(
					name = "vtune",
					description = "Enables VTune instrumentation. When enabled, the VTune "
						"'Tasks & Frames' view will be broken down by node type.",
					defaultValue = False,
				),

				IECore.BoolParameter(
					name = "contextSanitiser",
					description = "Checks for Contexts containing \"leaked\" variables that "
						"may affect performance. Any problems are reported as warnings to "
						"stderr.",
					defaultValue = False,
				),

				IECore.BoolParameter(
					name = "canceller",
					description = "Adds an IECore.Canceller to the Context used for computations. "
						"This can be used to measure any overhead generated by nodes checking for "
						"cancellation.",
					defaultValue = False
				),

				IECore.IntParameter(
					name = "cacheMemoryLimit",
					description = "The memory limit for the ValuePlug cache, measured in Mb. "
						"If this is not specified, the default limit will be used, or a limit "
						"specified by an application startup file.",
					defaultValue = 0,
				),

				IECore.IntParameter(
					name = "hashCacheSizeLimit",
					description = "The size limit for the per-thread hash cache. If this is not "
						"specified, the default limit will be used, or a limit specified by an "
						"application startup file.",
					defaultValue = 0,
				),

			]

		)

		self.parameters().userData()["parser"] = IECore.CompoundObject(
			{
				"flagless" : IECore.StringVectorData( [ "script" ] )
			}
		)

	def _run( self, args ) :

		if args["cacheMemoryLimit"].value :
			Gaffer.ValuePlug.setCacheMemoryLimit( 1024 * 1024 * args["cacheMemoryLimit"].value )
		if args["hashCacheSizeLimit"].value :
			Gaffer.ValuePlug.setHashCacheSizeLimit( args["hashCacheSizeLimit"].value )

		self.__timers = collections.OrderedDict()
		self.__memory = collections.OrderedDict()

		self.__memory["Application"] = _Memory.maxRSS()

		script = Gaffer.ScriptNode()
		script["fileName"].setValue( os.path.abspath( args["script"].value ) )

		with _Timer() as loadingTimer :
			script.load( continueOnError = True )
		self.__timers["Loading"] = loadingTimer

		self.root()["scripts"].addChild( script )

		self.__memory["Script"] = _Memory.maxRSS() - self.__memory["Application"]

		if args["postLoadScript"].value :
			postLoadScriptExecutionContext = { "root" : script }
			with Gaffer.DirtyPropagationScope() :
				exec(
					compile( open( args["postLoadScript"].value ).read(), args["postLoadScript"].value, "exec" ),
					postLoadScriptExecutionContext, postLoadScriptExecutionContext
				)

		if args["performanceMonitor"].value :
			self.__performanceMonitor = Gaffer.PerformanceMonitor()
		else :
			self.__performanceMonitor = None

		if args["contextMonitor"].value :
			contextMonitorRoot = None
			if args["contextMonitorRoot"].value :
				contextMonitorRoot = script.descendant( args["contextMonitorRoot"].value )
				if contextMonitorRoot is None :
					IECore.msg( IECore.Msg.Level.Error, "stats", "Context monitor root \"%s\" does not exist" % args["contextMonitorRoot"].value )
					return 1
			self.__contextMonitor = Gaffer.ContextMonitor( contextMonitorRoot )
		else :
			self.__contextMonitor = None

		if args["vtune"].value :
			try:
				self.__vtuneMonitor = Gaffer.VTuneMonitor()
			except AttributeError:
				self.__vtuneMonitor = None
				IECore.msg( IECore.Msg.Level.Error, "gui", "unable to create requested VTune monitor" )
		else :
			self.__vtuneMonitor = None

		self.__output = open( args["outputFile"].value, "w" ) if args["outputFile"].value else sys.stdout

		self.__writeVersion( script )

		self.__output.write( "\n" )

		self.__writeArgs( args )

		self.__output.write( "\n" )

		self.__writeSettings( script )

		self.__output.write( "\n" )

		self.__writeVariables( script )

		self.__output.write( "\n" )

		if args["nodeSummary"].value :

			self.__writeNodes( script )

		if args["scene"].value :

			self.__writeScene( script, args )

		if args["image"].value :

			self.__writeImage( script, args )

		if args["task"].value :

			self.__writeTask( script, args )

		self.__output.write( "\n" )

		self.__writeMemory()

		self.__output.write( "\n" )

		self.__writePerformance( script, args )

		self.__output.write( "\n" )

		self.__writeContext( script, args )

		self.__output.write( "\n" )

		self.__output.close()

		if args["annotatedScript"].value :

			if self.__performanceMonitor is not None :
				Gaffer.MonitorAlgo.annotate( script, self.__performanceMonitor, Gaffer.MonitorAlgo.PerformanceMetric.TotalDuration )
				Gaffer.MonitorAlgo.annotate( script, self.__performanceMonitor, Gaffer.MonitorAlgo.PerformanceMetric.HashCount )
				Gaffer.MonitorAlgo.annotate( script, self.__performanceMonitor, Gaffer.MonitorAlgo.PerformanceMetric.ComputeCount )
			if self.__contextMonitor is not None :
				Gaffer.MonitorAlgo.annotate( script, self.__contextMonitor )

			script.serialiseToFile( args["annotatedScript"].value )

		return 0

	def __writeVersion( self, script ) :

		numbers = [ Gaffer.Metadata.value( script, "serialiser:" + x + "Version" ) for x in ( "milestone", "major", "minor", "patch" ) ]
		if None not in numbers :
			version = ".".join( str( x ) for x in numbers )
		else :
			version = "unknown"

		versions = (
			( "Script", version ),
			( "Current", Gaffer.About.versionString() ),
		)

		self.__output.write( "Gaffer Version :\n\n" )
		self.__writeItems( versions )

	def __writeItems( self, items ) :

		if not len( items ) :
			return

		width = max( [ len( x[0] ) for x in items ] ) + 4
		for name, value in items :
			self.__output.write( "  {name:<{width}}{value}\n".format( name = name, width = width, value = value ) )

	def __writeArgs( self, args ) :

		self.__output.write( "Args :\n\n" )
		self.__writeItems( sorted( args.items() ) )

	def __writeSettings( self, script ) :

		plugsToIgnore = {
			script["fileName"],
			script["unsavedChanges"],
			script["variables"],
		}

		items = []
		def itemsWalk( p ) :

			if p in plugsToIgnore :
				return

			if hasattr( p, "getValue" ) :
				items.append( ( p.relativeName( script ), p.getValue() ) )
			else :
				for c in p.children( Gaffer.Plug ) :
					itemsWalk( c )

		itemsWalk( script )

		self.__output.write( "Settings :\n\n" )
		self.__writeItems( items )

	def __writeVariables( self, script ) :

		items = []
		for p in script["variables"] :
			data, name = script["variables"].memberDataAndName( p )
			if data is not None :
				items.append( ( name, data ) )

		self.__output.write( "Variables :\n\n" )
		self.__writeItems( items )

	def __writeNodes( self, script ) :

		counter = collections.Counter()
		for node in Gaffer.Node.RecursiveRange( script ) :
			counter[node.typeName()] += 1

		items = [ ( nodeType.rpartition( ":" )[2], count ) for nodeType, count in counter.most_common() ]
		items.extend( [
			( "", "" ),
			( "Total", sum( counter.values() ) ),
		] )

		self.__output.write( "Nodes :\n\n" )
		self.__writeItems( items )

	def __context( self, script, args ) :

		if args["canceller"].value :
			self.__canceller = IECore.Canceller()
			return Gaffer.Context( script.context(), self.__canceller )
		else :
			return Gaffer.Context( script.context() )

	def __frames( self, script, args ) :

		frames = self.parameters()["frames"].getFrameListValue().asList()
		if not frames :
			frames = [ script.context().getFrame() ]

		return frames

	def __writeScene( self, script, args ) :

		import GafferDispatch
		import GafferScene
		import GafferSceneTest

		scene = script.descendant( args["scene"].value )
		if isinstance( scene, GafferScene.Render ) :
			scene = scene["task"]
		elif isinstance( scene, Gaffer.Node ) :
			scene = next( GafferScene.ScenePlug.RecursiveOutputRange( scene ), None )

		if scene is None :
			IECore.msg( IECore.Msg.Level.Error, "stats", "Scene \"%s\" does not exist" % args["scene"].value )
			return

		contextSanitiser = _NullContextManager()
		if args["contextSanitiser"].value :
			contextSanitiser = GafferSceneTest.ContextSanitiser()

		def computeScene() :

			with self.__context( script, args ) as context :
				for frame in self.__frames( script, args ) :
					context.setFrame( frame )

					if isinstance( scene, GafferDispatch.TaskNode.TaskPlug ) :
						if args["location"].value :
							IECore.msg( IECore.Msg.Level.Warning, "stats", "`-location` argument is not compatible with TaskPlugs" )
						context["scene:render:sceneTranslationOnly"] = IECore.BoolData( True )
						scene.execute()
					else :
						if args["sets"] :
							GafferScene.SceneAlgo.sets( scene, args["sets"] )
						else :
							if args["location"].value :
								scene.transform( args["location"].value )
								scene.bound( args["location"].value )
								scene.attributes( args["location"].value )
								scene.object( args["location"].value )
							else :
								GafferSceneTest.traverseScene( scene )

		if args["preCache"].value :
			computeScene()

		memory = _Memory.maxRSS()
		with _Timer() as sceneTimer :
			with self.__performanceMonitor or _NullContextManager(), self.__contextMonitor or _NullContextManager(), self.__vtuneMonitor or _NullContextManager() :
				with contextSanitiser :
					computeScene()

		self.__timers["Scene generation"] = sceneTimer
		self.__memory["Scene generation"] = _Memory.maxRSS() - memory

		## \todo Calculate and write scene stats
		#  - Locations
		#  - Unique objects, attributes etc

	def __writeImage( self, script, args ) :

		import GafferImage
		import GafferImageTest

		image = script.descendant( args["image"].value )
		if isinstance( image, Gaffer.Node ) :
			image = next( GafferImage.ImagePlug.RecursiveOutputRange( image ), None )

		if image is None :
			IECore.msg( IECore.Msg.Level.Error, "stats", "Image \"%s\" does not exist" % args["image"].value )
			return

		contextSanitiser = _NullContextManager()
		if args["contextSanitiser"].value :
			contextSanitiser = GafferImageTest.ContextSanitiser()

		def computeImage() :

			with self.__context( script, args ) as context :
				for frame in self.__frames( script, args ) :
					context.setFrame( frame )
					GafferImageTest.processTiles( image )

		if args["preCache"].value :
			computeImage()

		memory = _Memory.maxRSS()
		with _Timer() as imageTimer :
			with self.__performanceMonitor or _NullContextManager(), self.__contextMonitor or _NullContextManager(), self.__vtuneMonitor or _NullContextManager() :
				with contextSanitiser :
					computeImage()

		self.__timers["Image generation"] = imageTimer
		self.__memory["Image generation"] = _Memory.maxRSS() - memory

		with self.__context( script, args ) as context :
			items = [
				( "Format", image["format"].getValue() ),
				( "Data window", image["dataWindow"].getValue() ),
				( "Channel names", image["channelNames"].getValue() ),
			]

		self.__output.write( "\nImage :\n\n" )
		self.__writeItems( items )

	def __writeTask( self, script, args ) :

		import GafferDispatch

		task = script.descendant( args["task"].value )
		if isinstance( task, GafferDispatch.TaskNode.TaskPlug ) :
			task = task.node()

		if task is None :
			IECore.msg( IECore.Msg.Level.Error, "stats", "Task \"%s\" does not exist" % args["task"].value )
			return

		dispatcher = GafferDispatch.LocalDispatcher()
		dispatcher["jobsDirectory"].setValue( tempfile.mkdtemp( prefix = "gafferStats" ) )

		memory = _Memory.maxRSS()
		with _Timer() as taskTimer :
			with self.__performanceMonitor or _NullContextManager(), self.__contextMonitor or _NullContextManager(), self.__vtuneMonitor or _NullContextManager() :
				with Gaffer.Context( script.context() ) as context :
					for frame in self.__frames( script, args ) :
						context.setFrame( frame )
						dispatcher.dispatch( [ task ] )

		self.__timers["Task execution"] = taskTimer
		self.__memory["Task execution"] = _Memory.maxRSS() - memory

	def __writeMemory( self ) :

		objectPool = IECore.ObjectPool.defaultObjectPool()

		items = list( self.__memory.items() )

		items.extend( [
			( "", "" ),
			( "Cache limit", _Memory( Gaffer.ValuePlug.getCacheMemoryLimit() ) ),
			( "Cache usage", _Memory( Gaffer.ValuePlug.cacheMemoryUsage() ) ),
			( "", "" ),
			( "Object pool limit", _Memory( objectPool.getMaxMemoryUsage() ) ),
			( "Object pool usage", _Memory( objectPool.memoryUsage() ) ),
		] )

		import IECoreScene
		if "IECoreScene" in sys.modules :
			items.extend( [
				( "", "" ),
				( "Scene interface limit", IECoreScene.SharedSceneInterfaces.getMaxScenes() ),
				( "Scene interfaces", IECoreScene.SharedSceneInterfaces.numScenes() ),
			] )

		items.extend( [
			( "", "" ),
			( "Max resident size", _Memory.maxRSS() ),
		] )

		self.__output.write( "Memory :\n\n" )
		self.__writeItems( items )

	def __writeStatisticsItems( self, script, stats, key, n ) :

		stats.sort( key = key, reverse = True )
		items = [ ( x[0].relativeName( script ), key( x ) ) for x in stats[:n] ]
		self.__writeItems( items )

	def __writePerformance( self, script, args ) :

			self.__output.write( "Performance :\n\n" )
			self.__writeItems( self.__timers.items() )

			if self.__performanceMonitor is not None :
				self.__output.write(
					"\n" + Gaffer.MonitorAlgo.formatStatistics(
						self.__performanceMonitor,
						maxLinesPerMetric = args["maxLinesPerMetric"].value
					)
				)

	def __writeContext( self, script, args ) :

			if self.__contextMonitor is None :
				return

			self.__output.write( "Contexts :\n\n" )

			stats = self.__contextMonitor.combinedStatistics()

			items = [ ( n, stats.numUniqueValues( n ) ) for n in stats.variableNames() ]
			items += [
				( "", "" ),
				( "Unique contexts", stats.numUniqueContexts() ),
			]

			self.__writeItems( items )

class _Timer( object ) :

	if six.PY3 :
		__cpuClock = time.process_time
	else :
		__cpuClock = time.clock

	def __enter__( self ) :

		self.__time = time.time()
		self.__cpuTime = self.__cpuClock()

		return self

	def __exit__( self, type, value, traceBack ) :

		self.__time = time.time() - self.__time
		self.__cpuTime = self.__cpuClock() - self.__cpuTime

	def __str__( self ) :

		return "%.3fs (wall), %.3fs (CPU)" % ( self.__time, self.__cpuTime )

class _Memory( object ) :

	def __init__( self, bytes ) :

		self.__bytes = bytes

	@classmethod
	def maxRSS( cls ) :

		if sys.platform == "darwin" :
			return cls( resource.getrusage( resource.RUSAGE_SELF ).ru_maxrss )
		else :
			return cls( resource.getrusage( resource.RUSAGE_SELF ).ru_maxrss * 1024 )

	def __str__( self ) :

		return "%.3fM" % ( self.__bytes / ( 1024 * 1024. ) )

	def __sub__( self, other ) :

		return _Memory( self.__bytes - other.__bytes )

class _NullContextManager( object ) :

	def __enter__( self ) :

		pass

	def __exit__( self, type, value, traceBack ) :

		pass

IECore.registerRunTimeTyped( stats )
