##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
import warnings

import IECore

import Gaffer
import GafferDispatch

# Before Dispatchers were inherited from TaskNode, they had a `dispatch()`
# method that was used to dispatch tasks from a list of nodes. Emulate
# that by making connections and calling `execute()`.

def __dispatch( self, nodes ) :

	for plug in self["tasks"] :
		plug.setInput( None )

	for node in nodes :
		if isinstance( node, GafferDispatch.TaskNode ) :
			self["tasks"].next().setInput( node["task"] )
		elif isinstance( node, Gaffer.SubGraph ) :
			for plug in GafferDispatch.TaskNode.TaskPlug.RecursiveOutputRange( node ) :
				if isinstance( plug.source().node(), GafferDispatch.TaskNode ) :
					self["tasks"].next().setInput( plug )
		else :
			raise IECore.Exception( "Dispatched nodes must be TaskNodes or SubGraphs containing TaskNodes" )

	self["task"].execute()

GafferDispatch.Dispatcher.dispatch = __dispatch

# When the `dispatch()` method existed, the nodes being dispatched needed to be
# passed to the dispatch signals as they were not discoverable any other way.
# But now they are available from connections to the `Dispatcher.tasks` plugs so
# it makes no sense to pass them. But we provide backwards compatibility for
# old-style slots to aid the transition.

def __slotWrapper( slot, numArgs ) :

	signature = inspect.signature( slot )
	dummyArgs = [ None ] * numArgs
	try :
		# Throws if not callable with numArgs
		signature.bind( *dummyArgs )
		# No need for a wrapper
		return slot
	except TypeError :
		pass

	# We'll need a wrapper

	warnings.warn(
		'The `nodes` argument to Dispatcher signals is deprecated. Use `dispatcher["tasks"]` instead.',
		DeprecationWarning
	)

	def call( dispatcher, *args ) :

		nodes = [ task.source().node() for task in dispatcher["tasks"] if task.getInput() is not None ]
		slot( dispatcher, nodes, *args )

	return call

def __connectWrapper( originalConnect, numArgs ) :

	def connect( signal, slot, scoped = None ) :

		return originalConnect( signal, __slotWrapper( slot, numArgs ), scoped )

	return connect

GafferDispatch.Dispatcher.PreDispatchSignal.connect = __connectWrapper( GafferDispatch.Dispatcher.PreDispatchSignal.connect, 1 )
GafferDispatch.Dispatcher.PreDispatchSignal.connectFront = __connectWrapper( GafferDispatch.Dispatcher.PreDispatchSignal.connectFront, 1 )
GafferDispatch.Dispatcher.DispatchSignal.connect = __connectWrapper( GafferDispatch.Dispatcher.DispatchSignal.connect, 1 )
GafferDispatch.Dispatcher.DispatchSignal.connectFront = __connectWrapper( GafferDispatch.Dispatcher.DispatchSignal.connectFront, 1 )
GafferDispatch.Dispatcher.PostDispatchSignal.connect = __connectWrapper( GafferDispatch.Dispatcher.PostDispatchSignal.connect, 2 )
GafferDispatch.Dispatcher.PostDispatchSignal.connectFront = __connectWrapper( GafferDispatch.Dispatcher.PostDispatchSignal.connectFront, 2 )
