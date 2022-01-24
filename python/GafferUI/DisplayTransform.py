##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

## Although the Style and Widget classes deal with uncorrected colour
# for their drawing, widgets such as colour choosers may be used in
# colour-sensitive applications where correcting for the display's
# characteristics is fundamentally important. Rather than introduce
# a GafferUI dependency on a specific colour management system, this
# class allows the registration of a function to perform linear->display
# transforms, and to signal when this is changed. It is expected that
# specific application configurations will set this appropriately.
class DisplayTransform( object ) :

	# have to store it inside a list so python doesn't
	# keep trying to turn it into a method.
	__linearToDisplay = [ lambda c : c ]

	@classmethod
	def set( cls, linearToDisplayCallable ) :

		cls.__linearToDisplay[0] = linearToDisplayCallable
		cls.changedSignal()()

	@classmethod
	def get( cls ) :

		return cls.__linearToDisplay[0]

	__changedSignal = Gaffer.Signals.Signal0()
	@classmethod
	def changedSignal( cls ) :

		return cls.__changedSignal
