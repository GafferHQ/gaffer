##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import GafferTractor

# Backwards compatibility for slots written when `preSpoolSignal()` didn't
# have the `taskData` argument.

def __slotWrapper( slot ) :

	signature = inspect.signature( slot )
	try :
		# Throws if not callable with three arguments
		signature.bind( None, None, None )
		# No need for a wrapper
		return slot
	except TypeError :
		pass

	# We'll need a wrapper

	warnings.warn(
		'Slot connected to `TractorDispatcher.preSpoolSignal() should have an additional `taskData` argument',
		DeprecationWarning
	)

	def call( dispatcher, *args ) :

		slot( dispatcher, *args[:-1] )

	return call

def __connectWrapper( originalConnect ) :

	def connect( slot, scoped = None ) :

		return originalConnect( __slotWrapper( slot ), scoped )

	return connect

GafferTractor.TractorDispatcher._TractorDispatcher__preSpoolSignal.connect = __connectWrapper( GafferTractor.TractorDispatcher._TractorDispatcher__preSpoolSignal.connect )
GafferTractor.TractorDispatcher._TractorDispatcher__preSpoolSignal.connectFront = __connectWrapper( GafferTractor.TractorDispatcher._TractorDispatcher__preSpoolSignal.connectFront )
