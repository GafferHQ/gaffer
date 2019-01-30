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

import inspect

import IECore

import Gaffer
import GafferTest

class ProcessMessageHandlerTest( GafferTest.TestCase ) :

	def testMessageOutSideProcessIsForwardedUnmodified( self ) :

		capturingMessageHandler = IECore.CapturingMessageHandler()
		messageHandler = Gaffer.ProcessMessageHandler( capturingMessageHandler )

		# if we log a message outside a compute or hash Process then we only get the original message
		messageHandler.handle(IECore.MessageHandler.Level.Debug, "sending out an SOS", "message in a bottle")

		self.assertEqual(len( capturingMessageHandler.messages ), 1 )
		self.assertEqual(capturingMessageHandler.messages[0].level, IECore.MessageHandler.Level.Debug)
		self.assertEqual(capturingMessageHandler.messages[0].context, "sending out an SOS")
		self.assertEqual(capturingMessageHandler.messages[0].message, "message in a bottle")

	def testMessageInProcessGetExtraDebugInfo( self ) :

		capturingMessageHandler = IECore.CapturingMessageHandler()
		messageHandler = Gaffer.ProcessMessageHandler( capturingMessageHandler )

		scriptNode = Gaffer.ScriptNode()

		expression = Gaffer.Expression( "Expression" )

		node = Gaffer.Node( "Node" )

		node["user"].addChild( Gaffer.IntPlug( "test", defaultValue = 0, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )

		scriptNode.addChild(expression)
		scriptNode.addChild(node)

		expression.setExpression( inspect.cleandoc(
			"""
			import IECore
			IECore.MessageHandler.output( IECore.MessageHandler.Level.Error, "testA", "testB" )
			parent["Node"]["user"]["test"] = len( context.get( "scene:path", [] ) )
			"""
		) )

		with Gaffer.Context() as context :

			with messageHandler :

				self.assertEqual( node['user']['test'].getValue(), 0 )

				self.assertEqual( len( capturingMessageHandler.messages ), 2 )

				self.assertEqual( capturingMessageHandler.messages[0].level, IECore.MessageHandler.Level.Error )
				self.assertEqual( capturingMessageHandler.messages[0].context, "testA" )
				self.assertEqual( capturingMessageHandler.messages[0].message, "testB" )

				self.assertEqual( capturingMessageHandler.messages[1].level, IECore.MessageHandler.Level.Debug )
				self.assertEqual( capturingMessageHandler.messages[1].context, "Gaffer::Process" )
				self.assertEqual( capturingMessageHandler.messages[1].message, "[ plug: 'ScriptNode.Expression.__execute', frame: 1 ]" )

				del capturingMessageHandler.messages[:]

				context["scene:path"] = IECore.InternedStringVectorData( [ "a", "b" ] )

				self.assertEqual( node['user']['test'].getValue(), 2 )

				self.assertEqual( len( capturingMessageHandler.messages ), 2 )

				self.assertEqual( capturingMessageHandler.messages[0].level, IECore.MessageHandler.Level.Error )
				self.assertEqual( capturingMessageHandler.messages[0].context, "testA" )
				self.assertEqual( capturingMessageHandler.messages[0].message, "testB" )

				self.assertEqual( capturingMessageHandler.messages[1].level, IECore.MessageHandler.Level.Debug )
				self.assertEqual( capturingMessageHandler.messages[1].context, "Gaffer::Process" )
				self.assertEqual( capturingMessageHandler.messages[1].message, "[ plug: 'ScriptNode.Expression.__execute', frame: 1, path: '/a/b' ]" )

				del capturingMessageHandler.messages[:]

				del context["frame"]
				context["scene:path"] = IECore.InternedStringVectorData( [ "a", "b", "c" ] )

				self.assertEqual( node['user']['test'].getValue(), 3 )
				self.assertEqual( len( capturingMessageHandler.messages ), 2 )

				self.assertEqual( capturingMessageHandler.messages[0].level, IECore.MessageHandler.Level.Error )
				self.assertEqual( capturingMessageHandler.messages[0].context, "testA" )
				self.assertEqual( capturingMessageHandler.messages[0].message, "testB" )

				self.assertEqual( capturingMessageHandler.messages[1].level, IECore.MessageHandler.Level.Debug )
				self.assertEqual( capturingMessageHandler.messages[1].context, "Gaffer::Process" )
				self.assertEqual( capturingMessageHandler.messages[1].message, "[ plug: 'ScriptNode.Expression.__execute', path: '/a/b/c' ]" )

if __name__ == "__main__":
	unittest.main()
