//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferScene/LocaliseAttributes.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( LocaliseAttributes );

size_t LocaliseAttributes::g_firstPlugIndex = 0;

LocaliseAttributes::LocaliseAttributes( const std::string &name )
	:	AttributeProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "attributes", Plug::In, "*" ) );
}

LocaliseAttributes::~LocaliseAttributes()
{
}

Gaffer::StringPlug *LocaliseAttributes::attributesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *LocaliseAttributes::attributesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

bool LocaliseAttributes::affectsProcessedAttributes( const Gaffer::Plug *input ) const
{
	return
		AttributeProcessor::affectsProcessedAttributes( input ) ||
		input == attributesPlug()
	;
}

void LocaliseAttributes::hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	AttributeProcessor::hashProcessedAttributes( path, context, h );
	h.append( inPlug()->fullAttributesHash( path ) );
	attributesPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr LocaliseAttributes::computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, const IECore::CompoundObject *inputAttributes ) const
{
	const string attributes = attributesPlug()->getValue();
	if( attributes.empty() )
	{
		return inputAttributes;
	}

	CompoundObjectPtr result = new CompoundObject;
	result->members() = inputAttributes->members();

	ConstCompoundObjectPtr fullAttributes = inPlug()->fullAttributes( path );
	for( const auto &attribute : fullAttributes->members() )
	{
		if( StringAlgo::matchMultiple( attribute.first, attributes ) )
		{
			result->members()[attribute.first] = attribute.second;
		}
	}

	return result;
}
