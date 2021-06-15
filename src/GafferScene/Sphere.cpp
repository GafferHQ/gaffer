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

#include "GafferScene/Sphere.h"

#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/SpherePrimitive.h"

using namespace Gaffer;
using namespace GafferScene;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;

GAFFER_NODE_DEFINE_TYPE( Sphere );

size_t Sphere::g_firstPlugIndex = 0;

Sphere::Sphere( const std::string &name )
	:	ObjectSource( name, "sphere" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "type", Plug::In, Sphere::Mesh, Sphere::Primitive, Sphere::Mesh ) );
	addChild( new FloatPlug( "radius", Plug::In, 1, 0 ) );
	addChild( new FloatPlug( "zMin", Plug::In, -1, -1, 1 ) );
	addChild( new FloatPlug( "zMax", Plug::In, 1, -1, 1 ) );
	addChild( new FloatPlug( "thetaMax", Plug::In, 360, 1e-4, 360 ) );
	addChild( new V2iPlug( "divisions", Plug::In, V2i( 20, 40 ), V2i( 3, 6 ) ) );
}

Sphere::~Sphere()
{
}

Gaffer::IntPlug *Sphere::typePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *Sphere::typePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *Sphere::radiusPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *Sphere::radiusPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

Gaffer::FloatPlug *Sphere::zMinPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::FloatPlug *Sphere::zMinPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

Gaffer::FloatPlug *Sphere::zMaxPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::FloatPlug *Sphere::zMaxPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

Gaffer::FloatPlug *Sphere::thetaMaxPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::FloatPlug *Sphere::thetaMaxPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

Gaffer::V2iPlug *Sphere::divisionsPlug()
{
	return getChild<V2iPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::V2iPlug *Sphere::divisionsPlug() const
{
	return getChild<V2iPlug>( g_firstPlugIndex + 5 );
}

void Sphere::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );

	if ( input == typePlug() || input == radiusPlug() || input == zMinPlug() || input == zMaxPlug() || input == thetaMaxPlug() )
	{
		outputs.push_back( sourcePlug() );
	}
	// divisions affects regardless of type because we don't want to call typePlug()->getValue()
	else if ( input->parent<V2iPlug>() == divisionsPlug() )
	{
		outputs.push_back( sourcePlug() );
	}
}

void Sphere::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	typePlug()->hash( h );
	radiusPlug()->hash( h );
	zMinPlug()->hash( h );
	zMaxPlug()->hash( h );
	thetaMaxPlug()->hash( h );
	divisionsPlug()->hash( h );
}

IECore::ConstObjectPtr Sphere::computeSource( const Context *context ) const
{
	float radius = radiusPlug()->getValue();
	float thetaMax = thetaMaxPlug()->getValue();
	float tmp = zMinPlug()->getValue();
	float zMax = zMaxPlug()->getValue();
	float zMin = std::min( tmp, zMax );
	zMax = std::max( tmp, zMax );

	if ( typePlug()->getValue() == Sphere::Primitive )
	{
		return new SpherePrimitive( radius, zMin, zMax, thetaMax );
	}
	else
	{
		return MeshPrimitive::createSphere( radius, zMin, zMax, thetaMax, divisionsPlug()->getValue(), context->canceller() );
	}
}
