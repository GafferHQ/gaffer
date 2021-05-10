//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferCortex/ParameterHandler.h"

#include "Gaffer/GraphComponent.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ValuePlug.h"

#include "IECore/CompoundObject.h"
#include "IECore/SimpleTypedData.h"

using namespace IECore;

using namespace GafferCortex;

ParameterHandler::ParameterHandler()
{
}

ParameterHandler::~ParameterHandler()
{
}

IECore::MurmurHash ParameterHandler::hash() const
{
	IECore::MurmurHash result;
	const Gaffer::Plug *p = plug();
	for( Gaffer::ValuePlug::RecursiveIterator it( p ); !it.done(); ++it )
	{
		result.append( (*it)->relativeName( p ) );
		(*it)->hash( result );
	}
	return result;
}

void ParameterHandler::setupPlugFlags( Gaffer::Plug *plug, unsigned flags )
{
	plug->setFlags( flags );

	const CompoundObject *ud = parameter()->userData()->member<CompoundObject>( "gaffer" );
	if( ud )
	{
		const BoolData *readOnly = ud->member<BoolData>( "readOnly" );
		if( readOnly )
		{
			Gaffer::MetadataAlgo::setReadOnly( plug, readOnly->readable() );
		}
	}
}

ParameterHandlerPtr ParameterHandler::create( IECore::ParameterPtr parameter )
{
	const CreatorMap &c = creators();
	IECore::TypeId typeId = parameter->typeId();
	while( typeId!=InvalidTypeId )
	{
		CreatorMap::const_iterator it = c.find( typeId );
		if( it!=c.end() )
		{
			return it->second( parameter );
		}
		typeId = RunTimeTyped::baseTypeId( typeId );
	}
	return nullptr;
}

void ParameterHandler::registerParameterHandler( IECore::TypeId parameterType, Creator creator )
{
	creators()[parameterType] = creator;
}

ParameterHandler::CreatorMap &ParameterHandler::creators()
{
	static CreatorMap m;
	return m;
}
