##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import GafferImage

# add plugs to the preferences node

preferences = application.root()["preferences"]
preferences["cache"] = Gaffer.CompoundPlug()
preferences["cache"]["enabled"] = Gaffer.BoolPlug( defaultValue = True )
preferences["cache"]["memoryLimit"] = Gaffer.IntPlug( defaultValue = Gaffer.ValuePlug.getCacheMemoryLimit() / ( 1024 * 1024 ) )
preferences["cache"]["imageReaderMemoryLimit"] = Gaffer.IntPlug( defaultValue = GafferImage.OpenImageIOReader.getCacheMemoryLimit() / ( 1024 * 1024 ) )

Gaffer.Metadata.registerPlugValue(
	preferences["cache"]["memoryLimit"],
	"description",
	"""
	Controls the memory limit for Gaffer's ValuePlug cache.
	""",
	persistent = False
)

Gaffer.Metadata.registerPlugValue(
	preferences["cache"]["imageReaderMemoryLimit"],
	"description",
	"""
	Controls the memory limit for the OpenImageIO cache that the OpenImageIOReader node uses.
	""",
	persistent = False
)

# update cache settings when they change

def __plugSet( plug ) :

	if plug.relativeName( plug.node() ) != "cache" :
		return

	memoryLimit = plug["memoryLimit"].getValue() * 1024 * 1024
	imageReaderMemoryLimit = plug["imageReaderMemoryLimit"].getValue() * 1024 * 1024
	if not plug["enabled"].getValue() :
		memoryLimit = 0
		imageReaderMemoryLimit = 0

	Gaffer.ValuePlug.setCacheMemoryLimit( memoryLimit )
	GafferImage.OpenImageIOReader.setCacheMemoryLimit( imageReaderMemoryLimit )

preferences.plugSetSignal().connect( __plugSet, scoped = False )
