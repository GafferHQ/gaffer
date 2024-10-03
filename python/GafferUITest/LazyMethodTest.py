##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class LazyMethodTest( GafferUITest.TestCase ) :

	class LazyWidget( GafferUI.TextWidget ) :

		def __init__( self, **kw ) :

			GafferUI.TextWidget.__init__( self, **kw )

			self.__scriptNode = Gaffer.ScriptNode()

		## To use deferUntilPlaybackStops, the widget must
		# have a `scriptNode()` method from which a Playback
		# object can be acquired.
		def scriptNode( self ) :

			return self.__scriptNode

		@GafferUI.LazyMethod()
		def setTextLazily( self, text ) :

			self.setText( text )

		@GafferUI.LazyMethod( replacePendingCalls = False )
		def setTextLazilyNoReplace( self, text ) :

			self.setText( text )

		@GafferUI.LazyMethod( deferUntilPlaybackStops = True )
		def setTextLazilyDeferredUntilStop( self, text ) :

			self.setText( text )

	def test( self ) :

		with GafferUI.Window() as window :
			w = self.LazyWidget()

		cs = GafferTest.CapturingSlot( w.textChangedSignal() )

		w.setTextLazily( "t" )
		self.assertEqual( len( cs ), 0 )
		self.assertEqual( w.getText(), "" )

		window.setVisible( True )

		self.assertEqual( len( cs ), 1 )
		self.assertEqual( w.getText(), "t" )

		w.setTextLazily( "u" )

		self.assertEqual( len( cs ), 1 )
		self.assertEqual( w.getText(), "t" )

		self.waitForIdle( 100 )

		self.assertEqual( len( cs ), 2 )
		self.assertEqual( w.getText(), "u" )

		w.setTextLazily( "v" )
		w.setTextLazily( "w" )

		self.assertEqual( len( cs ), 2 )
		self.assertEqual( w.getText(), "u" )

		self.waitForIdle( 100 )

		self.assertEqual( len( cs ), 3 )
		self.assertEqual( w.getText(), "w" )

	def testReplacePendingCalls( self ) :

		with GafferUI.Window() as window :
			w = self.LazyWidget()

		cs = GafferTest.CapturingSlot( w.textChangedSignal() )

		w.setTextLazilyNoReplace( "s" )
		w.setTextLazilyNoReplace( "t" )
		self.assertEqual( len( cs ), 0 )
		self.assertEqual( w.getText(), "" )

		window.setVisible( True )

		self.assertEqual( len( cs ), 2 )
		self.assertEqual( w.getText(), "t" )

	def testDeferUntilPlaybackStops( self ) :

		with GafferUI.Window() as window :
			w = self.LazyWidget()

		cs = GafferTest.CapturingSlot( w.textChangedSignal() )

		w.setTextLazilyDeferredUntilStop( "t" )
		self.assertEqual( len( cs ), 0 )
		self.assertEqual( w.getText(), "" )

		window.setVisible( True )

		self.assertEqual( len( cs ), 1 )
		self.assertEqual( w.getText(), "t" )

		p = GafferUI.Playback.acquire( w.scriptNode().context() )

		p.setState( p.State.PlayingForwards )

		w.setTextLazilyDeferredUntilStop( "s" )

		self.assertEqual( len( cs ), 1 )
		self.assertEqual( w.getText(), "t" )

		self.waitForIdle( 100 )

		self.assertEqual( len( cs ), 1 )
		self.assertEqual( w.getText(), "t" )

		p.setState( p.State.Stopped )

		self.assertEqual( len( cs ), 2 )
		self.assertEqual( w.getText(), "s" )

	def testFlush( self ) :

		w = self.LazyWidget()
		cs = GafferTest.CapturingSlot( w.textChangedSignal() )

		self.LazyWidget.setTextLazily.flush( w )
		self.assertEqual( len( cs ), 0 )
		self.assertEqual( w.getText(), "" )

		w.setTextLazily( "t" )
		self.assertEqual( len( cs ), 0 )
		self.assertEqual( w.getText(), "" )

		self.LazyWidget.setTextLazily.flush( w )
		self.assertEqual( len( cs ), 1 )
		self.assertEqual( w.getText(), "t" )

		self.LazyWidget.setTextLazily.flush( w )
		self.assertEqual( len( cs ), 1 )
		self.assertEqual( w.getText(), "t" )

if __name__ == "__main__":
	unittest.main()
