##########################################################################
#
#  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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
import GafferScene

import IECore

import imath

# This private node is registered as a render adaptor in startup/GafferScene/usdPointInstancerAdaptor.py

class _PointInstancerAdaptor( GafferScene.SceneProcessor ) :

	def __init__( self, name = "_PointInstancerAdaptor" ) :

		GafferScene.SceneProcessor.__init__( self, name )

		self["renderer"] = Gaffer.StringPlug()

		# By default, we are enabled for any renderer other than OpenGL
		enabledForRenderers = set( GafferScene.Private.IECoreScenePreview.Renderer.types() )
		enabledForRenderers = enabledForRenderers - set( [ "OpenGL", "Capturing" ] )
		self["enabledRenderers"] = Gaffer.StringVectorDataPlug( defaultValue = IECore.StringVectorData( enabledForRenderers ) )

		# First, a simple thing that is a bit messy to do: we don't want to process locations that
		# aren't points. The most obvious way this could come up is if a parent transform is put in
		# the 'usd:pointInstancers' set - we don't want to hide everything underneath that location.
		# In order to apply only to actual points primitives, we use a PrimitiveVariableQuery to check
		# each location for whether it is an object with a P primvar.
		self["usdPointInstancerSet"] = GafferScene.SetFilter()
		self["usdPointInstancerSet"]["setExpression"].setValue( 'usd:pointInstancers' )

		self["pathInSetFilterResult"] = GafferScene.FilterResults()
		self["pathInSetFilterResult"]["scene"].setInput( self["in"] )
		self["pathInSetFilterResult"]["filter"].setInput( self["usdPointInstancerSet"]["out"] )

		self["primitiveVariableQuery"] = GafferScene.PrimitiveVariableQuery()
		self["primitiveVariableQuery"]["scene"].setInput( self["in"] )
		self["primitiveVariableQuery"]["location"].setValue( "${collect:value}" )
		self["primitiveVariableQuery"].addQuery( Gaffer.V3fPlug( "value", defaultValue = imath.V3f( 0, 0, 0 ), ) )
		self["primitiveVariableQuery"]["queries"][0]["name"].setValue( 'P' )

		self["collectValidPaths"] = Gaffer.Collect()
		self["collectValidPaths"].addInput( Gaffer.StringPlug( "paths", defaultValue = '${collect:value}', ) )
		self["collectValidPaths"]["contextValues"].setInput( self["pathInSetFilterResult"]["outStrings"] )
		self["collectValidPaths"]["enabled"].setInput( self["primitiveVariableQuery"]["out"][0]["exists"] )

		self["validPaths"] = GafferScene.PathFilter()
		self["validPaths"]["paths"].setInput( self["collectValidPaths"]["out"]["paths"] )

		# Set an invisible attribute on the descendants of the instancers, which shouldn't be visible
		# ( USD halts draw traversal when it finds PointInstancer )
		self["instancerDescendants"] = GafferScene.PathFilter()
		self["instancerDescendants"]["paths"].setValue( IECore.StringVectorData( [ '/*' ] ) )
		self["instancerDescendants"]["roots"].setInput( self["validPaths"]["out"] )

		self["invisAttribute"] = GafferScene.StandardAttributes()
		self["invisAttribute"]["in"].setInput( self["in"] )
		self["invisAttribute"]["filter"].setInput( self["instancerDescendants"]["out"] )
		self["invisAttribute"]["attributes"]["visibility"]["value"].setValue( False )
		self["invisAttribute"]["attributes"]["visibility"]["enabled"].setValue( True )

		self["attrOptionQuery"] = GafferScene.OptionQuery()
		self["attrOptionQuery"]["scene"].setInput( self["in"] )
		self["attrOptionQuery"].addQuery( Gaffer.StringPlug( "value" ), "gafferUSD:pointInstancerAdaptor:attributes" )

		self["instancer"] = GafferScene.Instancer()
		self["instancer"]["in"].setInput( self["invisAttribute"]["out"] )
		self["instancer"]["filter"].setInput( self["validPaths"]["out"] )
		self["instancer"]["prototypeMode"].setValue( 1 )
		self["instancer"]["prototypeIndex"].setValue( 'prototypeIndex' )
		self["instancer"]["omitDuplicateIds"].setValue( False )
		self["instancer"]["orientation"].setValue( 'orientation' )
		self["instancer"]["scale"].setValue( 'scale' )
		self["instancer"]["inactiveIds"].setValue( 'inactiveIds invisibleIds' )
		self["instancer"]["attributes"].setInput( self["attrOptionQuery"]["out"][0]["value"] )
		self["instancer"]["attributePrefix"].setValue( 'user:' )

		# Do some rewiring to turn this Instancer into a recursive instancer by plumbing the output
		# back into the prototypes. This allows for USD PointInstancers to instance other PointInstancers
		for plug in Gaffer.Plug.Range( self["instancer"]["prototypes"] ) :
			plug.setFlags( Gaffer.Plug.Flags.AcceptsDependencyCycles, True )
		self["instancer"]["prototypes"].setInput( self["instancer"]["out"] )
		self["instancer"]["out"]["setNames"].setInput( self["instancer"]["in"]["setNames"] )
		self["instancer"]["out"]["set"].setInput( self["instancer"]["in"]["set"] )

		# Currently only Arnold supports encapsulation
		self["encapsulateSwitch"] = Gaffer.NameSwitch( "NameSwitch" )
		self["encapsulateSwitch"].setup( Gaffer.BoolPlug( "value", ) )
		self["encapsulateSwitch"]["selector"].setInput( self["renderer"] )
		self["encapsulateSwitch"]["in"][0]["name"].setValue( '*' )
		self["encapsulateSwitch"]["in"][0]["value"].setValue( False )
		self["encapsulateSwitch"]["in"][1]["name"].setValue( 'Arnold' )
		self["encapsulateSwitch"]["in"][1]["value"].setValue( True )

		self["instancer"]["encapsulate"].setInput( self["encapsulateSwitch"]["out"]["value"] )

		self["enabledOptionQuery"] = GafferScene.OptionQuery()
		self["enabledOptionQuery"]["scene"].setInput( self["in"] )
		self["enabledOptionQuery"].addQuery( Gaffer.BoolPlug( "value" ), "gafferUSD:pointInstancerAdaptor:enabled" )

		self["defaultEnabledExpression"] = Gaffer.Expression()
		self["defaultEnabledExpression"].setExpression( 'parent["enabledOptionQuery"]["queries"]["query0"]["value"] = parent["renderer"] in parent["enabledRenderers"]' )

		self["invisAttribute"]["enabled"].setInput( self["enabledOptionQuery"]["out"][0]["value"] )
		self["instancer"]["enabled"].setInput( self["enabledOptionQuery"]["out"][0]["value"] )

		self["out"].setInput( self["instancer"]["out"] )

IECore.registerRunTimeTyped( _PointInstancerAdaptor, typeName = "GafferUSD::_PointInstancerAdaptor" )
