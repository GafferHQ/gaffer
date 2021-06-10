//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferScene/Plane.h"

#include "IECoreScene/MeshPrimitive.h"

using namespace Gaffer;
using namespace GafferScene;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;

GAFFER_NODE_DEFINE_TYPE( Plane );

size_t Plane::g_firstPlugIndex = 0;

Plane::Plane( const std::string &name )
	:	ObjectSource( name, "plane" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new V2fPlug( "dimensions", Plug::In, V2f( 1.0f ), V2f( 0.0f ) ) );
	addChild( new V2iPlug( "divisions", Plug::In, V2i( 1 ), V2i( 1 ) ) );
}

Plane::~Plane()
{
}

Gaffer::V2fPlug *Plane::dimensionsPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex );
}

const Gaffer::V2fPlug *Plane::dimensionsPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex );
}

Gaffer::V2iPlug *Plane::divisionsPlug()
{
	return getChild<V2iPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::V2iPlug *Plane::divisionsPlug() const
{
	return getChild<V2iPlug>( g_firstPlugIndex + 1 );
}

void Plane::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );

	if ( input->parent<V2fPlug>() == dimensionsPlug() || input->parent<V2iPlug>() == divisionsPlug() )
	{
		outputs.push_back( sourcePlug() );
	}
}

void Plane::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	dimensionsPlug()->hash( h );
	divisionsPlug()->hash( h );
}

IECore::ConstObjectPtr Plane::computeSource( const Context *context ) const
{
	V2f dimensions = dimensionsPlug()->getValue();
	return MeshPrimitive::createPlane( Box2f( -dimensions / 2.0f, dimensions / 2.0f ), divisionsPlug()->getValue(), context->canceller() );
}
