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

#include "GafferScene/MeshDistortion.h"

#include "IECoreScene/MeshAlgo.h"
#include "IECoreScene/MeshPrimitive.h"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

size_t MeshDistortion::g_firstPlugIndex = 0;

GAFFER_NODE_DEFINE_TYPE( MeshDistortion );

MeshDistortion::MeshDistortion( const std::string &name )
	:	ObjectProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "position", Plug::In, "P" ) );
	addChild( new StringPlug( "referencePosition", Plug::In, "Pref" ) );
	addChild( new StringPlug( "uvSet", Plug::In, "uv" ) );
	addChild( new StringPlug( "distortion", Plug::In, "distortion" ) );
	addChild( new StringPlug( "uvDistortion", Plug::In, "uvDistortion" ) );
}

MeshDistortion::~MeshDistortion()
{
}

Gaffer::StringPlug *MeshDistortion::positionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *MeshDistortion::positionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *MeshDistortion::referencePositionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *MeshDistortion::referencePositionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *MeshDistortion::uvSetPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *MeshDistortion::uvSetPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *MeshDistortion::distortionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *MeshDistortion::distortionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *MeshDistortion::uvDistortionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *MeshDistortion::uvDistortionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

bool MeshDistortion::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		ObjectProcessor::affectsProcessedObject( input ) ||
		input == positionPlug() ||
		input == referencePositionPlug() ||
		input == uvSetPlug() ||
		input == distortionPlug() ||
		input == uvDistortionPlug()
	;
}

void MeshDistortion::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ObjectProcessor::hashProcessedObject( path, context, h );

	positionPlug()->hash( h );
	referencePositionPlug()->hash( h );
	uvSetPlug()->hash( h );
	distortionPlug()->hash( h );
	uvDistortionPlug()->hash( h );
}

IECore::ConstObjectPtr MeshDistortion::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const MeshPrimitive *mesh = runTimeCast<const MeshPrimitive>( inputObject );
	if( !mesh )
	{
		return inputObject;
	}

	const std::string position = positionPlug()->getValue();
	const std::string referencePosition = referencePositionPlug()->getValue();
	const std::string uvSet = uvSetPlug()->getValue();
	if( position.empty() || referencePosition.empty() || uvSet.empty() )
	{
		return inputObject;
	}

	const std::string distortion = distortionPlug()->getValue();
	const std::string uvDistortion = uvDistortionPlug()->getValue();
	if( distortion.empty() && uvDistortion.empty() )
	{
		return inputObject;
	}

	auto distortions = MeshAlgo::calculateDistortion(
		mesh,
		uvSet,
		referencePosition,
		position
	);

	MeshPrimitivePtr result = mesh->copy();

	if( !distortion.empty() )
	{
		result->variables[distortion] = distortions.first;
	}

	if( !uvDistortion.empty() )
	{
		result->variables[uvDistortion] = distortions.second;
	}

	return result;
}
