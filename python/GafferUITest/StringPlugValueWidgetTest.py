##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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

import unittest

import Gaffer
import GafferUI
import GafferUITest

class StringPlugValueWidgetTest( GafferUITest.TestCase ) :

	def test( self ) :

		n = Gaffer.Node()
		n["user"]["p1"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["user"]["p2"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		w = GafferUI.StringPlugValueWidget( n["user"]["p1"] )
		self.assertEqual( w.getPlug(), n["user"]["p1"] )
		self.assertEqual( w.getPlugs(), { n["user"]["p1"] } )
		self.assertEqual( w.textWidget().getText(), "" )
		self.assertEqual( w.textWidget()._qtWidget().placeholderText(), "" )

		n["user"]["p1"].setValue( "x" )
		self.assertEqual( w.textWidget().getText(), "x" )
		self.assertEqual( w.textWidget()._qtWidget().placeholderText(), "" )

		w.setPlugs( n["user"].children() )
		self.assertEqual( w.textWidget().getText(), "" )
		self.assertEqual( w.textWidget()._qtWidget().placeholderText(), "---" )

		n["user"]["p2"].setValue( "x" )
		self.assertEqual( w.textWidget().getText(), "x" )
		self.assertEqual( w.textWidget()._qtWidget().placeholderText(), "" )

		n["user"]["p1"].setValue( "" )
		n["user"]["p2"].setValue( "" )
		self.assertEqual( w.textWidget().getText(), "" )
		self.assertEqual( w.textWidget()._qtWidget().placeholderText(), "" )

		Gaffer.Metadata.registerValue( n["user"]["p1"], "stringPlugValueWidget:placeholderText", "test" )
		self.assertEqual( w.textWidget().getText(), "" )
		self.assertEqual( w.textWidget()._qtWidget().placeholderText(), "" )

		Gaffer.Metadata.registerValue( n["user"]["p2"], "stringPlugValueWidget:placeholderText", "test" )
		self.assertEqual( w.textWidget().getText(), "" )
		self.assertEqual( w.textWidget()._qtWidget().placeholderText(), "test" )

if __name__ == "__main__":
	unittest.main()
