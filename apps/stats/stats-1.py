##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import os
import collections

import IECore

import Gaffer

class stats( Gaffer.Application ) :

	def __init__( self ) :

		Gaffer.Application.__init__( self )

		self.parameters().addParameters(

			[
				IECore.FileNameParameter(
					name = "script",
					description = "The script to examine.",
					defaultValue = "",
					allowEmptyString = False,
					extensions = "gfr",
					check = IECore.FileNameParameter.CheckType.MustExist,
				),

			]

		)

		self.parameters().userData()["parser"] = IECore.CompoundObject(
			{
				"flagless" : IECore.StringVectorData( [ "script" ] )
			}
		)

	def _run( self, args ) :

		script = Gaffer.ScriptNode()
		script["fileName"].setValue( os.path.abspath( args["script"].value ) )
		script.load( continueOnError = True )

		self.__printVersion( script )

		print ""

		self.__printSettings( script )

		print ""

		self.__printVariables( script )

		print ""

		self.__printNodes( script )

	def __printVersion( self, script ) :

		numbers = [ Gaffer.Metadata.nodeValue( script, "serialiser:" + x + "Version" ) for x in ( "milestone", "major", "minor", "patch" ) ]
		if None not in numbers :
			version = ".".join( str( x ) for x in numbers )
		else :
			version = "unknown"

		print "Gaffer Version : {version}".format( version = version )

	def __printItems( self, items ) :

		width = max( [ len( x[0] ) for x in items ] ) + 4
		for name, value in items :
			print "  {name:<{width}}{value}".format( name = name, width = width, value = value )

	def __printSettings( self, script ) :

		plugsToIgnore = {
			script["fileName"],
			script["unsavedChanges"],
			script["variables"],
		}

		items = []
		def itemsWalk( p ) :

			if p in plugsToIgnore :
				return

			if hasattr( p, "getValue" ) :
				items.append( ( p.relativeName( script ), p.getValue() ) )
			else :
				for c in p.children( Gaffer.Plug ) :
					itemsWalk( c )

		itemsWalk( script )

		print "Settings :\n"
		self.__printItems( items )

	def __printVariables( self, script ) :

		items = []
		for p in script["variables"] :
			data, name = script["variables"].memberDataAndName( p )
			if data is not None :
				items.append( ( name, data ) )

		print "Variables :\n"
		self.__printItems( items )

	def __printNodes( self, script ) :

		def countWalk( node, counter ) :

			if not isinstance( node, Gaffer.ScriptNode ) :
				counter[node.typeName()] += 1

			for c in node.children( Gaffer.Node ) :
				countWalk( c, counter )

		counter = collections.Counter()
		countWalk( script, counter )

		items = [ ( nodeType.rpartition( ":" )[2], count ) for nodeType, count in counter.most_common() ]
		items.extend( [
			( "", "" ),
			( "Total", sum( counter.values() ) ),
		] )

		print "Nodes :\n"
		self.__printItems( items )

IECore.registerRunTimeTyped( stats )
