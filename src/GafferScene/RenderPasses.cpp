//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/RenderPasses.h"

#include "Gaffer/TypedObjectPlug.h"

using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( RenderPasses );

const std::string g_passNamesOptionName = "option:renderPass:names";

size_t RenderPasses::g_firstPlugIndex = 0;

RenderPasses::RenderPasses( const std::string &name )
	:	GlobalsProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringVectorDataPlug( "names" ) );
}

RenderPasses::~RenderPasses()
{
}

Gaffer::StringVectorDataPlug *RenderPasses::namesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex );
}

const Gaffer::StringVectorDataPlug *RenderPasses::namesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex );
}

void RenderPasses::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );

	if( input == namesPlug() )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void RenderPasses::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	namesPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr RenderPasses::computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const
{
	IECore::ConstStringVectorDataPtr namesData = namesPlug()->getValue();
	const std::vector<std::string> &names = namesData->readable();
	if( !names.size() )
	{
		return inputGlobals;
	}

	IECore::CompoundObjectPtr result = new IECore::CompoundObject();
	result->members() = inputGlobals->members();

	if( auto data = result->member<IECore::StringVectorData>( g_passNamesOptionName ) )
	{
		auto copy = data->copy();
		copy->writable().erase(
			std::remove_if(
				copy->writable().begin(),
				copy->writable().end(),
				[&names]( const auto &elem )
				{
					return std::find(
						names.begin(),
						names.end(),
						elem
					) != names.end();
				}
			),
			copy->writable().end()
		);
		copy->writable().insert( copy->writable().end(), names.begin(), names.end() );

		result->members()[g_passNamesOptionName] = copy;
	}
	else
	{
		result->members()[g_passNamesOptionName] = const_cast<IECore::StringVectorData *>( namesData.get() );
	}

	return result;
}
