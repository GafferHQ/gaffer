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


#include "GafferScene/UDIMQuery.h"
#include "GafferScene/SceneAlgo.h"

#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/Output.h"
#include "IECore/StringAlgo.h"

#include "tbb/concurrent_vector.h"
#include "boost/algorithm/string/replace.hpp"
#include "boost/container/flat_set.hpp"


using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( UDIMQuery );

size_t UDIMQuery::g_firstPlugIndex = 0;

UDIMQuery::UDIMQuery( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "in", Plug::In ) );
	addChild( new StringPlug( "uvSet", Plug::In, "uv" ) );
	addChild( new StringPlug( "attributes", Plug::In, "" ) );
	addChild( new FilterPlug( "filter" ) );
	addChild( new CompoundObjectPlug( "out", Plug::Out, new IECore::CompoundObject(), Plug::Flags::Default ) );
}

UDIMQuery::~UDIMQuery()
{
}

GafferScene::ScenePlug *UDIMQuery::inPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const GafferScene::ScenePlug *UDIMQuery::inPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *UDIMQuery::uvSetPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *UDIMQuery::uvSetPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *UDIMQuery::attributesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *UDIMQuery::attributesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

GafferScene::FilterPlug *UDIMQuery::filterPlug()
{
	return getChild<FilterPlug>( g_firstPlugIndex + 3 );
}

const GafferScene::FilterPlug *UDIMQuery::filterPlug() const
{
	return getChild<FilterPlug>( g_firstPlugIndex + 3 );
}

Gaffer::CompoundObjectPlug *UDIMQuery::outPlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::CompoundObjectPlug *UDIMQuery::outPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 4 );
}

void UDIMQuery::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if(
		input == uvSetPlug() ||
		input == attributesPlug() ||
		input == filterPlug() ||
		input == inPlug()->objectPlug() ||
		input == inPlug()->attributesPlug() ||
		input == inPlug()->childNamesPlug()
	)
	{
		outputs.push_back( outPlug() );
	}
}

namespace
{

struct InfoHashAccumulator
{
	bool operator()( const GafferScene::ScenePlug *in, const GafferScene::ScenePlug::ScenePath &path )
	{
		IECore::MurmurHash locationHash;
		in->objectPlug()->hash( locationHash );
		locationHash.append( in->fullAttributesHash( path ) );
		std::string pathStr;
		ScenePlug::pathToString( path, pathStr );
		m_hashes.push_back( std::pair<std::string, IECore::MurmurHash>( pathStr, locationHash ) );
		return true;
	}

	void appendHash( IECore::MurmurHash &h )
	{
		std::sort( m_hashes.begin(), m_hashes.end() );
		for( const auto &i : m_hashes )
		{
			h.append( i.first );
			h.append( i.second );
		}
	}

	tbb::concurrent_vector< std::pair< std::string, IECore::MurmurHash > > m_hashes;
};

} // namespace

void UDIMQuery::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( output, context, h );
	if( output == outPlug() )
	{
		uvSetPlug()->hash( h );
		attributesPlug()->hash( h );

		InfoHashAccumulator f;
		GafferScene::SceneAlgo::filteredParallelTraverse( inPlug(), filterPlug(), f );
		f.appendHash( h );
	}
}

namespace {

struct BakeInfoData
{
	std::string mesh;
	boost::container::flat_set<int> udims;
	CompoundObjectPtr attributes;
};

struct InfoDataAccumulator
{
	InfoDataAccumulator( std::string uvSet, std::string attributeNames )
		: m_uvSet( uvSet ), m_attributeNames( attributeNames )
	{
	}

	bool operator()( const GafferScene::ScenePlug *in, const GafferScene::ScenePlug::ScenePath &path )
	{
		IECore::CompoundObjectPtr locationDict;

		IECore::ConstObjectPtr object = in->objectPlug()->getValue();
		const IECoreScene::MeshPrimitive *meshPrimitive = runTimeCast<const IECoreScene::MeshPrimitive>( object.get() );
		if( !meshPrimitive )
		{
			return true;
		}

		// First check if there are face-varying UVs
		bool faceVarying = true;
		auto uvs = meshPrimitive->variableIndexedView<IECore::V2fVectorData>( m_uvSet,  IECoreScene::PrimitiveVariable::FaceVarying );
		if( !uvs )
		{
			// Next check for vertex UVs
			faceVarying = false;
			uvs = meshPrimitive->variableIndexedView<IECore::V2fVectorData>( m_uvSet,  IECoreScene::PrimitiveVariable::Vertex );
		}

		if( !uvs )
		{
			// No face-varying or vertex UVs
			return true;
		}

		std::string pathString;
		ScenePlug::pathToString( path, pathString );
		unsigned int targetSize = meshPrimitive->variableSize( faceVarying ? IECoreScene::PrimitiveVariable::FaceVarying : IECoreScene::PrimitiveVariable::Vertex );
		if( uvs->size() != targetSize )
		{
			throw IECore::Exception(
				boost::str(
					boost::format(
						"Cannot query UDIMs.  Bad uvs at location %s.  Required count %i but found %i."
					) % pathString % targetSize % uvs->size()
				)
			);
		}

		const IntVectorData *vertsPerFaceData = meshPrimitive->verticesPerFace();
		const std::vector<int> &vertsPerFace = vertsPerFaceData->readable();

		BakeInfoData &info = *m_data.grow_by( 1 );
		info.mesh = pathString;

		// We check the center UVs of each face, because the edge uvs could lie directly on a UDIM boundary,
		// and without checking adjacency information, it would be impossible to tell which UDIM the edge
		// belongs to.  Checking face centers is fairly simple, and is completely accurate except in extreme
		// cases of polygons spanning multiple UDIMs, which is not done according to UDIM conventions.
		int faceVertId = 0;
		for( int numVerts : vertsPerFace )
		{
			Imath::V2f accum = Imath::V2f(0);
			if( faceVarying )
			{
				for( int i = 0; i < numVerts; i++ )
				{
					accum += (*uvs)[faceVertId];
					faceVertId++;
				}
			}
			else
			{
				for( int i = 0; i < numVerts; i++ )
				{
					accum += (*uvs)[ meshPrimitive->vertexIds()->readable()[faceVertId] ];
					faceVertId++;
				}
			}
			Imath::V2f centerUV = accum / numVerts;
			int udim = 1001 + int( floor( centerUV[0] ) ) + 10 * int( floor( centerUV[1] ) );

			info.udims.insert( udim );
		}

		info.attributes = new CompoundObject();
		if( m_attributeNames.size() )
		{
			IECore::ConstCompoundObjectPtr inAttributes = in->fullAttributes( path );
			for( const auto &i : inAttributes->members() )
			{
				if( StringAlgo::matchMultiple( i.first, m_attributeNames ) )
				{
					info.attributes->members()[ i.first ] = i.second;
				}
			}
		}

		return true;
	}

	std::string m_uvSet;
	IECore::StringAlgo::MatchPattern m_attributeNames;
	tbb::concurrent_vector< BakeInfoData > m_data;
};

} // namespace

void UDIMQuery::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == outPlug() )
	{
		InfoDataAccumulator f( uvSetPlug()->getValue(), attributesPlug()->getValue() );
		GafferScene::SceneAlgo::filteredParallelTraverse( inPlug(), filterPlug(), f );

		IECore::CompoundObjectPtr result = new IECore::CompoundObject();

		for( const auto &i : f.m_data )
		{
			for( int udim : i.udims )
			{
				std::string udimStr = std::to_string( udim );

				CompoundObjectPtr udimEntry = result->member<CompoundObject>(
					udimStr, /* throwExceptions = */ false, /* createIfMissing = */ true
				);

				// Result treated as const anyway, so this is safe.
				udimEntry->members()[i.mesh] = const_cast<CompoundObject*>( i.attributes.get() );
			}
		}
		static_cast<CompoundObjectPlug *>( output )->setValue( result );
	}
	else
	{
		ComputeNode::compute( output, context );
	}
}
