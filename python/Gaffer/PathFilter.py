##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

## PathFilters are classes which can filter the results
# of Path.children() methods to provide a masked view of
# filesystems. Filters are applied to a path using the Path.addFilter()
# method.
class PathFilter( object ) :

	def __init__( self, userData={} ) :

		self.__userData = userData.copy()

		self.__enabled = True
		self.__changedSignal = Gaffer.Signal1()

	def userData( self ) :

		return self.__userData

	def setEnabled( self, enabled ) :

		if enabled == self.__enabled :
			return

		self.__enabled = enabled
		self.__changedSignal( self )

	def getEnabled( self ) :

		return self.__enabled

	def filter( self, paths ) :

		if self.__enabled :
			return self._filter( paths )
		else :
			return paths

	## Returns a signal which is emitted whenever the filter
	# changes in some way.
	def changedSignal( self ) :

		return self.__changedSignal

	## Must be implemented by derived classes to filter the passed
	# list of paths and return a new list.
	def _filter( self, paths ) :

		raise NotImplementedError
