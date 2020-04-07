##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUI

def __applyChildVisibility( plug, visible ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		if visible :
			Gaffer.Metadata.registerValue( plug, "compoundNumericNodule:childrenVisible", True )
		else :
			Gaffer.Metadata.deregisterValue( plug, "compoundNumericNodule:childrenVisible" )

def __plugContextMenuSignal( graphEditor, plug, menuDefinition ) :

	# See if we've got a CompoundNodule. Early out if not.

	nodeGadget = graphEditor.graphGadget().nodeGadget( plug.node() )
	if not nodeGadget :
		return

	nodule = nodeGadget.nodule( plug )
	if not isinstance( nodule, GafferUI.CompoundNumericNodule ) :
		plug = plug.parent()
		if isinstance( plug, Gaffer.Plug ) :
			nodule = nodeGadget.nodule( plug )
		if not isinstance( nodule, GafferUI.CompoundNumericNodule ) :
			return

	# Add menu items for showing/hiding the children.

	childNames = "".join( c.getName() for c in plug ).upper()

	if len( nodule ) > 0 :
		menuDefinition.append(
			"/Collapse {} Components".format( childNames ),
			{
				"command" : functools.partial( __applyChildVisibility, plug, False ),
				"active" : not Gaffer.MetadataAlgo.readOnly( plug ),
			}
		)
	else :
		menuDefinition.append(
			"/Expand {} Components".format( childNames ),
			{
				"command" : functools.partial( __applyChildVisibility, plug, True ),
				"active" : not Gaffer.MetadataAlgo.readOnly( plug )
			}
		)

GafferUI.GraphEditor.plugContextMenuSignal().connect( __plugContextMenuSignal, scoped = False )
