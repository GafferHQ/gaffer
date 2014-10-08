//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/StringAlgo.h"

#include "GafferScene/AttributeProcessor.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( AttributeProcessor );

size_t AttributeProcessor::g_firstPlugIndex = 0;

AttributeProcessor::AttributeProcessor( const std::string &name )
	:	SceneElementProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "names" ) );
	addChild( new BoolPlug( "invertNames" ) );

	// Fast pass-throughs for things we don't modify
	outPlug()->objectPlug()->setInput( inPlug()->objectPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
}

AttributeProcessor::~AttributeProcessor()
{
}

Gaffer::StringPlug *AttributeProcessor::namesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *AttributeProcessor::namesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *AttributeProcessor::invertNamesPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *AttributeProcessor::invertNamesPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

void AttributeProcessor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( input == namesPlug() || input == invertNamesPlug() )
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}
}

bool AttributeProcessor::processesAttributes() const
{
	bool invert = invertNamesPlug()->getValue();
	if( invert )
	{
		// we don't know if we're modifying the attributes till we find out what
		// names they have.
		return true;
	}
	else
	{
		// if there are no names, then we know we're not modifying the attributes.
		std::string names = namesPlug()->getValue();
		return names.size();
	}
}

void AttributeProcessor::hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	namesPlug()->hash( h );
	invertNamesPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr AttributeProcessor::computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputAttributes ) const
{
	if( inputAttributes->members().empty() )
	{
		return inputAttributes;
	}

	const std::string names = namesPlug()->getValue();
	const bool invert = invertNamesPlug()->getValue();

	CompoundObjectPtr result = new CompoundObject;
	for( CompoundObject::ObjectMap::const_iterator it = inputAttributes->members().begin(), eIt = inputAttributes->members().end(); it != eIt; ++it )
	{
		ConstObjectPtr attribute = it->second;
		if( matchMultiple( it->first, names ) != invert )
		{
			attribute = processAttribute( path, context, it->first, attribute.get() );
		}

		if( attribute )
		{
			result->members().insert(
				CompoundObject::ObjectMap::value_type(
					it->first,
					// cast is ok - result is const immediately on
					// returning from this function, and attribute will
					// therefore not be modified.
					boost::const_pointer_cast<Object>( attribute )
				)
			);
		}
	}

	return result;
}
