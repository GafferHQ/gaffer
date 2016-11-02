//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
#include "Gaffer/SubGraph.h"
#include "Gaffer/ArrayPlug.h"

#include "GafferScene/FilterPlug.h"
#include "GafferScene/Filter.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( FilterPlug );

FilterPlug::FilterPlug( const std::string &name, Direction direction, unsigned flags )
	:	IntPlug( name, direction, Filter::NoMatch, Filter::NoMatch, Filter::EveryMatch, flags )
{
}

FilterPlug::FilterPlug( const std::string &name, Direction direction, int defaultValue, int minValue, int maxValue, unsigned flags )
	:	IntPlug( name, direction, defaultValue, minValue, maxValue, flags )
{
}

FilterPlug::~FilterPlug()
{
}

bool FilterPlug::acceptsInput( const Gaffer::Plug *input ) const
{
	if( !IntPlug::acceptsInput( input ) )
	{
		return false;
	}

	if( !input )
	{
		return true;
	}

	if( input->isInstanceOf( staticTypeId() ) )
	{
		return true;
	}

	// Really we want to return false here, but we must provide backwards
	// compatibility for a time when FilterPlug didn't exist and IntPlugs
	// were used instead. Those old plugs may have been promoted onto Boxes
	// routed via Dots, or used within ArrayPlugs. In each case, dynamic
	// IntPlugs will have been created and serialised into the script, so
	// we must accept them.
	/// \todo Remove this compatibility for version 1.0.0.0?
	if( runTimeCast<const IntPlug>( input ) )
	{
		const Plug *p = input->source<Plug>();
		const Node *n = p->node();
		if( runTimeCast<const FilterPlug>( p ) || runTimeCast<const SubGraph>( n ) || runTimeCast<const Dot>( n ) )
		{
			return true;
		}
		if( const ArrayPlug *arrayPlug = input->parent<ArrayPlug>() )
		{
			if( arrayPlug && arrayPlug->getChild<FilterPlug>( 0 ) )
			{
				return true;
			}
		}
	}

	return false;
}

Gaffer::PlugPtr FilterPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new FilterPlug( name, direction, defaultValue(), minValue(), maxValue(), getFlags() );
}
