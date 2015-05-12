//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
#include "IECore/Light.h"
#include "IECore/ExternalProcedural.h"

#include "GafferScene/Parameters.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Parameters );

size_t Parameters::g_firstPlugIndex = 0;

Parameters::Parameters( const std::string &name )
	:	SceneElementProcessor( name, Filter::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new CompoundDataPlug( "parameters" ) );

	// Fast pass-throughs for things we don't modify
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
}

Parameters::~Parameters()
{
}

Gaffer::CompoundDataPlug *Parameters::parametersPlug()
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex );
}

const Gaffer::CompoundDataPlug *Parameters::parametersPlug() const
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex );
}

void Parameters::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( parametersPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

bool Parameters::processesObject() const
{
	return true;
}

void Parameters::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	parametersPlug()->hash( h );
}

IECore::ConstObjectPtr Parameters::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	if( !parametersPlug()->children().size() )
	{
		return inputObject;
	}

	ConstObjectPtr outputObject = inputObject;
	CompoundData *outputParameters = NULL;

	if( const Camera *camera = runTimeCast<const Camera>( inputObject.get() ) )
	{
		CameraPtr cameraCopy = camera->copy();
		outputParameters = cameraCopy->parametersData();
		outputObject = cameraCopy;
	}
	else if( const Light *light = runTimeCast<const Light>( inputObject.get() ) )
	{
		LightPtr lightCopy = light->copy();
		outputParameters = lightCopy->parametersData().get();
		outputObject = lightCopy;
	}
	else if( const ExternalProcedural *procedural = runTimeCast<const ExternalProcedural>( inputObject.get() ) )
	{
		ExternalProceduralPtr proceduralCopy = procedural->copy();
		outputParameters = proceduralCopy->parameters();
		outputObject = proceduralCopy;
	}

	if( outputParameters )
	{
		parametersPlug()->fillCompoundData( outputParameters->writable() );
	}

	return outputObject;
}
