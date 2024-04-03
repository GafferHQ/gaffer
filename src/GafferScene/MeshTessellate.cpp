//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/MeshTessellate.h"

#include "Gaffer/Context.h"
#include "IECoreScene/MeshPrimitive.h"
#include "GafferScene/Private/IECoreScenePreview/MeshAlgo.h"


using namespace GafferScene;
using namespace Gaffer;
using namespace IECoreScene;
using namespace IECoreScenePreview;
using namespace IECore;

GAFFER_NODE_DEFINE_TYPE( MeshTessellate );

size_t MeshTessellate::g_firstPlugIndex = 0;

MeshTessellate::MeshTessellate( const std::string &name )
	:	ObjectProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "divisions", Gaffer::Plug::In, 1, 1 ) );
	addChild( new BoolPlug( "calculateNormals", Gaffer::Plug::In, false ) );
	addChild( new IntPlug( "scheme", Gaffer::Plug::In, (int)MeshAlgo::SubdivisionScheme::FromMesh, (int)MeshAlgo::SubdivisionScheme::First, (int)MeshAlgo::SubdivisionScheme::Last ) );
	addChild( new BoolPlug( "tessellatePolygons", Gaffer::Plug::In, false ) );

}

MeshTessellate::~MeshTessellate()
{
}

Gaffer::IntPlug *MeshTessellate::divisionsPlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 0);
}

const Gaffer::IntPlug *MeshTessellate::divisionsPlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 0);
}

Gaffer::BoolPlug *MeshTessellate::calculateNormalsPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *MeshTessellate::calculateNormalsPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *MeshTessellate::schemePlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *MeshTessellate::schemePlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *MeshTessellate::tessellatePolygonsPlug()
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *MeshTessellate::tessellatePolygonsPlug() const
{
	return getChild<Gaffer::BoolPlug>( g_firstPlugIndex + 3 );
}

bool MeshTessellate::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		ObjectProcessor::affectsProcessedObject( input ) ||
		input == divisionsPlug() ||
		input == calculateNormalsPlug() ||
		input == schemePlug() ||
		input == tessellatePolygonsPlug();
}



void MeshTessellate::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ObjectProcessor::hashProcessedObject( path, context, h );

	divisionsPlug()->hash( h );
	calculateNormalsPlug()->hash( h );
	schemePlug()->hash( h );
	tessellatePolygonsPlug()->hash( h );
}


IECore::ConstObjectPtr MeshTessellate::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const IECoreScene::MeshPrimitive *inputMesh = runTimeCast<const IECoreScene::MeshPrimitive>( inputObject );
	if( !inputMesh || !inputMesh->verticesPerFace()->readable().size() )
	{
		return inputObject;
	}

	IECoreScenePreview::MeshAlgo::SubdivisionScheme schemeValue =
		(IECoreScenePreview::MeshAlgo::SubdivisionScheme)schemePlug()->getValue();

	if(
		inputMesh->interpolation() == "linear" &&
		!tessellatePolygonsPlug()->getValue() &&
		schemeValue == IECoreScenePreview::MeshAlgo::SubdivisionScheme::FromMesh
	)
	{
		return inputObject;
	}


	return IECoreScenePreview::MeshAlgo::tessellateMesh(
		*inputMesh,
		divisionsPlug()->getValue(),
		calculateNormalsPlug()->getValue(),
		schemeValue,
		context->canceller()
	);
}

Gaffer::ValuePlug::CachePolicy MeshTessellate::processedObjectComputeCachePolicy() const
{
	return ValuePlug::CachePolicy::Default;
}
