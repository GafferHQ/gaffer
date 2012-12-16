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

from __future__ import with_statement

import IECore

import Gaffer
import GafferUI

class procedural( Gaffer.Application ) :

	def __init__( self ) :
	
		Gaffer.Application.__init__( self )
		
		self.parameters().addParameters(
		
			[
			
				IECore.StringParameter(
					name = "procedural",
					description = "The name of the procedural to visualise.",
					defaultValue = ""
				),
				
				IECore.IntParameter(
					name = "version",
					description = "The version of the procedural to visualise.",
					defaultValue = -1,
				),
				
				IECore.StringParameter(
					name = "preset",
					description = "The name of a preset to load.",
					defaultValue = "",
				),
								
				IECore.StringVectorParameter(
					name = "arguments",
					description = "The arguments to be passed to the procedural. This should be the last "
						"command line argument passed.",
					defaultValue = IECore.StringVectorData( [] ),
					userData = {
						"parser" : {
							"acceptFlags" : IECore.BoolData( True ),
						},
					},
				),
				
			]
			
		)
		
		self.parameters().userData()["parser"] = IECore.CompoundObject(
			{
				"flagless" : IECore.StringVectorData( [ "procedural", "version" ] )
			}
		)
		
		self.__classLoader = None
				
	def _run( self, args ) :
		
		loader = IECore.ClassLoader.defaultProceduralLoader()
		
		matchingProceduralNames = loader.classNames( "*" + args["procedural"].value )
		if not len( matchingProceduralNames ) :
			IECore.msg( IECore.Msg.Level.Error, "procedural", "Procedural \"%s\" does not exist" % args["procedural"].value )
			return 1
		elif len( matchingProceduralNames ) > 1 :
			IECore.msg(
				IECore.Msg.Level.Error, "procedural",
				"Procedural name \"%s\" is ambiguous - could be any of the following : \n\n\t%s" % (
					args["procedural"].value,
					"\n\t".join( matchingProceduralNames ),
				)
			)
			return 1
		else :
			proceduralName = matchingProceduralNames[0]
		
		proceduralVersion = args["version"].value
		if proceduralVersion >= 0 :
			if proceduralVersion not in classLoader.versions( proceduralName ) :
				IECore.msg( IECore.Msg.Level.Error, "procedural", "Version %d of procedural \"%s\" does not exist" % ( proceduralVersion, args["procedural"].value ) )
				return 1
		else :
			proceduralVersion = None # let loader choose default	
		
		procedural = loader.load( proceduralName, proceduralVersion )()
		
		if args["preset"].value :
			
			presetLoader = IECore.ClassLoader.defaultLoader( "IECORE_PROCEDURAL_PRESET_PATHS" )
			
			preset = None
			if procedural.typeName() + "/" + args["preset"].value in presetLoader.classNames() :
				preset = presetLoader.load( procedural.typeName() + "/" + args["preset"].value )()
			elif args["preset"].value in presetLoader.classNames() :
				preset = presetLoader.load( args["preset"].value )()
				
			if preset is None :
				IECore.msg( IECore.Msg.Level.Error, "procedural", "Preset \"%s\" does not exist" % args["preset"].value )
				return 1
				
			if not preset.applicableTo( procedural, procedural.parameters() ) :
				IECore.msg( IECore.Msg.Level.Error, "procedural", "Preset \"%s\" is not applicable to procedural \"%s\"" % ( args["preset"].value, proceduralName ) )
				return 1
				
			preset( procedural, procedural.parameters() )
			
		IECore.ParameterParser().parse( list( args["arguments"] ), procedural.parameters() )

		proceduralHolder = Gaffer.ProceduralHolder()
		proceduralHolder.setParameterised( procedural )
		
		with GafferUI.Window( "Procedural : %s " % proceduralName ) as window :
			with GafferUI.SplitContainer( GafferUI.SplitContainer.Orientation.Horizontal ) as splitContainer :
				viewer = GafferUI.Viewer( Gaffer.ScriptNode() )
				viewer.setNodeSet( Gaffer.StandardSet( [ proceduralHolder ] ) )
				with GafferUI.Frame( borderStyle = GafferUI.Frame.BorderStyle.None ) :
					GafferUI.NodeUI.create( proceduralHolder )
			splitContainer.setSizes( ( 3, 2 ) )
		
		## \todo Naughty! We need a public API for this sort of thing
		window._qtWidget().resize( 900, 600 )	
		window.setVisible( True )
		GafferUI.EventLoop.mainEventLoop().start()		
			
		return 0

IECore.registerRunTimeTyped( procedural )
