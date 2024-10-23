//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Lucien Fostier All rights reserved.
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

#include "GafferML/TensorToScene.h"
#include "IECoreScene/MeshPrimitive.h"

#include "onnxruntime_cxx_api.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferML;

GAFFER_NODE_DEFINE_TYPE( TensorToScene );

size_t TensorToScene::g_firstPlugIndex = 0;

TensorToScene::TensorToScene( const std::string &name )
	:	SceneNode( name )
{

	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new TensorPlug( "vertices" ) );
	addChild( new TensorPlug( "faces" ) );

}

TensorToScene::~TensorToScene()
{
}

TensorPlug *TensorToScene::verticesTensorPlug()
{
	return getChild<TensorPlug>( g_firstPlugIndex );
}

const TensorPlug *TensorToScene::verticesTensorPlug() const
{
	return getChild<TensorPlug>( g_firstPlugIndex );
}


TensorPlug *TensorToScene::facesTensorPlug()
{
	return getChild<TensorPlug>( g_firstPlugIndex + 1 );
}

const TensorPlug *TensorToScene::facesTensorPlug() const
{
	return getChild<TensorPlug>( g_firstPlugIndex + 1 );
}


void TensorToScene::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneNode::affects( input, outputs );
	if ( input == verticesTensorPlug() )
	{
		outputs.push_back(outPlug()->boundPlug());
		outputs.push_back(outPlug()->transformPlug());
		outputs.push_back(outPlug()->attributesPlug());
		outputs.push_back(outPlug()->objectPlug());
		outputs.push_back(outPlug()->childNamesPlug());
	}
}

void TensorToScene::hashBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 0 )
	{
		h = parent->childBoundsPlug()->hash();
	}
	else
	{
		SceneNode::hashBound( path, context, parent, h );
		verticesTensorPlug()->hash(h);
	}

}

Imath::Box3f TensorToScene::computeBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	ConstTensorDataPtr verticesTensorData = verticesTensorPlug()->getValue();
	const size_t count = verticesTensorData->value.GetTensorTypeAndShapeInfo().GetElementCount();
	const float *sourceData = verticesTensorData->value.GetTensorData<float>();

	Imath::Box3f bound;
	for( size_t i = 0; i < count; i += 3 )
	{
		Imath::V3f v;
		for( size_t j = 0; j < 3; j++ )
		{
			v[j] = *( sourceData + ( i + j ) );
		}
		bound.extendBy( v );
	}

	return bound;
}

void TensorToScene::hashTransform( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashTransform( path, context, parent, h );
}

Imath::M44f TensorToScene::computeTransform( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	return outPlug()->transformPlug()->defaultValue();
}

void TensorToScene::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 1 )
	{
		SceneNode::hashAttributes( path, context, parent, h );
		return;
	}
	else if( path.size() == 2 )
	{
		SceneNode::hashAttributes( path, context, parent, h );
	}
	h = outPlug()->attributesPlug()->defaultValue()->Object::hash();
}

IECore::ConstCompoundObjectPtr TensorToScene::computeAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	if( path.size() == 1 )
	{
		CompoundObjectPtr result = new CompoundObject;

		return result;
	}
	else if( path.size() == 2 )
	{

		CompoundObjectPtr result = new CompoundObject;

		return result;
	}
	return outPlug()->attributesPlug()->defaultValue();
}

void TensorToScene::hashObject( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 2 )
	{
		SceneNode::hashObject( path, context, parent, h );
		h.append( path.back() );

	}
	else
	{
		h = outPlug()->objectPlug()->defaultValue()->hash();
	}
	h.append(verticesTensorPlug()->hash());
}

IECore::ConstObjectPtr TensorToScene::computeObject( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	ConstTensorDataPtr verticesTensorData = verticesTensorPlug()->getValue();
	const size_t count = verticesTensorData->value.GetTensorTypeAndShapeInfo().GetElementCount();
	const float *sourceData = verticesTensorData->value.GetTensorData<float>();

	ConstTensorDataPtr facesTensorData = facesTensorPlug()->getValue();
	const int64_t *sourceFacesData = facesTensorData->value.GetTensorData<int64_t>();

	// Copy out topology
	IntVectorDataPtr verticesPerFaceData = new IntVectorData;
	vector<int> &verticesPerFace = verticesPerFaceData->writable();

	IntVectorDataPtr vertexIdsData = new IntVectorData;
	vector<int> &vertexIds = vertexIdsData->writable();

	V3fVectorDataPtr pointsData = new V3fVectorData;
	vector<V3f> &points = pointsData->writable();

	for( size_t i = 0; i < count; i += 3 )
	{
		Imath::V3f v;
		for( size_t j = 0; j < 3; j++ )
		{
			v[j] = *( sourceData + ( i + j ) );
		}
		points.push_back( v );
	}

	int vertexPerFace = facesTensorData->value.GetTensorTypeAndShapeInfo().GetShape()[1];
	for( int i = 0; i < facesTensorData->value.GetTensorTypeAndShapeInfo().GetShape()[0]; i++ )
	{
		verticesPerFace.push_back(vertexPerFace);
		for ( int j = 0; j < vertexPerFace; j++ )
		{
			vertexIds.push_back( *( sourceFacesData + i * 3 + j ) );
		}
	}

	return new MeshPrimitive( verticesPerFaceData, vertexIdsData, "linear", pointsData );
}

void TensorToScene::hashChildNames( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashChildNames( path, context, parent, h );
}

IECore::ConstInternedStringVectorDataPtr TensorToScene::computeChildNames( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	if ( path.size() == 0)
	{
		IECore::InternedStringVectorDataPtr result = new IECore::InternedStringVectorData();
		auto& v = result->writable();
		v.push_back("smpl");
		return result;
	}
	return outPlug()->childNamesPlug()->defaultValue();
}

void TensorToScene::hashGlobals( const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = outPlug()->globalsPlug()->defaultValue()->Object::hash();
}

IECore::ConstCompoundObjectPtr TensorToScene::computeGlobals( const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	return outPlug()->globalsPlug()->defaultValue();
}

void TensorToScene::hashSetNames( const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = outPlug()->setNamesPlug()->defaultValue()->Object::hash();

}

IECore::ConstInternedStringVectorDataPtr TensorToScene::computeSetNames( const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	return outPlug()->setNamesPlug()->defaultValue();
}

void TensorToScene::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = outPlug()->setPlug()->defaultValue()->Object::hash();
}

IECore::ConstPathMatcherDataPtr TensorToScene::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	return outPlug()->setPlug()->defaultValue();
}
