##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Image Engine Design Inc nor the names of
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

import Gaffer
import GafferDispatch

class GraphvizDispatcher( GafferDispatch.Dispatcher ) :

	def __init__( self, name = "GraphvizDispatcher" ) :

		GafferDispatch.Dispatcher.__init__( self, name )

		self["fileName"] = Gaffer.StringPlug()
		self["includeFrames"] = Gaffer.BoolPlug( defaultValue = True )
		self["contextVariables"] = Gaffer.StringPlug()

	def __walkBatches( self, batch, outFile, scriptNode ) :

		if "id" in batch.blindData() :
			return

		nodeName = batch.plug().node().relativeName( scriptNode ) if batch.plug() is not None else "<root>"
		nodeType = batch.plug().node().typeName() if batch.plug() is not None else "None"
		batch.blindData()["id"] = (
			nodeName + batch.context().hash().toString()
		) if batch.context() is not None else IECore.MurmurHash().toString()

		frameString = None
		if self["includeFrames"].getValue() :
			frameString = "-"
			frameList = IECore.frameListFromList( [ int( i ) for i in batch.frames() ] )
			if len( frameList.asList() ) > 0 :
				if frameList.start == frameList.end :
					frameString = str( frameList.start )
				elif frameList.step != 1 :
					frameString = "{} - {} x {}".format( frameList.start, frameList.end, frameList.step )
				else :
					frameString = "{} - {}".format( frameList.start, frameList.end )

		contextVariables = {}

		if batch.context() is not None :
			scriptContext = scriptNode.context()
			matchPattern = self["contextVariables"].getValue()
			for entry in [ k for k in batch.context().keys() if k != "frame" and not k.startswith( "ui:" ) and not k.startswith( "dispatcher:" ) ] :
				if IECore.StringAlgo.matchMultiple( entry, matchPattern ) and ( entry not in scriptContext.keys() or batch.context()[entry] != scriptContext[entry] ) :
					contextVariables[entry] = batch.context().substitute( str( batch.context()[entry] ) )

		batchString = '\t"{}" [label="{}\n\t\t{}'.format( batch.blindData()["id"], nodeName, nodeType )
		if frameString is not None :
			batchString += "\n\t\t{}".format( frameString )
		if len( contextVariables ) > 0 :
			batchString += "\n\t\t" + "\n\t\t".join(
				[ "{} = {}".format( k, v ) for k, v in contextVariables.items() ]
			)

		batchString += '"];\n'
		outFile.write( batchString )

		for preTask in batch.preTasks() :
			self.__walkBatches( preTask, outFile, scriptNode )

			outFile.write(
				'\t"{}"->"{}";\n'.format( preTask.blindData()["id"], batch.blindData()["id"] )
			)

	def _doDispatch( self, rootBatch ) :

		jobName = self["jobName"].getValue()
		fileName = self["fileName"].getValue()

		scriptNode = rootBatch.preTasks()[0].node().scriptNode()

		with open( fileName, "w" ) as outFile :
			outFile.write( "strict digraph {} {{\n".format( jobName ) )
			self.__walkBatches( rootBatch, outFile, scriptNode )
			outFile.write( "}" )

IECore.registerRunTimeTyped( GraphvizDispatcher, typeName = "GafferDispatch::GraphvizDispatcher" )
GafferDispatch.Dispatcher.registerDispatcher( "Graphviz", GraphvizDispatcher )

Gaffer.Metadata.registerNode(

	GraphvizDispatcher,

	"description",
	"""
	Creates a file in Graphviz DOT language representing dependency graph
	of the batches being dispatched.
	""",

	plugs = {

		"fileName" : [

			"description",
			"""
			The name of DOT language file to save.
			""",

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"path:leaf", True,

		],

		"includeFrames" : [

			"description",
			"""
			Whether or not to include frame ranges in the task description.
			""",

		],

		"contextVariables" : [

			"description",
			"""
			The names of context variables to include in the batch description.
			Names should be separated by spaces and can use Gaffer's standard wildcards.
			""",

		],

	}

)
