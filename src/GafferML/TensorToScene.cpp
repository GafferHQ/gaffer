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

#include "GafferScene/SceneAlgo.h"

#include "Gaffer/StringPlug.h"

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
	addChild( new Gaffer::StringPlug( "name", Gaffer::Plug::In, "tensor" ) );
	addChild( new Gaffer::StringPlug( "sets" ) );
	addChild( new Gaffer::TransformPlug( "transform" ) );

	addChild( new TensorPlug( "vertices" ) );
	addChild( new TensorPlug( "faces" ) );

}

TensorToScene::~TensorToScene()
{
}

Gaffer::StringPlug *TensorToScene::namePlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *TensorToScene::namePlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *TensorToScene::setsPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *TensorToScene::setsPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::TransformPlug *TensorToScene::transformPlug()
{
	return getChild<Gaffer::TransformPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::TransformPlug *TensorToScene::transformPlug() const
{
	return getChild<Gaffer::TransformPlug>( g_firstPlugIndex + 2 );
}

TensorPlug *TensorToScene::verticesTensorPlug()
{
	return getChild<TensorPlug>( g_firstPlugIndex + 3 );
}

const TensorPlug *TensorToScene::verticesTensorPlug() const
{
	return getChild<TensorPlug>( g_firstPlugIndex + 3 );
}

TensorPlug *TensorToScene::facesTensorPlug()
{
	return getChild<TensorPlug>( g_firstPlugIndex + 4 );
}

const TensorPlug *TensorToScene::facesTensorPlug() const
{
	return getChild<TensorPlug>( g_firstPlugIndex + 4 );
}

void TensorToScene::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneNode::affects( input, outputs );
	if ( input == verticesTensorPlug() )
	{
		outputs.push_back(outPlug()->boundPlug());
		outputs.push_back(outPlug()->objectPlug());
	}
	if ( input == facesTensorPlug() )
	{
		outputs.push_back(outPlug()->objectPlug());
	}
	else if( input == namePlug() )
	{
		outputs.push_back( outPlug()->childNamesPlug() );
		outputs.push_back( outPlug()->setPlug() );
	}
	else if( transformPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->transformPlug() );
		outputs.push_back( outPlug()->boundPlug() );
	}
	else if( input == setsPlug() )
	{
		outputs.push_back( outPlug()->setNamesPlug() );
		outputs.push_back( outPlug()->setPlug() );
	}

}

void TensorToScene::hashBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashBound( path, context, parent, h );
	verticesTensorPlug()->hash(h);
	if( path.size() == 0 )
	{
		h = parent->childBoundsPlug()->hash();
		transformPlug()->hash( h );

	}

}

Imath::Box3f TensorToScene::computeBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	ConstTensorDataPtr verticesTensorData = verticesTensorPlug()->getValue();
	const size_t count = verticesTensorData->value.GetTensorTypeAndShapeInfo().GetElementCount();
	const float *sourceData = verticesTensorData->value.GetTensorData<float>();

	Imath::Box3f result;
	for( size_t i = 0; i < count; i += 3 )
	{
		Imath::V3f v;
		for( size_t j = 0; j < 3; j++ )
		{
			v[j] = *( sourceData + ( i + j ) );
		}
		result.extendBy( v );
	}
	if( path.size() == 0 )
	{
		result = Imath::transform( result, transformPlug()->matrix() );
	}

	return result;
}

void TensorToScene::hashTransform( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashTransform( path, context, parent, h );
	if( path.size() == 1 )
	{
		transformPlug()->hash( h );
	}
	
}

Imath::M44f TensorToScene::computeTransform( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	if( path.size() == 1 )
	{
		return transformPlug()->matrix();
	}
	return Imath::M44f();
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
	if( path.size() == 0 )
	{
		SceneNode::hashChildNames( path, context, parent, h );
		namePlug()->hash( h );
		return;
	}
	h = parent->childNamesPlug()->defaultValue()->Object::hash();
}

IECore::ConstInternedStringVectorDataPtr TensorToScene::computeChildNames( const SceneNode::ScenePath &path, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	if( path.size() == 0 )
	{
		IECore::InternedStringVectorDataPtr result = new IECore::InternedStringVectorData();
		result->writable().push_back( validatedName() );
		return result;
	}
	return parent->childNamesPlug()->defaultValue();
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
	IECore::InternedStringVectorDataPtr result = new IECore::InternedStringVectorData;
	IECore::StringAlgo::tokenize( setsPlug()->getValue(), ' ', result->writable() );
	return result;
}

void TensorToScene::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const GafferScene::ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( setNameValid( setName ) )
	{
		SceneNode::hashSet( setName, context, parent, h );
		namePlug()->hash( h );
	}
	else
	{
		h = outPlug()->setPlug()->defaultValue()->Object::hash();
	}
}

IECore::ConstPathMatcherDataPtr TensorToScene::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const GafferScene::ScenePlug *parent ) const
{
	if( setNameValid( setName ) )
	{
		IECore::PathMatcherDataPtr result = new IECore::PathMatcherData;
		result->writable().addPath( ScenePlug::ScenePath( { validatedName() } ) );
		return result;
	}
	else
	{
		return outPlug()->setPlug()->defaultValue();
	}
}
IECore::InternedString TensorToScene::validatedName() const
{
	const IECore::InternedString name = namePlug()->getValue();
	if( name.string().size() )
	{
		SceneAlgo::validateName( name );
		return name;
	}
	else
	{
		/// \todo Why don't we just let `validateName()` throw for us instead?
		return "unnamed";
	}
}

bool TensorToScene::setNameValid( const IECore::InternedString &setName ) const
{
	std::vector<IECore::InternedString> setNames;
	IECore::StringAlgo::tokenize( setsPlug()->getValue(), ' ', setNames );
	return std::find( setNames.begin(), setNames.end(), setName ) != setNames.end();
}

