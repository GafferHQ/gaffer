//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferScene/ObjectToScene.h"

#include "IECore/NullObject.h"

using namespace Gaffer;
using namespace GafferScene;
using namespace IECore;

GAFFER_NODE_DEFINE_TYPE( ObjectToScene );

size_t ObjectToScene::g_firstPlugIndex = 0;

ObjectToScene::ObjectToScene( const std::string &name )
	:	ObjectSource( name, "object" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ObjectPlug( "object", Plug::In, IECore::NullObject::defaultNullObject() ) );
}

ObjectToScene::~ObjectToScene()
{
}

Gaffer::ObjectPlug *ObjectToScene::objectPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex );
}

const Gaffer::ObjectPlug *ObjectToScene::objectPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex );
}

void ObjectToScene::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );

	if( input == objectPlug() )
	{
		outputs.push_back( sourcePlug() );
	}
}

void ObjectToScene::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	objectPlug()->hash( h );
}

IECore::ConstObjectPtr ObjectToScene::computeSource( const Context *context ) const
{
	return objectPlug()->getValue();
}
