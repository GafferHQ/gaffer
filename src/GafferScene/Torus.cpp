//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "IECore/MeshPrimitive.h"

#include <cstdio>

#include "GafferScene/Torus.h"

using namespace Gaffer;
using namespace GafferScene;
using namespace Imath;
using namespace IECore;

IE_CORE_DEFINERUNTIMETYPED( Torus );

size_t Torus::g_firstPlugIndex = 0;

Torus::Torus( const std::string &name )
	:	ObjectSource( name, "torus" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FloatPlug( "innerRadius", Plug::In, 0.6, 0 ) );
	addChild( new FloatPlug( "outerRadius", Plug::In, 0.4, 0 ) );
	addChild( new V2iPlug( "divisions", Plug::In, V2i( 40, 20 ), V2i( 6, 6 ) ) );
}

Torus::~Torus()
{
}

Gaffer::FloatPlug *Torus::innerRadiusPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex );
}

const Gaffer::FloatPlug *Torus::innerRadiusPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *Torus::outerRadiusPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *Torus::outerRadiusPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

Gaffer::V2iPlug *Torus::divisionsPlug()
{
	return getChild<V2iPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::V2iPlug *Torus::divisionsPlug() const
{
	return getChild<V2iPlug>( g_firstPlugIndex + 2 );
}

void Torus::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );

	if ( input == innerRadiusPlug() || input == outerRadiusPlug() )
	{
		outputs.push_back( sourcePlug() );
	}
	else if ( input->parent<V2iPlug>() == divisionsPlug() )
	{
		outputs.push_back( sourcePlug() );
	}
}

void Torus::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	innerRadiusPlug()->hash( h );
	outerRadiusPlug()->hash( h );
	divisionsPlug()->hash( h );
}

IECore::ConstObjectPtr Torus::computeSource( const Context *context ) const
{
	float innerRadius = innerRadiusPlug()->getValue();
	float outerRadius = outerRadiusPlug()->getValue();

	return MeshPrimitive::createTorus( innerRadius, outerRadius, divisionsPlug()->getValue() );
}
