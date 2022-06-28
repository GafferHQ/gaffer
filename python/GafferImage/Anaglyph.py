##########################################################################
#
#  Copyright (c) 2022, Image Engine Design Inc. All rights reserved.
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
import GafferImage

class Anaglyph( GafferImage.ImageProcessor ) :

	def __init__(self, name = 'Anaglyph' ) :
		GafferImage.ImageProcessor.__init__( self, name )

		self["__SelectLeft"] = GafferImage.SelectView()
		self["__SelectLeft"]["in"].setInput( self["in"] )

		self["__DeleteChannelsLeft"] = GafferImage.DeleteChannels()
		self["__DeleteChannelsLeft"]["in"].setInput( self["__SelectLeft"]["out"] )
		self["__DeleteChannelsLeft"]["channels"].setValue( '[GB] *.[GB]' )

		self["__SelectRight"] = GafferImage.SelectView()
		self["__SelectRight"]["in"].setInput( self["in"] )
		self["__SelectRight"]["view"].setValue( 'right' )

		self["__DeleteChannelsRight"] = GafferImage.DeleteChannels()
		self["__DeleteChannelsRight"]["in"].setInput( self["__SelectRight"]["out"] )
		self["__DeleteChannelsRight"]["channels"].setValue( '[R] *.[R]' )

		self["__Merge"] = GafferImage.Merge()
		self["__Merge"]["in"][0].setInput( self["__DeleteChannelsLeft"]["out"] )
		self["__Merge"]["in"][1].setInput( self["__DeleteChannelsRight"]["out"] )
		self["__Merge"]["operation"].setValue( GafferImage.Merge.Operation.Max )

		self["__disableSwitch"] = Gaffer.Switch()
		self["__disableSwitch"].setup( self["in"] )
		self["__disableSwitch"]["in"][0].setInput( self["in"] )
		self["__disableSwitch"]["in"][1].setInput( self["__Merge"]["out"] )
		self["__disableSwitch"]["index"].setInput( self["enabled"] )

		self['out'].setFlags(Gaffer.Plug.Flags.Serialisable, False)
		self["out"].setInput( self["__disableSwitch"]["out"] )

IECore.registerRunTimeTyped( Anaglyph, typeName = "GafferImage::Anaglyph" )
