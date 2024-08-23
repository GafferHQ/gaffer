##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferDispatch

## Builds a box containing a node graph that represents the
#  batch tree being dispatched. Useful for debugging dispatcher
#  internals. To use it, `import GafferDispatchTest` before opening
#  the dispatcher window, and then select "Debug" in the dispatcher
#  chooser.
class DebugDispatcher( GafferDispatch.Dispatcher ) :

	def __init__( self ) :

		GafferDispatch.Dispatcher.__init__( self )

	def _doDispatch( self, rootBatch ) :

		scriptNode = rootBatch.preTasks()[0].node().scriptNode()
		box = Gaffer.Box( self["jobName"].getValue() or "debug" )
		scriptNode.addChild( box )

		dispatchData = {
			"scriptNode" : scriptNode,
			"box" : box,
			"batchesToNodes" : {},
		}

		box["Root"] = self.__createNode( "Root" )

		for upstreamBatch in rootBatch.preTasks() :
			self.__buildGraphWalk( box["Root"], upstreamBatch, dispatchData )

	def __buildGraphWalk( self, parentNode, batch, dispatchData ) :

		node = self.__acquireNode( batch, dispatchData )
		parentNode["preTasks"][-1].setInput( node["task"] )

		if batch.blindData().get( "debugDispatcher:visited" ) :
			return

		for upstreamBatch in batch.preTasks() :
			self.__buildGraphWalk( node, upstreamBatch, dispatchData )

		batch.blindData()["debugDispatcher:visited"] = IECore.BoolData( True )

	def __acquireNode( self, batch, dispatchData ) :

		node = dispatchData["batchesToNodes"].get( batch )
		if node is not None :
			return node

		nodeName = batch.node().relativeName( dispatchData["scriptNode"] )

		node = self.__createNode( nodeName + "_" + batch.context().hash().toString()[:8] )
		dispatchData["box"].addChild( node )

		node["node"].setValue( nodeName )
		node["frames"].setValue( str( IECore.frameListFromList( [ int( x ) for x in batch.frames() ] ) ) )

		scriptContext = dispatchData["scriptNode"].context()
		contextArgs = []
		for entry in [ k for k in batch.context().keys() if k != "frame" and not k.startswith( "ui:" ) and not k.startswith( "dispatcher:" ) ] :
			if entry not in scriptContext.keys() or batch.context()[entry] != scriptContext[entry] :
				contextArgs.extend( [ "-" + entry, repr( batch.context()[entry] ) ] )

		node["context"].setValue( " ".join( contextArgs ) )

		dispatchData["batchesToNodes"][batch] = node
		return node

	@staticmethod
	def __createNode( name ) :

		node = Gaffer.Node()
		node.setName( name.replace( ".", "_" ) )

		node["preTasks"] = Gaffer.ArrayPlug( elementPrototype = Gaffer.Plug( "preTask0" ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		node["task"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		node["node"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		node["frames"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		node["context"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		Gaffer.Metadata.registerValue( node["preTasks"], "nodule:type", "GafferUI::CompoundNodule" )
		for n in "node", "frames", "context" :
			Gaffer.Metadata.registerValue( node[n], "nodule:type", "" )

		return node

IECore.registerRunTimeTyped( DebugDispatcher )

GafferDispatch.Dispatcher.registerDispatcher( "Debug", DebugDispatcher )
