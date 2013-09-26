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

#include "IECore/Primitive.h"

#include "GafferScene/MapOffset.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( MapOffset );

size_t MapOffset::g_firstPlugIndex = 0;

MapOffset::MapOffset( const std::string &name )
	:	SceneElementProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new V2fPlug( "offset" ) );
	addChild( new IntPlug( "udim", Plug::In, 1001, 1001 ) );
	addChild( new StringPlug( "sName", Plug::In, "s" ) );
	addChild( new StringPlug( "tName", Plug::In, "t" ) );
}

MapOffset::~MapOffset()
{
}

Gaffer::V2fPlug *MapOffset::offsetPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex );
}

const Gaffer::V2fPlug *MapOffset::offsetPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *MapOffset::udimPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *MapOffset::udimPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *MapOffset::sNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *MapOffset::sNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *MapOffset::tNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *MapOffset::tNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

void MapOffset::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( 
		input->parent<Plug>() == offsetPlug() ||
		input == udimPlug() ||
		input == sNamePlug() ||
		input == tNamePlug()
	)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

bool MapOffset::processesObject() const
{
	return true;
}

void MapOffset::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{	
	offsetPlug()->hash( h );
	udimPlug()->hash( h );
	sNamePlug()->hash( h );
	tNamePlug()->hash( h );
}

IECore::ConstObjectPtr MapOffset::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	// early out if it's not a primitive
	const Primitive *inputPrimitive = runTimeCast<const Primitive>( inputObject.get() );
	if( !inputPrimitive )
	{
		return inputObject;
	}

	// early out if the s/t names haven't been provided. 
	
	std::string sName = sNamePlug()->getValue();
	std::string tName = tNamePlug()->getValue();

	if( sName == "" || tName == "" )
	{
		return inputObject;
	}
	
	// do the work
	
	PrimitivePtr result = inputPrimitive->copy();
	
	V2f offset = offsetPlug()->getValue();
	
	const int udim = udimPlug()->getValue();
	offset.x += (udim - 1001) % 10;
	offset.y += (udim - 1001) / 10;
		
	if( FloatVectorDataPtr sData = result->variableData<FloatVectorData>( sName ) )
	{
		for( vector<float>::iterator it = sData->writable().begin(), eIt = sData->writable().end(); it != eIt; ++it )
		{
			*it += offset.x;		
		}
	}
	
	if( FloatVectorDataPtr tData = result->variableData<FloatVectorData>( tName ) )
	{
		for( vector<float>::iterator it = tData->writable().begin(), eIt = tData->writable().end(); it != eIt; ++it )
		{
			*it += offset.y;		
		}
	}
	
	return result;
}
