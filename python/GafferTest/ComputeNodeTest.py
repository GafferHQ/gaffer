##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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
import unittest
import threading
import time
import six

import IECore

import Gaffer
import GafferTest

class ComputeNodeTest( GafferTest.TestCase ) :

	def testOperation( self ) :

		n1 = GafferTest.AddNode()
		n1["sum"].getValue()

		dirtiedPlugs = GafferTest.CapturingSlot( n1.plugDirtiedSignal() )
		setPlugs = GafferTest.CapturingSlot( n1.plugSetSignal() )

		n1["op1"].setValue( 2 )
		self.assertEqual( len( setPlugs ), 1 )
		self.assertEqual( len( dirtiedPlugs ), 2 )
		self.assertEqual( setPlugs[0][0].fullName(), "AddNode.op1" )
		self.assertEqual( dirtiedPlugs[0][0].fullName(), "AddNode.op1" )
		self.assertEqual( dirtiedPlugs[1][0].fullName(), "AddNode.sum" )

		n1["op2"].setValue( 3 )
		self.assertEqual( len( setPlugs ), 2 )
		self.assertEqual( setPlugs[1][0].fullName(), "AddNode.op2" )

		del dirtiedPlugs[:]
		del setPlugs[:]

		# plug set or dirty signals are not emitted during computation
		self.assertEqual( n1.getChild("sum").getValue(), 5 )
		self.assertEqual( len( setPlugs ), 0 )
		self.assertEqual( len( dirtiedPlugs ), 0 )

		# connect another add node onto the output of this one

		n2 = GafferTest.AddNode( "Add2" )

		dirtiedPlugs2 = GafferTest.CapturingSlot( n2.plugDirtiedSignal() )
		setPlugs2 = GafferTest.CapturingSlot( n2.plugSetSignal() )

		n2["op1"].setInput( n1["sum"] )
		# connecting a plug doesn't set the value of the input plug
		# immediately - the value is transferred only upon request.
		self.assertEqual( len( setPlugs2 ), 0 )
		self.assertEqual( len( dirtiedPlugs2 ), 2 )
		self.assertEqual( dirtiedPlugs2[0][0].fullName(), "Add2.op1" )
		self.assertEqual( dirtiedPlugs2[1][0].fullName(), "Add2.sum" )

		del dirtiedPlugs2[:]
		del setPlugs2[:]

		self.assertEqual( n2["op1"].getValue(), 5 )
		self.assertEqual( n2["sum"].getValue(), 5 )

		# plug set or dirty signals are not emitted during computation
		self.assertEqual( len( setPlugs2 ), 0 )
		self.assertEqual( len( dirtiedPlugs2 ), 0 )

	def testDirtyOfInputsWithConnections( self ) :

		n1 = GafferTest.AddNode( "n1" )
		n2 = GafferTest.AddNode( "n2" )

		dirtied = GafferTest.CapturingSlot( n1.plugDirtiedSignal(), n2.plugDirtiedSignal() )

		n2["op1"].setInput( n1["sum"] )
		self.assertEqual( len( dirtied ), 2 )
		self.assertTrue( dirtied[0][0].isSame( n2["op1"] ) )
		self.assertTrue( dirtied[1][0].isSame( n2["sum"] ) )

		del dirtied[:]
		n1["op1"].setValue( 10 )
		self.assertEqual( len( dirtied ), 4 )
		self.assertTrue( dirtied[0][0].isSame( n1["op1"] ) )
		self.assertTrue( dirtied[1][0].isSame( n1["sum"] ) )
		self.assertTrue( dirtied[2][0].isSame( n2["op1"] ) )
		self.assertTrue( dirtied[3][0].isSame( n2["sum"] ) )

		self.assertEqual( n2.getChild( "sum" ).getValue(), 10 )

	def testDirtyPlugComputesSameValueAsBefore( self ) :

		n1 = GafferTest.AddNode( "N1" )
		n2 = GafferTest.AddNode( "N2" )

		n2.getChild( "op1" ).setInput( n1.getChild( "sum" ) )

		n1.getChild( "op1" ).setValue( 1 )
		n1.getChild( "op2" ).setValue( -1 )

		self.assertEqual( n2.getChild( "sum" ).getValue(), 0 )

	def testOutputsDirtyForNewNodes( self ) :

		n = GafferTest.AddNode()
		n["op1"].setValue( 1 )
		n["op2"].setValue( 2 )

		self.assertEqual( n["sum"].getValue(), 3 )

	def testComputeInContext( self ) :

		n = GafferTest.FrameNode()
		self.assertEqual( n["output"].getValue(), 1 )

		c = Gaffer.Context()
		c.setFrame( 10 )

		with c :
			self.assertEqual( n["output"].getValue(), 10 )

	def testComputeInThreads( self ) :

		n = GafferTest.FrameNode()

		def f( frame ) :

			c = Gaffer.Context()
			c.setFrame( frame )

			with c :
				time.sleep( 0.01 )
				self.assertEqual( n["output"].getValue(), frame )

		threads = []
		for i in range( 0, 1000 ) :

			t = threading.Thread( target = f, args = ( i, ) )
			t.start()
			threads.append( t )

		for t in threads :
			t.join()

	def testDirtyNotPropagatedDuringCompute( self ) :

		n1 = GafferTest.AddNode( "n1" )
		n2 = GafferTest.AddNode( "n2" )

		n1["op1"].setValue( 2 )
		n1["op2"].setValue( 3 )
		n2["op1"].setInput( n1["sum"] )

		dirtyCapturer = GafferTest.CapturingSlot( n2.plugDirtiedSignal() )

		self.assertEqual( n2["sum"].getValue(), 5 )

		self.assertEqual( len( dirtyCapturer ), 0 )

	def testWrongPlugSet( self ) :

		n = GafferTest.BadNode()
		self.assertRaises( RuntimeError, n["out1"].getValue )

	def testPlugNotSet( self ) :

		n = GafferTest.BadNode()
		self.assertRaises( RuntimeError, n["out3"].getValue )

	def testHash( self ) :

		n = GafferTest.MultiplyNode()
		self.assertHashesValid( n )

	def testHashForPythonDerivedClasses( self ) :

		n = GafferTest.AddNode()
		self.assertHashesValid( n )

	def testDisableCaching( self ) :

		n = GafferTest.CachingTestNode()

		n["in"].setValue( "d" )

		v1 = n["out"].getValue( _copy=False )
		v2 = n["out"].getValue( _copy=False )

		self.assertEqual( v1, v2 )
		self.assertEqual( v1, IECore.StringData( "d" ) )

		# the objects should be one and the same, as the second computation
		# should have shortcut and returned a cached result.
		self.assertTrue( v1.isSame( v2 ) )

		n["out"].setFlags( Gaffer.Plug.Flags.Cacheable, False )
		v3 = n["out"].getValue( _copy=False )

		self.assertEqual( v3, IECore.StringData( "d" ) )
		self.assertEqual( v3, v1 )

		# we disabled caching, so the two values should
		# be distinct objects, even though they are equal.
		self.assertFalse( v3.isSame( v1 ) )

	def testConnectedPlugsShareHashesAndCacheEntries( self ) :

		class Out( Gaffer.ComputeNode ) :

			def __init__( self, name="Out" ) :

				Gaffer.ComputeNode.__init__( self, name )

				self.addChild( Gaffer.ObjectPlug( "oOut", Gaffer.Plug.Direction.Out, IECore.NullObject() ) )
				self.addChild( Gaffer.FloatPlug( "fOut", Gaffer.Plug.Direction.Out ) )

			def hash( self, output, context, h ) :

				h.append( context.getFrame() )

			def compute( self, plug, context ) :

				if plug.getName() == "oOut" :
					plug.setValue( IECore.IntData( int( context.getFrame() ) ) )
				else :
					plug.setValue( context.getFrame() )

		IECore.registerRunTimeTyped( Out )

		class In( Gaffer.ComputeNode ) :

			def __init__( self, name="In" ) :

				Gaffer.ComputeNode.__init__( self, name )

				self.addChild( Gaffer.ObjectPlug( "oIn", Gaffer.Plug.Direction.In, IECore.NullObject() ) )
				self.addChild( Gaffer.IntPlug( "iIn", Gaffer.Plug.Direction.In ) )

		IECore.registerRunTimeTyped( In )

		nOut = Out()
		nIn = In()

		nIn["oIn"].setInput( nOut["oOut"] )
		nIn["iIn"].setInput( nOut["fOut"] )

		for i in range( 0, 1000 ) :

			c = Gaffer.Context()
			c.setFrame( i )
			with c :

				# because oIn and oOut are connected, they should
				# have the same hash and share the exact same value.

				self.assertEqual( nIn["oIn"].getValue(), IECore.IntData( i ) )
				self.assertEqual( nOut["oOut"].getValue(), IECore.IntData( i ) )

				self.assertEqual( nIn["oIn"].hash(), nOut["oOut"].hash() )
				self.assertTrue( nIn["oIn"].getValue( _copy=False ).isSame( nOut["oOut"].getValue( _copy=False ) ) )

				# even though iIn and fOut are connected, they should have
				# different hashes and different values, because type conversion
				# (float to int) is performed when connecting them.

				self.assertEqual( nIn["iIn"].getValue(), i )
				self.assertEqual( nOut["fOut"].getValue(), float( i ) )

				self.assertNotEqual( nIn["iIn"].hash(), nOut["fOut"].hash() )

	class PassThrough( Gaffer.ComputeNode ) :

		def __init__( self, name="PassThrough" ) :

			Gaffer.ComputeNode.__init__( self, name )

			self.addChild( Gaffer.ObjectPlug( "in", Gaffer.Plug.Direction.In, IECore.NullObject() ) )
			self.addChild( Gaffer.ObjectPlug( "out", Gaffer.Plug.Direction.Out, IECore.NullObject() ) )

		def affects( self, input ) :

			outputs = Gaffer.ComputeNode.affects( self, input )

			if input.isSame( self["in"] ) :
				outputs.append( self["out"] )

			return outputs

		def hash( self, output, context, h ) :

			assert( output.isSame( self["out"] ) )

			# by assigning directly to the hash rather than appending,
			# we signify that we'll pass through the value unchanged.
			h.copyFrom( self["in"].hash() )

		def compute( self, plug, context ) :

			assert( plug.isSame( self["out"] ) )

			plug.setValue( self["in"].getValue( _copy=False ), _copy=False )

	IECore.registerRunTimeTyped( PassThrough )

	def testPassThroughSharesHashes( self ) :

		n = self.PassThrough()
		n["in"].setValue( IECore.IntVectorData( [ 1, 2, 3 ] ) )

		self.assertEqual( n["in"].hash(), n["out"].hash() )
		self.assertEqual( n["in"].getValue(), n["out"].getValue() )

	def testPassThroughSharesCacheEntries( self ) :

		n = self.PassThrough()
		n["in"].setValue( IECore.IntVectorData( [ 1, 2, 3 ] ) )

		self.assertTrue( n["in"].getValue( _copy=False ).isSame( n["out"].getValue( _copy=False ) ) )

	def testInternalConnections( self ) :

		a = GafferTest.AddNode()
		a["op1"].setValue( 10 )

		n = Gaffer.Node()
		n["in"] = Gaffer.IntPlug()
		n["out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		n["out"].setInput( n["in"] )

		n["in"].setInput( a["sum"] )

		self.assertEqual( n["out"].getValue(), a["sum"].getValue() )
		self.assertEqual( n["out"].hash(), a["sum"].hash() )

	def testErrorSignal( self ) :

		b = GafferTest.BadNode()
		a = GafferTest.AddNode()
		a["op1"].setInput( b["out3"] )

		cs = GafferTest.CapturingSlot( b.errorSignal() )

		self.assertRaises( RuntimeError, b["out1"].getValue )
		self.assertEqual( len( cs ), 1 )
		self.assertTrue( cs[0][0].isSame( b["out1"] ) )
		self.assertTrue( cs[0][1].isSame( b["out1"] ) )
		self.assertTrue( isinstance( cs[0][2], str ) )

		self.assertRaises( RuntimeError, a["sum"].getValue )
		self.assertEqual( len( cs ), 2 )
		self.assertTrue( cs[1][0].isSame( b["out3"] ) )
		self.assertTrue( cs[1][1].isSame( b["out3"] ) )
		self.assertTrue( isinstance( cs[1][2], str ) )

	def testErrorSignalledOnIntermediateNodes( self ) :

		nodes = [ GafferTest.BadNode() ]
		for i in range( 0, 10 ) :

			nodes.append( GafferTest.AddNode() )
			nodes[-1]["op1"].setInput(
				nodes[-2]["sum"] if i != 0 else nodes[-2]["out3"]
			)

		slots = [ GafferTest.CapturingSlot( n.errorSignal() ) for n in nodes ]

		self.assertRaises( RuntimeError, nodes[-1]["sum"].getValue )
		for i, slot in enumerate( slots ) :
			self.assertEqual( len( slot ), 1 )
			self.assertTrue( slot[0][0].isSame( nodes[i]["out3"] if i == 0 else nodes[i]["sum"] ) )
			self.assertTrue( slot[0][1].isSame( nodes[0]["out3"] ) )

	def testErrorSignalledAtScopeTransitions( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["b"] = GafferTest.BadNode()
		s["b"]["a"] = GafferTest.AddNode()
		s["b"]["a"]["op1"].setInput( s["b"]["b"]["out3"] )

		css = GafferTest.CapturingSlot( s.errorSignal() )
		csb = GafferTest.CapturingSlot( s["b"].errorSignal() )
		csbb = GafferTest.CapturingSlot( s["b"]["b"].errorSignal() )

		p = Gaffer.PlugAlgo.promote( s["b"]["a"]["sum"] )

		self.assertRaises( RuntimeError, p.getValue )
		self.assertEqual( len( css ), 0 )
		self.assertEqual( len( csb ), 1 )
		self.assertTrue( csb[0][0].isSame( p ) )
		self.assertTrue( csb[0][1].isSame( s["b"]["b"]["out3"] ) )
		self.assertEqual( len( csbb ), 1 )
		self.assertTrue( csbb[0][0].isSame( s["b"]["b"]["out3"] ) )
		self.assertTrue( csbb[0][1].isSame( s["b"]["b"]["out3"] ) )

	def testErrorSlotsDontSeeException( self ) :

		self.fRan = False
		def f( *unusedArgs ) :

			# If there's an active python exception (from
			# the error in BadNode below) when we try this
			# import, it'll appear (falsely) as if the error
			# originated from the import, and throw an exception
			# here. This is not the intention - error slots are
			# just meant to be informed of the error, without
			# ever seeing the exception itself.
			import IECore
			self.fRan = True

		n = GafferTest.BadNode()
		c = n.errorSignal().connect( f, scoped = True )

		with IECore.IgnoredExceptions( Exception ) :
			n["out1"].getValue()

		self.assertTrue( self.fRan )

	def testPlugDestructionDuringComputation( self ) :

		class PlugDestructionNode( GafferTest.AddNode ) :

			def __init__( self, name="PlugDestructionNode" ) :

				GafferTest.AddNode.__init__( self, name )

			def compute( self, plug, context ) :

				# It's not particularly smart to create a plug from
				# inside a compute, but here we're doing it to emulate
				# a situation which can occur when the python
				# garbage collector kicks in during computation.
				# When that happens, the garbage collector might
				# collect and destroy plugs from other graphs, and
				# we need the computation framework to be robust to
				# that. See #1576 for details of the original garbage
				# collection manifesting itself.
				v = Gaffer.ValuePlug()
				del v

				GafferTest.AddNode.compute( self, plug, context )

		IECore.registerRunTimeTyped( PlugDestructionNode )

		n = PlugDestructionNode()
		n["op1"].setValue( 1 )
		self.assertEqual( n["sum"].getValue(), 1 )

	def testThreading( self ) :

		GafferTest.testComputeNodeThreading()

	def testCancellationWithoutCooperation( self ) :

		s = Gaffer.ScriptNode()

		# The Expression nodes contain no explicit cancellation
		# checks. We rely on the Process stack to cancel prior to even
		# calling `compute()`. We use two expressions with a sleep
		# in each to give the main thread time to call cancel before
		# the second compute starts.

		s["n"] = GafferTest.AddNode()
		s["e1"] = Gaffer.Expression()
		s["e1"].setExpression( "import time; time.sleep( 0.9 ); parent['n']['op1'] = 10" )
		s["e2"] = Gaffer.Expression()
		s["e2"].setExpression( "import time; time.sleep( 0.9 ); parent['n']['op2'] = 20" )

		cs = GafferTest.CapturingSlot( s["n"].errorSignal() )

		def f( context ) :

			with context :
				with self.assertRaises( IECore.Cancelled ) :
					s["n"]["sum"].getValue()

		canceller = IECore.Canceller()
		thread = threading.Thread(
			target = f,
			args = [  Gaffer.Context( s.context(), canceller ) ]
		)
		thread.start()

		canceller.cancel()
		thread.join()

		# No errors should have been signalled, because cancellation
		# is not an error.
		self.assertEqual( len( cs ), 0 )

	def testCancellationWithCooperation( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		s["e"] = Gaffer.Expression()
		s["e"].setExpression( inspect.cleandoc(
			"""
			parent['n']['op1'] = 10
			while True :
				IECore.Canceller.check( context.canceller() )
			"""
		) )

		cs = GafferTest.CapturingSlot( s["n"].errorSignal() )

		def f( context ) :

			with context :
				with self.assertRaises( IECore.Cancelled ) :
					s["n"]["sum"].getValue()

		canceller = IECore.Canceller()
		thread = threading.Thread(
			target = f,
			args = [  Gaffer.Context( s.context(), canceller ) ]
		)
		thread.start()

		# Give the background thread time to get into the infinite
		# loop in the Expression, and then cancel it.
		time.sleep( 1 )
		canceller.cancel()
		thread.join()

		# No errors should have been signalled, because cancellation
		# is not an error.
		self.assertEqual( len( cs ), 0 )

	def testSlowCancellationWarnings( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		s["e"] = Gaffer.Expression()
		s["e"].setExpression( inspect.cleandoc(
			"""
			import time
			parent['n']['op1'] = 10
			time.sleep( 1.5 )
			"""
		) )

		messageHandler = IECore.CapturingMessageHandler()

		def f( context ) :

			with context, messageHandler :
				s["n"]["sum"].getValue()

		canceller = IECore.Canceller()
		thread = threading.Thread(
			target = f,
			args = [  Gaffer.Context( s.context(), canceller ) ]
		)
		thread.start()

		# Give the background thread time to get into the infinite
		# loop in the Expression, and then cancel it.
		time.sleep( 0.1 )
		canceller.cancel()
		thread.join()

		# Check that we have been warned about the slow cancellation.
		# Currently we're not smart enough to omit a message only for
		# the problematic compute - there is a message for each parent
		# process too.
		self.assertEqual( len( messageHandler.messages ), 3 )
		self.assertEqual( messageHandler.messages[0].level, IECore.Msg.Level.Warning )
		self.assertEqual( messageHandler.messages[0].context, "Process::~Process" )
		self.assertTrue( messageHandler.messages[0].message.startswith( "Cancellation for `ScriptNode.e.__execute` (computeNode:compute) took" ) )

	class ThrowingNode( Gaffer.ComputeNode ) :

		def __init__( self, name="ThrowingNode" ) :

			self.hashFail = False

			Gaffer.ComputeNode.__init__( self, name )

			self["in"] = Gaffer.IntPlug()
			self["out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )

		def affects( self, input ) :

			outputs = Gaffer.ComputeNode.affects( self, input )
			if input == self["in"] :
				outputs.append( self["out"] )

			return outputs

		def hash( self, plug, context, h ) :

			if plug == self["out"] :
				if self.hashFail :
					raise RuntimeError( "HashEeek!" )
				else:
					self["in"].hash( h )

		def compute( self, plug, context ) :

			if plug == self["out"] :
				raise RuntimeError( "Eeek!" )
			else :
				Gaffer.ComputeNode.compute( plug, context )

		def hashCachePolicy( self, plug ) :

			return Gaffer.ValuePlug.CachePolicy.Standard

		def computeCachePolicy( self, plug ) :

			return Gaffer.ValuePlug.CachePolicy.Standard

	IECore.registerRunTimeTyped( ThrowingNode )

	def testProcessException( self ) :

		thrower = self.ThrowingNode( "thrower" )
		add = GafferTest.AddNode()

		add["op1"].setInput( thrower["out"] )
		add["op2"].setValue( 1 )

		# We expect `thrower` to throw, and we want the name of the plug to be added
		# as a prefix to the error message.

		with Gaffer.Context() as context :
			context["test"] = 1
			with six.assertRaisesRegex( self, Gaffer.ProcessException, r'thrower.out : [\s\S]*Eeek!' ) as raised :
				add["sum"].getValue()

		# And we want to be able to retrieve details of the problem
		# from the exception.

		self.assertEqual( raised.exception.plug(), thrower["out"] )
		self.assertEqual( raised.exception.context(), context )
		self.assertEqual( raised.exception.processType(), "computeNode:compute" )

		# Make sure hash failures are reported correctly as well

		thrower.hashFail = True
		with Gaffer.Context() as context :
			context["test"] = 2
			with six.assertRaisesRegex( self, Gaffer.ProcessException, r'thrower.out : [\s\S]*HashEeek!' ) as raised :
				add["sum"].getValue()

		self.assertEqual( raised.exception.plug(), thrower["out"] )
		self.assertEqual( raised.exception.context(), context )
		self.assertEqual( raised.exception.processType(), "computeNode:hash" )

	def testProcessExceptionNotShared( self ) :

		thrower1 = self.ThrowingNode( "thrower1" )
		thrower2 = self.ThrowingNode( "thrower2" )

		with six.assertRaisesRegex( self, Gaffer.ProcessException, r'thrower1.out : [\s\S]*Eeek!' ) as raised :
			thrower1["out"].getValue()

		self.assertEqual( raised.exception.plug(), thrower1["out"] )

		with six.assertRaisesRegex( self, Gaffer.ProcessException, r'thrower2.out : [\s\S]*Eeek!' ) as raised :
			thrower2["out"].getValue()

		self.assertEqual( raised.exception.plug(), thrower2["out"] )

	def testProcessExceptionRespectsNameChanges( self ) :

		thrower = self.ThrowingNode( "thrower1" )
		with six.assertRaisesRegex( self, Gaffer.ProcessException, r'thrower1.out : [\s\S]*Eeek!' ) as raised :
			thrower["out"].getValue()

		self.assertEqual( raised.exception.plug(), thrower["out"] )

		thrower.setName( "thrower2" )
		with six.assertRaisesRegex( self, Gaffer.ProcessException, r'thrower2.out : [\s\S]*Eeek!' ) as raised :
			thrower["out"].getValue()

		self.assertEqual( raised.exception.plug(), thrower["out"] )

if __name__ == "__main__":
	unittest.main()
