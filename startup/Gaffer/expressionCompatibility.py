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

class __ExpressionPlug( Gaffer.Plug ) :

	def __init__( self ) :

		Gaffer.Plug.__init__(
			self,
			flags = Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.Serialisable
		)

	def setValue( self, value ) :

		engine = "python"
		if "engine" in self.node() :
			engine = self.node()["engine"].getValue()

		self.node().setExpression( value, engine )

## In prior versions of Gaffer, public "engine" and "expression"
# plugs were used to specify the expression to execute. These were
# then replaced with a setExpression() method. Here we emulate the
# old API for any old files or scripts which need it.
def __getItem( self, name ) :

	if name == "engine" and name not in self :
		self["engine"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.Serialisable )
	elif name == "expression" and name not in self :
		self["expression"] = __ExpressionPlug()

	return Gaffer.Node.__getitem__( self, name )

Gaffer.Expression.__getitem__ = __getItem
