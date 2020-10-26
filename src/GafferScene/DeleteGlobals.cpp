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

#include "GafferScene/DeleteGlobals.h"

#include "Gaffer/StringPlug.h"

#include "IECore/StringAlgo.h"

#include "boost/algorithm/string/predicate.hpp"

using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( DeleteGlobals );

size_t DeleteGlobals::g_firstPlugIndex = 0;

DeleteGlobals::DeleteGlobals( const std::string &name )
	:	GlobalsProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "names" ) );
	addChild( new BoolPlug( "invertNames" ) );
}

DeleteGlobals::~DeleteGlobals()
{
}

Gaffer::StringPlug *DeleteGlobals::namesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *DeleteGlobals::namesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *DeleteGlobals::invertNamesPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *DeleteGlobals::invertNamesPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

void DeleteGlobals::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );

	if( input == namesPlug() || input == invertNamesPlug() )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

std::string DeleteGlobals::namePrefix() const
{
	return "";
}

void DeleteGlobals::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	namesPlug()->hash( h );
	invertNamesPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr DeleteGlobals::computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const
{
	if( inputGlobals->members().empty() )
	{
		return inputGlobals;
	}

	const std::string names = namesPlug()->getValue();
	const bool invert = invertNamesPlug()->getValue();
	if( !invert && !names.size() )
	{
		return inputGlobals;
	}

	const std::string prefix = namePrefix();

	IECore::CompoundObjectPtr result = new IECore::CompoundObject;
	for( IECore::CompoundObject::ObjectMap::const_iterator it = inputGlobals->members().begin(), eIt = inputGlobals->members().end(); it != eIt; ++it )
	{
		bool keep = true;
		if( boost::starts_with( it->first.c_str(), prefix ) )
		{
			if( IECore::StringAlgo::matchMultiple( it->first.c_str() + prefix.size(), names.c_str() ) != invert )
			{
				keep = false;
			}
		}
		if( keep )
		{
			result->members()[it->first] = it->second;
		}
	}

	return result;
}
