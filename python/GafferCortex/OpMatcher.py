##########################################################################
#
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

import contextlib
import threading
import traceback
import weakref

import IECore

import Gaffer

## The OpMatcher class provides a means of searching for Ops suitable to
# act upon a given input value.
#
# The following Op userData entries are supported :
#
# ["OpMatcher"]["ignore"] - when this BoolData is True, the Op is not
# considered by the matcher.
#
# The following Parameter usedData entries are supported :
#
# ["OpMatcher"]["ignore"] - when this BoolData is True, the Parameter is not
# considered by the matcher.
class OpMatcher( object ) :

	def __init__( self, classLoader, classNamesMatchString = "*", reportErrors=True ) :

		# these are filled with tuples of the form ( opClass, parameter, parameterPath )
		self.__ops = []

		for className in classLoader.classNames( classNamesMatchString ) :

			try :
				opClass = classLoader.load( className )
				opInstance = opClass()
			except Exception as m :
				if reportErrors :
					IECore.msg( IECore.Msg.Level.Error, "GafferCortex.OpMatcher", "Error loading op \"%s\" : %s" % ( className, traceback.format_exc() ) )
				continue

			ignore = False
			with contextlib.suppress( KeyError ) :
				# backwards compatibility with something proprietary
				ignore = opInstance.userData()["UI"]["OpMatcher"]["ignore"].value
			with contextlib.suppress( KeyError ) :
				ignore = opInstance.userData()["OpMatcher"]["ignore"].value
			if ignore :
				continue

			parameters = []
			self.__findParameters( opInstance.parameters(), parameters )
			if len( parameters ) :
				self.__ops.append( ( opClass, parameters ) )

	## Returns a list of ( op, parameter ) tuples. Each op will be an Op instance
	# where the corresponding parameter has already been set with parameterValue.
	def matches( self, parameterValue ) :

		processedValues = []
		if isinstance( parameterValue, ( Gaffer.FileSystemPath, Gaffer.SequencePath ) ) :
			# we might be able to match a single file
			processedValues.append( IECore.StringData( str( parameterValue ) ) )
			# or provide a single file input to an op which accepts multiple files
			processedValues.append( IECore.StringVectorData( [ str( parameterValue ) ] ) )
		elif isinstance( parameterValue, list ) :
			processedValue = IECore.StringVectorData()
			for value in parameterValue :
				assert( isinstance( value, ( Gaffer.FileSystemPath, Gaffer.SequencePath ) ) )
				processedValue.append( str( value ) )
		elif isinstance( parameterValue, IECore.Object ) :
			processedValue = parameterValue

		if not processedValues :
			return []

		result = []
		for opClass, parameters in self.__ops :
			for testParameter, parameterPath in parameters :
				for processedValue in processedValues :
					if testParameter.valueValid( processedValue )[0] :
						op = opClass()
						parameter = op.parameters()
						for name in parameterPath :
							parameter = parameter[name]

						parameter.setValue( processedValue )
						result.append( ( op, parameter ) )

		return result

	__defaultInstances = weakref.WeakKeyDictionary()
	__defaultInstancesMutex = threading.Lock()
	## Returns an OpMatcher suitable for sharing by everyone - initialising one
	# takes considerable time so it's preferable to reuse one if one has been created
	# for the classLoader in question already. If classLoader is not specified then
	# it defaults to IECore.ClassLoader.defaultOpLoader().
	@classmethod
	def defaultInstance( cls, classLoader=None ) :

		if classLoader is None :
			classLoader = IECore.ClassLoader.defaultOpLoader()

		with cls.__defaultInstancesMutex :

			result = cls.__defaultInstances.get( classLoader, None )
			if result is None :
				result = OpMatcher( classLoader )
				cls.__defaultInstances[classLoader] = result

			return result

	def __findParameters( self, parameter, result, path = None ) :

		if path is None :
			path = []

		for child in parameter.values() :

			ignore = False
			with contextlib.suppress( KeyError ) :
				# backwards compatibility with something proprietary
				ignore = child.userData()["UI"]["OpMatcher"]["ignore"].value
			with contextlib.suppress( KeyError ) :
				# backwards compatibility with something proprietary
				ignore = child.userData()["OpMatcher"]["ignore"].value
			if ignore :
				continue

			childPath = path + [ child.name ]

			if isinstance( child, IECore.CompoundParameter ) :
				self.__findParameters( child, result, childPath )
			elif isinstance( child, ( IECore.PathParameter, IECore.PathVectorParameter ) ) :
				if child.mustExist :
					result.append( ( child, childPath ) )
