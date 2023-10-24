##########################################################################
#
#  Copyright (c) 2019, John Haddon. All rights reserved.
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

import pathlib
import re

import IECore

import Gaffer

## Creates a custom Gaffer extension by exporting one or more Boxes
# as new node types defined in a python module. An associated startup
# file is generated to add the nodes to the node menu. If `directory`
# is placed on the GAFFER_EXTENSION_PATHS then the extension will be
# loaded automatically by Gaffer.
def exportExtension( name, boxes, directory ) :

	if isinstance( directory, str ) :
		directory = pathlib.Path( directory )

	pythonDir = directory / "python" / name
	pythonDir.mkdir( parents = True, exist_ok = True )

	with open( pythonDir / "__init__.py", "w", encoding = "utf-8" ) as initFile :

		for box in boxes :

			with open( pythonDir / (box.getName() + ".py"), "w", encoding = "utf-8" ) as nodeFile :
				nodeFile.write( __nodeDefinition( box, name ) )

			initFile.write( "from .{name} import {name}\n".format( name = box.getName() ) )

	uiDir = directory / "python" / (name + "UI")
	uiDir.mkdir( parents = True, exist_ok = True )

	with open( uiDir / "__init__.py", "w", encoding = "utf-8" ) as initFile :

		for box in boxes :

			with open( uiDir / (box.getName() + "UI.py"), "w", encoding = "utf-8" ) as uiFile :
				uiFile.write( __uiDefinition( box, name ) )

			initFile.write( "from . import {name}UI\n".format( name = box.getName() ) )

	startupDir = directory / "startup" / "gui"
	startupDir.mkdir( parents = True, exist_ok = True )

	with open( startupDir / (name + ".py"), "w", encoding = "utf-8" ) as startupFile :

		nodeMenuDefinition = []
		for box in boxes :

			nodeMenuPath = Gaffer.Metadata.value( box, "extension:nodeMenuItem" )
			if not nodeMenuPath :
				nodeMenuPath = "/{name}/{node}".format( name = name, node = box.getName() )

			nodeMenuDefinition.append(
				"nodeMenu.append( \"{nodeMenuPath}\", {name}.{node} )\n".format(
					nodeMenuPath = nodeMenuPath,
					name = name,
					node = box.getName()
				)
			)

		startupFile.write(
			__startupTemplate.format(
				name = name,
				nodeMenuDefinition = "\n".join( nodeMenuDefinition )
			)
		)

__startupTemplate = """\
import GafferUI
import {name}
import {name}UI

nodeMenu = GafferUI.NodeMenu.acquire( application )

{nodeMenuDefinition}
"""

def __indent( text, n ) :

	prefix = "\t" * n
	return "\n".join( prefix + l for l in text.split( "\n" ) )

__nodeTemplate = """\
{imports}

class {name}( Gaffer.SubGraph ) :

	def __init__( self, name = "{name}" ) :

		Gaffer.SubGraph.__init__( self, name )

{constructor}

		self.__removeDynamicFlags()

	# Remove dynamic flags using the same logic used by the Reference node.
	## \todo : Create the plugs without the flags in the first place.
	def __removeDynamicFlags( self ) :

		for plug in Gaffer.Plug.Range( self ) :
			plug.setFlags( Gaffer.Plug.Flags.Dynamic, False )
			if not isinstance( plug, ( Gaffer.SplineffPlug, Gaffer.SplinefColor3fPlug, Gaffer.SplinefColor4fPlug ) ) :
				for plug in Gaffer.Plug.RecursiveRange( plug ) :
					plug.setFlags( Gaffer.Plug.Flags.Dynamic, False )

IECore.registerRunTimeTyped( {name}, typeName = "{extension}::{name}" )
"""

def __nodeDefinition( box, extension ) :

	invisiblePlug = re.compile( "^__.*$" )
	children = Gaffer.StandardSet()
	for child in box.children() :
		if isinstance( child, Gaffer.Node ) :
			children.add( child )
		elif isinstance( child, Gaffer.Plug ) :
			if not invisiblePlug.match( child.getName() ) and child != box["user"] :
				children.add( child )

	with Gaffer.Context() as context :
		context["serialiser:includeVersionMetadata"] = IECore.BoolData( False )
		context["serialiser:protectParentNamespace"] = IECore.BoolData( False )
		context["valuePlugSerialiser:omitParentNodePlugValues"] = IECore.BoolData( True )
		context["plugSerialiser:includeParentPlugMetadata"] = IECore.BoolData( False )
		constructor = Gaffer.Serialisation( box, "self", children ).result()

	imports = { "import IECore", "import Gaffer" }
	constructorLines = []
	for line in constructor.split( "\n" ) :
		if line.startswith( "import" ) :
			imports.add( line )
		else :
			constructorLines.append( line )

	return __nodeTemplate.format(
		imports = "\n".join( sorted( imports ) ),
		name = box.getName(),
		constructor = __indent( "\n".join( constructorLines ), 2 ),
		extension = extension
	)

__uiTemplate = """\
import imath
import IECore
import Gaffer
import {extension}

Gaffer.Metadata.registerNode(

	{extension}.{name},

{metadata}
{plugMetadata}

)
"""

def __uiDefinition( box, extension ) :

	return __uiTemplate.format(

		extension = extension,
		name = box.getName(),
		metadata = __indent( __metadata( box ), 1 ),
		plugMetadata = __indent( __plugMetadata( box ), 1 )

	)

def __metadata( graphComponent ) :

	items = []
	for k in Gaffer.Metadata.registeredValues( graphComponent, Gaffer.Metadata.RegistrationTypes.InstancePersistent ) :

		v = Gaffer.Metadata.value( graphComponent, k )
		items.append(
			"{k}, {v},".format( k = repr( k ), v = IECore.repr( v ) )
		)

	return "\n".join( items )

def __plugMetadata( box ) :

	items = []
	def walkPlugs( graphComponent ) :

		if isinstance( graphComponent, Gaffer.Plug ) :

			m = __metadata( graphComponent )
			if m :
				items.append(
					"\"{name}\" : [\n{m}\n],\n".format(
						name = graphComponent.relativeName( graphComponent.node() ),
						m = __indent( m, 1 )
					)
				)

		for plug in graphComponent.children( Gaffer.Plug ) :
			walkPlugs( plug )

	walkPlugs( box )

	if items :
		return "plugs = {\n\n" + __indent( "\n".join( items ), 1 ) + "\n}\n"
	else :
		return ""
