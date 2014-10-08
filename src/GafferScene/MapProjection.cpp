//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, John Haddon. All rights reserved.
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

#include "OpenEXR/ImathFun.h"

#include "IECore/Primitive.h"
#include "IECore/Camera.h"
#include "IECore/AngleConversion.h"

#include "GafferScene/MapProjection.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( MapProjection );

size_t MapProjection::g_firstPlugIndex = 0;

MapProjection::MapProjection( const std::string &name )
	:	SceneElementProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "camera" ) );
	addChild( new StringPlug( "sName", Plug::In, "s" ) );
	addChild( new StringPlug( "tName", Plug::In, "t" ) );
	
	// Fast pass-throughs for things we don't modify
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
}

MapProjection::~MapProjection()
{
}

Gaffer::StringPlug *MapProjection::cameraPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *MapProjection::cameraPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *MapProjection::sNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *MapProjection::sNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *MapProjection::tNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *MapProjection::tNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

void MapProjection::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if(
		input == cameraPlug() ||
		input == sNamePlug() ||
		input == tNamePlug() ||
		input == inPlug()->transformPlug()
	)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

bool MapProjection::processesObject() const
{
	return true;
}

void MapProjection::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePath cameraPath;
	ScenePlug::stringToPath( cameraPlug()->getValue(), cameraPath );

	h.append( inPlug()->objectHash( cameraPath ) );
	h.append( inPlug()->transformHash( cameraPath ) );

	inPlug()->transformPlug()->hash( h );
	sNamePlug()->hash( h );
	tNamePlug()->hash( h );
}

IECore::ConstObjectPtr MapProjection::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	// early out if it's not a primitive with a "P" variable
	const Primitive *inputPrimitive = runTimeCast<const Primitive>( inputObject.get() );
	if( !inputPrimitive )
	{
		return inputObject;
	}

	const V3fVectorData *pData = inputPrimitive->variableData<V3fVectorData>( "P" );
	if( !pData )
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

	// get the camera and early out if we can't find one

	ScenePath cameraPath;
	ScenePlug::stringToPath( cameraPlug()->getValue(), cameraPath );

	ConstCameraPtr constCamera = runTimeCast<const Camera>( inPlug()->object( cameraPath ) );
	if( !constCamera )
	{
		return inputObject;
	}

	M44f cameraMatrix = inPlug()->fullTransform( cameraPath );
	M44f objectMatrix = inPlug()->fullTransform( path );
	M44f objectToCamera = objectMatrix * cameraMatrix.inverse();

	CameraPtr camera = constCamera->copy();
	camera->addStandardParameters();
	float tanFOV = -1;
	if( camera->parametersData()->member<StringData>( "projection" )->readable() == "perspective" )
	{
		const float fov = camera->parametersData()->member<FloatData>( "projection:fov" )->readable();
		tanFOV = tan( degreesToRadians( fov / 2.0f ) ); // camera x coordinate at screen window x==1
	}

	const Box2f &screenWindow = camera->parametersData()->member<Box2fData>( "screenWindow" )->readable();

	// do the work

	PrimitivePtr result = inputPrimitive->copy();

	FloatVectorDataPtr sData = new FloatVectorData();
	FloatVectorDataPtr tData = new FloatVectorData();

	result->variables[sName] = PrimitiveVariable( PrimitiveVariable::Vertex, sData );
	result->variables[tName] = PrimitiveVariable( PrimitiveVariable::Vertex, tData );

	const vector<V3f> &p = pData->readable();
	vector<float> &s = sData->writable();
	vector<float> &t = tData->writable();
	s.reserve( p.size() );
	t.reserve( p.size() );

	for( size_t i = 0, e = p.size(); i < e; ++i )
	{
		V3f pCamera = p[i] * objectToCamera;
		V2f pScreen;
		if( tanFOV > 0.0f )
		{
			// perspective
			const float d = pCamera.z * tanFOV;
			pScreen = V2f( pCamera.x / d, pCamera.y / d );
		}
		else
		{
			// orthographic
			pScreen = V2f( pCamera.x, pCamera.y );
		}
		s.push_back( lerpfactor( pScreen.x, screenWindow.min.x, screenWindow.max.x ) );
		t.push_back( lerpfactor( pScreen.y, screenWindow.min.y, screenWindow.max.y ) );
	}

	return result;
}
