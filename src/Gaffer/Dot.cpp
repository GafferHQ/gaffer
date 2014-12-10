//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#include "Gaffer/Dot.h"
#include "Gaffer/Metadata.h"

using namespace IECore;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( Dot );

static InternedString g_inPlugName( "in" );
static InternedString g_outPlugName( "out" );
static InternedString g_nodulePositionName( "nodeGadget:nodulePosition" );

Dot::Dot( const std::string &name )
	:	DependencyNode( name )
{
}

Dot::~Dot()
{
}

void Dot::setup( const Plug *plug )
{
	if( const Plug *inputPlug = plug->getInput<Plug>() )
	{
		// We'd prefer to set up based on an input plug if possible - see comments
		// in DotNodeGadgetTest.testCustomNoduleTangentsPreferInputIfAvailable().
		plug = inputPlug;
	}

	Gaffer::PlugPtr in = plug->createCounterpart( g_inPlugName, Plug::In );
	Gaffer::PlugPtr out = plug->createCounterpart( g_outPlugName, Plug::Out );

	in->setFlags( Plug::Dynamic, true );
	out->setFlags( Plug::Dynamic, true );

	// Set up Metadata so our plugs appear in the right place. We must do this now rather
	// than later because the NodeGraph will add a Nodule for the plug as soon as the plug
	// is added as a child.

	ConstStringDataPtr nodulePosition;
	for( const Plug *metadataPlug = plug; metadataPlug; metadataPlug = metadataPlug->parent<Plug>() )
	{
		if( nodulePosition = Metadata::plugValue<StringData>( metadataPlug, g_nodulePositionName ) )
		{
			break;
		}
	}

	if( nodulePosition )
	{
		const std::string &position = nodulePosition->readable();
		std::string oppositePosition;
		if( position == "left" )
		{
			oppositePosition = "right";
		}
		else if( position == "right" )
		{
			oppositePosition = "left";
		}
		else if( position == "bottom" )
		{
			oppositePosition = "top";
		}
		else
		{
			oppositePosition = "bottom";
		}

		Metadata::registerPlugValue(
			plug->direction() == Plug::In ? in.get() : out.get(),
			g_nodulePositionName, nodulePosition
		);
		Metadata::registerPlugValue(
			plug->direction() == Plug::In ? out.get() : in.get(),
			g_nodulePositionName, new StringData( oppositePosition )
		);
	}

	setChild( g_inPlugName, in );
	setChild( g_outPlugName, out );

	out->setInput( in );
}

void Dot::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	DependencyNode::affects( input, outputs );
}

Plug *Dot::correspondingInput( const Plug *output )
{
	if( output == outPlug<Plug>() )
	{
		return inPlug<Plug>();
	}
	return DependencyNode::correspondingInput( output );
}

const Plug *Dot::correspondingInput( const Plug *output ) const
{
	if( output == outPlug<Plug>() )
	{
		return inPlug<Plug>();
	}
	return DependencyNode::correspondingInput( output );
}
