##########################################################################
#
#  Copyright (c) 2013, Image Engine Design. All rights reserved.
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
#      * Neither the name of Image Engine Design nor the names of
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
import GafferUI
import GafferImage

class FilterPlugValueWidget( GafferUI.EnumPlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		if isinstance( plug, GafferImage.FilterPlug ) :
			# Backwards compatibility for FilterPlug, which
			# was used for specifying GafferImage.Filters.
			values = [ (f, f) for f in GafferImage.FilterPlug.filters() ]
		else :
			assert( isinstance( plug, Gaffer.StringPlug ) )
			# Just a StringPlug for specifying the name of
			# an OIIO filter. This is how we want to do things
			# from now on.
			## \todo We should probably query these properly
			# from OIIO. Currently the OIIO::Filter class isn't
			# bound to Python though, so we need to decide
			# whether to provide access via our own APIs, or
			# to contribute some bindings to the OIIO project.
			values = [
				( "Default", "" ),
				( "Box", "box" ),
				( "Triangle", "triangle" ),
				( "Gaussian", "gaussian" ),
				( "Sharp Gaussian", "sharp-gaussian" ),
				( "Catmull-Rom", "catrom" ),
				( "Blackman-Harris", "blackman-harris" ),
				( "Sinc", "sinc" ),
				( "Lanczos3", "lanczos3" ),
				( "Radial Lanczos3", "radial-lanczos3" ),
				( "Mitchell", "mitchell" ),
				( "BSpline", "bspline" ),
				( "Disk", "disk" ),
				( "Cubic", "cubic" ),
				( "Keys", "keys" ),
				( "Simon", "simon" ),
				( "Rifman", "rifman" ),
			]

		GafferUI.EnumPlugValueWidget.__init__( self, plug, values, **kw )


GafferUI.PlugValueWidget.registerType( GafferImage.FilterPlug, FilterPlugValueWidget )

