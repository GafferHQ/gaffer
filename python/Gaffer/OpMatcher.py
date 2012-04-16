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

import threading
import traceback

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
class OpMatcher() :

	def __init__( self, classLoader, classNamesMatchString = "*" ) :
		
		# these are filled with tuples of the form ( opClass, parameter, parameterPath )
		self.__ops = []
		
		classNamesMatchString = "common/*"
		for className in classLoader.classNames( classNamesMatchString ) :
					
			try :
				opClass = classLoader.load( className )
				opInstance = opClass()
			except Exception, m :
				IECore.msg( IECore.Msg.Level.Error, "Gaffer.OpMatcher", "Error loading op \"%s\" : %s" % ( className, traceback.format_exc() ) )
				continue
			
			ignore = False
			with IECore.IgnoredExceptions( KeyError ) :
				# backwards compatibility with something proprietary
				ignore = opInstance.userData()["UI"]["OpMatcher"]["ignore"].value
			with IECore.IgnoredExceptions( KeyError ) :
				ignore = opInstance.userData()["OpMatcher"]["ignore"].value
			if ignore :
				continue
					
			parameter = self.__findParameter( opInstance.parameters() )
			if parameter is not None :
				self.__ops.append( ( opClass, ) + parameter )
			
	## Returns a list of suitable ops set up to operate on the given
	# parameterValue.
	def matches( self, parameterValue ) :
	
		processedValue = None
		if isinstance( parameterValue, ( Gaffer.FileSystemPath, Gaffer.SequencePath ) ) :
			processedValue = IECore.StringData( str( parameterValue ) )
		elif isinstance( parameterValue, list ) :
			processedValue = IECore.StringVectorData()
			for value in parameterValue :
				assert( isinstance( value, ( Gaffer.FileSystemPath, Gaffer.SequencePath ) ) )
				processedValue.append( str( value ) )
		elif isinstance( parameterValue, IECore.Object ) :
			processedValue = parameterValue
			
		if processedValue is None :
			return []
		
		result = []
		for opClass, testParameter, parameterPath in self.__ops :
			if testParameter.valueValid( processedValue )[0] :
				op = opClass()
				parameter = op.parameters()
				for name in parameterPath :
					parameter = parameter[name]
			
				parameter.setValue( processedValue )
				result.append( op )
		
		return result
				
	__defaultInstance = None
	__defaultInstanceMutex = threading.Lock()
	## Returns an OpMatcher suitable for sharing by everyone.
	@classmethod
	def defaultInstance( cls ) :
	
		with cls.__defaultInstanceMutex :
			if cls.__defaultInstance is None :
				cls.__defaultInstance = OpMatcher( IECore.ClassLoader.defaultOpLoader() )
				
			return cls.__defaultInstance
	
	def __findParameter( self, parameter, path = None ) :
	
		if path is None :
			path = []
	
		result = None
				
		for child in parameter.values() :
		
			ignore = False
			with IECore.IgnoredExceptions( KeyError ) :
				# backwards compatibility with something proprietary
				ignore = child.userData()["UI"]["OpMatcher"]["ignore"].value
			with IECore.IgnoredExceptions( KeyError ) :
				# backwards compatibility with something proprietary
				ignore = child.userData()["OpMatcher"]["ignore"].value	
			if ignore :
				continue
			
			childPath = path + [ child.name ]
			
			if isinstance( child, IECore.CompoundParameter ) :
				result = self.__findParameter( child, childPath )
				
			elif isinstance( child, ( IECore.PathParameter, IECore.PathVectorParameter ) ) :
				if child.mustExist :
					result = child, childPath
			
			if result is not None :
				return result
				
		return None
		
