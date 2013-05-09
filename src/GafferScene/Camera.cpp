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

#include "IECore/Camera.h"
#include "IECore/Transform.h"

#include "GafferScene/Camera.h"

using namespace Gaffer;
using namespace GafferScene;
using namespace Imath;

IE_CORE_DEFINERUNTIMETYPED( Camera );

size_t Camera::g_firstPlugIndex = 0;

Camera::Camera( const std::string &name )
	:	ObjectSource( name, "camera" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "projection", Plug::In, "perspective" ) );
	addChild( new FloatPlug( "fieldOfView", Plug::In, 50.0f, 0.0f, 180.0f ) );
	addChild( new V2fPlug( "clippingPlanes", Plug::In, V2f( 0.01, 100000 ), V2f( 0 ) ) );
}

Camera::~Camera()
{
}

Gaffer::StringPlug *Camera::projectionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Camera::projectionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex  );
}

Gaffer::FloatPlug *Camera::fieldOfViewPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *Camera::fieldOfViewPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

Gaffer::V2fPlug *Camera::clippingPlanesPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::V2fPlug *Camera::clippingPlanesPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 2 );
}

void Camera::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );
	
	if(
		input == projectionPlug() ||
		input == fieldOfViewPlug() ||
		input->parent<Plug>() == clippingPlanesPlug()
	)
	{
		outputs.push_back( sourcePlug() );
	}
}

void Camera::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	projectionPlug()->hash( h );
	fieldOfViewPlug()->hash( h );
	clippingPlanesPlug()->hash( h );
}

IECore::ConstObjectPtr Camera::computeSource( const Context *context ) const
{
	IECore::CameraPtr result = new IECore::Camera;
	result->parameters()["projection"] = new IECore::StringData( projectionPlug()->getValue() );
	result->parameters()["projection:fov"] = new IECore::FloatData( fieldOfViewPlug()->getValue() );
	result->parameters()["clippingPlanes"] = new IECore::V2fData( clippingPlanesPlug()->getValue() );
	return result;
}
