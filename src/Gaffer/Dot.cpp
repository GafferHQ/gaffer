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
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/StringPlug.h"

using namespace IECore;
using namespace Gaffer;

GAFFER_NODE_DEFINE_TYPE( Dot );

static InternedString g_inPlugName( "in" );
static InternedString g_outPlugName( "out" );
static InternedString g_sectionName( "noduleLayout:section" );

size_t Dot::g_firstPlugIndex = 0;

Dot::Dot( const std::string &name )
	:	DependencyNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "labelType", Plug::In, None, None, Custom ) );
	addChild( new StringPlug( "label" ) );
}

Dot::~Dot()
{
}

void Dot::setup( const Plug *plug )
{
	const Plug *originalPlug = plug;

	const Plug *inputPlug = plug->getInput();
	if( plug->direction() == Gaffer::Plug::In && inputPlug != nullptr )
	{
		// We'd prefer to set up based on an input plug if possible - see comments
		// in DotNodeGadgetTest.testCustomNoduleTangentsPreferInputIfAvailable().
		plug = inputPlug;
	}

	Gaffer::PlugPtr in = plug->createCounterpart( g_inPlugName, Plug::In );
	Gaffer::PlugPtr out = plug->createCounterpart( g_outPlugName, Plug::Out );

	MetadataAlgo::copyColors( originalPlug , in.get() , /* overwrite = */ false );
	MetadataAlgo::copyColors( originalPlug , out.get() , /* overwrite = */ false );

	in->setFlags( Plug::Serialisable, true );
	out->setFlags( Plug::Serialisable, true );

	// Set up Metadata so our plugs appear in the right place. We must do this now rather
	// than later because the GraphEditor will add a Nodule for the plug as soon as the plug
	// is added as a child.

	ConstStringDataPtr sectionData;
	for( const Plug *metadataPlug = plug; metadataPlug; metadataPlug = metadataPlug->parent<Plug>() )
	{
		if( ( sectionData = Metadata::value<StringData>( metadataPlug, g_sectionName ) ) )
		{
			break;
		}
	}

	if( sectionData )
	{
		const std::string &section = sectionData->readable();
		std::string oppositeSection;
		if( section == "left" )
		{
			oppositeSection = "right";
		}
		else if( section == "right" )
		{
			oppositeSection = "left";
		}
		else if( section == "bottom" )
		{
			oppositeSection = "top";
		}
		else
		{
			oppositeSection = "bottom";
		}

		Metadata::registerValue(
			plug->direction() == Plug::In ? in.get() : out.get(),
			g_sectionName, sectionData
		);
		Metadata::registerValue(
			plug->direction() == Plug::In ? out.get() : in.get(),
			g_sectionName, new StringData( oppositeSection )
		);
	}

	setChild( g_inPlugName, in );
	setChild( g_outPlugName, out );

	out->setInput( in );
}

IntPlug *Dot::labelTypePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}
const IntPlug *Dot::labelTypePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

StringPlug *Dot::labelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}
const StringPlug *Dot::labelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

void Dot::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	DependencyNode::affects( input, outputs );
}

Plug *Dot::correspondingInput( const Plug *output )
{
	if( output == outPlug() )
	{
		return inPlug();
	}
	return DependencyNode::correspondingInput( output );
}

const Plug *Dot::correspondingInput( const Plug *output ) const
{
	if( output == outPlug() )
	{
		return inPlug();
	}
	return DependencyNode::correspondingInput( output );
}
