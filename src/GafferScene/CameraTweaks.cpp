//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/CameraTweaks.h"

#include "GafferScene/TweakPlug.h"

#include "IECoreScene/Camera.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( CameraTweaks );

size_t CameraTweaks::g_firstPlugIndex = 0;

CameraTweaks::CameraTweaks( const std::string &name )
	:	ObjectProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new TweaksPlug( "tweaks" ) );
}

CameraTweaks::~CameraTweaks()
{
}

GafferScene::TweaksPlug *CameraTweaks::tweaksPlug()
{
	return getChild<GafferScene::TweaksPlug>( g_firstPlugIndex );
}

const GafferScene::TweaksPlug *CameraTweaks::tweaksPlug() const
{
	return getChild<GafferScene::TweaksPlug>( g_firstPlugIndex );
}

bool CameraTweaks::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		ObjectProcessor::affectsProcessedObject( input ) ||
		tweaksPlug()->isAncestorOf( input )
	;
}

void CameraTweaks::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( tweaksPlug()->children().empty() )
	{
		h = inPlug()->objectPlug()->hash();
	}
	else
	{
		ObjectProcessor::hashProcessedObject( path, context, h );
		tweaksPlug()->hash( h );
	}
}

IECore::ConstObjectPtr CameraTweaks::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	IECoreScene::ConstCameraPtr inputCamera = IECore::runTimeCast<const IECoreScene::Camera>( inputObject );
	if( !inputCamera )
	{
		return inputObject;
	}

	const Plug *tweaksPlug = this->tweaksPlug();
	if( tweaksPlug->children().empty() )
	{
		return inputObject;
	}

	IECoreScene::CameraPtr result = inputCamera->copy();

	for( TweakPlug::Iterator tIt( tweaksPlug ); !tIt.done(); ++tIt )
	{
		if( !(*tIt)->enabledPlug()->getValue() )
		{
			continue;
		}
		const std::string name = (*tIt)->namePlug()->getValue();
		if( name.empty() )
		{
			continue;
		}

		if( name == "fieldOfView" )
		{
			InternedString internedName(name);
			CompoundDataPtr dummyParameters = new CompoundData();
			dummyParameters->writable()[internedName] = new FloatData( result->calculateFieldOfView()[0] );
			(*tIt)->applyTweak( dummyParameters.get(), TweakPlug::MissingMode::IgnoreOrReplace );
			FloatData *tweakedData = dummyParameters->member<FloatData>( internedName );
			if( tweakedData )
			{
				float fieldOfView = std::max( 0.0f, std::min( 179.99f, tweakedData->readable() ) );
				result->setFocalLengthFromFieldOfView( fieldOfView );
			}
		}
		else if( name == "apertureAspectRatio" )
		{
			InternedString internedName(name);
			Imath::V2f aperture = result->getAperture();
			CompoundDataPtr dummyParameters = new CompoundData();
			dummyParameters->writable()[internedName] = new FloatData( aperture[0] / aperture[1] );
			(*tIt)->applyTweak( dummyParameters.get(), TweakPlug::MissingMode::IgnoreOrReplace );
			FloatData *tweakedData = dummyParameters->member<FloatData>( internedName );
			if( tweakedData )
			{
				aperture[1] = aperture[0] / max( 0.0000001f, tweakedData->readable() );
				result->setAperture( aperture );
			}
		}
		else
		{
			(*tIt)->applyTweak( result->parametersData(), TweakPlug::MissingMode::IgnoreOrReplace );
		}
	}


	return result;
}
