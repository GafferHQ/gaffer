//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/NameSwitch.h"

#include "Gaffer/NameValuePlug.h"
#include "Gaffer/StringPlug.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;

size_t NameSwitch::g_firstPlugIndex = 0;

GAFFER_NODE_DEFINE_TYPE( NameSwitch );

NameSwitch::NameSwitch( const std::string &name )
	:	Switch( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "selector" ) );
	addChild( new IntPlug( "__outIndex", Plug::Out ) );
	indexPlug()->setName( "__index" );
	indexPlug()->setInput( outIndexPlug() );
}

NameSwitch::~NameSwitch()
{
}

void NameSwitch::setup( const Plug *plug )
{
	if( inPlugs() )
	{
		throw IECore::Exception( "Switch already has an \"in\" plug." );
	}
	if( outPlug() )
	{
		throw IECore::Exception( "Switch already has an \"out\" plug." );
	}

	PlugPtr inElement = plug->createCounterpart( "value", Plug::In );
	inElement->setFlags( Plug::Serialisable, true );
	NameValuePlugPtr element = new NameValuePlug( "", inElement, /* defaultEnabled = */ true, "in0" );
	ArrayPlugPtr in = new ArrayPlug(
		"in",
		Plug::In,
		element,
		2,
		std::numeric_limits<size_t>::max(),
		Plug::Default,
		/* resizeWhenInputsChange = */ false
	);
	addChild( in );

	PlugPtr out = new NameValuePlug( "", plug->createCounterpart( "value", Plug::Out ), /* defaultEnabled = */ true, "out" );
	addChild( out );

	inPlugs()->getChild<NameValuePlug>( 0 )->namePlug()->setValue( "*" );
}

StringPlug *NameSwitch::selectorPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const StringPlug *NameSwitch::selectorPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

IntPlug *NameSwitch::outIndexPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const IntPlug *NameSwitch::outIndexPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

void NameSwitch::affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const
{
	Switch::affects( input, outputs );

	auto nameValuePlug = input->parent<NameValuePlug>();
	if(
		input == selectorPlug() ||
		(
			nameValuePlug && nameValuePlug->parent() == inPlugs() &&
			( input == nameValuePlug->namePlug() || input == nameValuePlug->enabledPlug() )
		)
	)
	{
		outputs.push_back( outIndexPlug() );
	}
}

void NameSwitch::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	Switch::hash( output, context, h );

	if( output == outIndexPlug() )
	{
		selectorPlug()->hash( h );
		const ArrayPlug *in = inPlugs();
		for( int i = 1, e = in->children().size(); i < e; ++i )
		{
			auto p = in->getChild<NameValuePlug>( i );
			p->enabledPlug()->hash( h );
			p->namePlug()->hash( h );
		}
	}
}

void NameSwitch::compute( ValuePlug *output, const Context *context ) const
{
	if( output == outIndexPlug() )
	{
		int outIndex = 0;
		const string selector = selectorPlug()->getValue();
		const ArrayPlug *in = inPlugs();
		for( int i = 1, e = in->children().size(); i < e; ++i )
		{
			auto p = in->getChild<NameValuePlug>( i );
			if( !p->enabledPlug()->getValue() )
			{
				continue;
			}
			const string name = p->namePlug()->getValue();
			if( !name.empty() && StringAlgo::matchMultiple( selector, name ) )
			{
				outIndex = i;
				break;
			}
		}

		static_cast<IntPlug *>( output )->setValue( outIndex );
		return;
	}

	Switch::compute( output, context );
}
