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

import GafferUI
import GafferUITest

class MessageWidgetTest( GafferUITest.TestCase ) :

	def testCounts( self ) :

		def assertCounts( debug, info, warning, error ) :

			self.assertEqual( w.messageCount( IECore.Msg.Level.Debug ), debug )
			self.assertEqual( w.messageCount( IECore.Msg.Level.Info ), info )
			self.assertEqual( w.messageCount( IECore.Msg.Level.Warning ), warning )
			self.assertEqual( w.messageCount( IECore.Msg.Level.Error ), error )
			self.assertEqual( w.messageCount(), debug + info + warning + error )

		def msg( level ) :

			IECore.msg( level, "test", "test" )
			self.waitForIdle( 10 )

		w = GafferUI.MessageWidget()
		assertCounts( 0, 0, 0, 0 )

		with w.messageHandler() :

			msg( IECore.Msg.Level.Error )
			assertCounts( 0, 0, 0, 1 )

			msg( IECore.Msg.Level.Warning )
			assertCounts( 0, 0, 1, 1 )

			msg( IECore.Msg.Level.Info )
			assertCounts( 0, 1, 1, 1 )

			msg( IECore.Msg.Level.Debug )
			assertCounts( 1, 1, 1, 1 )

			msg( IECore.Msg.Level.Error )
			msg( IECore.Msg.Level.Error )
			assertCounts( 1, 1, 1, 3 )

			w.clear()
			assertCounts( 0, 0, 0, 0 )

	def testForwarding( self ) :

		w = GafferUI.MessageWidget()

		h = IECore.CapturingMessageHandler()
		w.forwardingMessageHandler().addHandler( h )

		self.assertEqual( w.messageCount( IECore.Msg.Level.Error ), 0 )
		self.assertEqual( len( h.messages ), 0 )

		with w.messageHandler() :
			IECore.msg( IECore.Msg.Level.Error, "test", "test" )
			self.waitForIdle( 10 )

		self.assertEqual( w.messageCount( IECore.Msg.Level.Error ), 1 )
		self.assertEqual( len( h.messages ), 1 )

		w.forwardingMessageHandler().removeHandler( h )

		with w.messageHandler() :
			IECore.msg( IECore.Msg.Level.Error, "test", "test" )
			self.waitForIdle( 10 )

		self.assertEqual( w.messageCount( IECore.Msg.Level.Error ), 2 )
		self.assertEqual( len( h.messages ), 1 )

if __name__ == "__main__":
	unittest.main()
