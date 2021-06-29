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

import functools

import IECore

import Gaffer
import GafferUI

def __plugMenu( title, plugs ) :

	chosenPlugs = []
	def choosePlug( plug ) :
		chosenPlugs.append( plug )

	menuDefinition = IECore.MenuDefinition()
	for plug in plugs :
		menuDefinition.append(
			"/" + ( Gaffer.Metadata.value( plug, "noduleLayout:label" ) or plug.getName() ),
			{
				"command" : functools.partial( choosePlug, plug )
			}
		)

	menu = GafferUI.Menu( menuDefinition, title = title )
	menu.popup( modal = True )

	return chosenPlugs[0] if chosenPlugs else None

GafferUI.PlugAdder.plugMenuSignal().connect( __plugMenu, scoped = False )

def __menu( title, names ) :

	from uuid import uuid4

	chosenNames = []
	def chooseName( name ) :
		chosenNames.append( name )

	menuDefinition = IECore.MenuDefinition()
	for name in names :
		if not name.split('/')[-1] :
			menuDefinition.append(
				"/" + name + uuid4().hex,
				{
					"divider" : True
				}
			)
		else :
			menuDefinition.append(
				"/" + name,
				{
					"command" : functools.partial( chooseName, name )
				}
			)

	menu = GafferUI.Menu( menuDefinition, title = title )
	menu.popup( modal = True )

	return chosenNames[0] if chosenNames else ""

GafferUI.PlugAdder.menuSignal().connect( __menu, scoped = False )
