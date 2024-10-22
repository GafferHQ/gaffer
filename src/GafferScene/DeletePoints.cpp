//////////////////////////////////////////////////////////////////////////
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
//      * Neither the name of Image Engine Design Inc nor the names of
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

#include "GafferScene/DeletePoints.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/PointsAlgo.h"
#include "IECoreScene/PointsPrimitive.h"

#include "boost/algorithm/string.hpp"

#include "fmt/format.h"

#include <unordered_set>

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

namespace {

// Copied from Instancer.cpp - maybe should be shared somehow if it gets reused?
struct IdData
{
	IdData() :
		intElements( nullptr ), int64Elements( nullptr )
	{
	}

	void initialize( const Primitive *primitive, const std::string &name, bool throwIfMissing = false )
	{
		if( const IntVectorData *intData = primitive->variableData<IntVectorData>( name ) )
		{
			intElements = &intData->readable();
		}
		else if( const Int64VectorData *int64Data = primitive->variableData<Int64VectorData>( name ) )
		{
			int64Elements = &int64Data->readable();
		}
		else if( throwIfMissing )
		{
			throw IECore::Exception( fmt::format( "DeletePoints : No primitive variable \"{}\" found of type IntVectorData or type Int64VectorData", name ) );
		}
	}

	size_t size() const
	{
		if( intElements )
		{
			return intElements->size();
		}
		else if( int64Elements )
		{
			return int64Elements->size();
		}
		else
		{
			return 0;
		}
	}

	int64_t element( size_t i ) const
	{
		if( intElements )
		{
			return (*intElements)[i];
		}
		else
		{
			return (*int64Elements)[i];
		}
	}

	const std::vector<int> *intElements;
	const std::vector<int64_t> *int64Elements;

};

} // namespace

GAFFER_NODE_DEFINE_TYPE( DeletePoints );

size_t DeletePoints::g_firstPlugIndex = 0;

DeletePoints::DeletePoints( const std::string &name )
	:	Deformer( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild(new IntPlug(
		"selectionMode", Plug::In,
		(int)SelectionMode::VertexPrimitiveVariable, (int)SelectionMode::VertexPrimitiveVariable, (int)SelectionMode::IdList
	) );
	addChild( new StringPlug( "points", Plug::In, "deletePoints" ) );
	addChild( new StringPlug( "idListVariable", Plug::In, "inactiveIds" ) );
	addChild( new Int64VectorDataPlug( "idList", Plug::In ) );
	addChild( new StringPlug( "id", Plug::In, "instanceId" ) );

	addChild( new BoolPlug( "invert", Plug::In, false ) );
	addChild( new BoolPlug( "ignoreMissingVariable", Plug::In, false ) );
}

DeletePoints::~DeletePoints()
{
}

Gaffer::IntPlug *DeletePoints::selectionModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *DeletePoints::selectionModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *DeletePoints::pointsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *DeletePoints::pointsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *DeletePoints::idListVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *DeletePoints::idListVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::Int64VectorDataPlug *DeletePoints::idListPlug()
{
	return getChild<Int64VectorDataPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::Int64VectorDataPlug *DeletePoints::idListPlug() const
{
	return getChild<Int64VectorDataPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *DeletePoints::idPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *DeletePoints::idPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::BoolPlug *DeletePoints::invertPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::BoolPlug *DeletePoints::invertPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 5 );
}

Gaffer::BoolPlug *DeletePoints::ignoreMissingVariablePlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::BoolPlug *DeletePoints::ignoreMissingVariablePlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 6 );
}

bool DeletePoints::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		Deformer::affectsProcessedObject( input ) ||
		input == selectionModePlug() ||
		input == pointsPlug() ||
		input == idListVariablePlug() ||
		input == idListPlug() ||
		input == idPlug() ||
		input == invertPlug() ||
		input == ignoreMissingVariablePlug()
	;
}

void DeletePoints::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Deformer::hashProcessedObject( path, context, h );
	selectionModePlug()->hash( h );
	pointsPlug()->hash( h );
	idListVariablePlug()->hash( h );
	idListPlug()->hash( h );
	idPlug()->hash( h );
	invertPlug()->hash( h );
	ignoreMissingVariablePlug()->hash( h );
}

IECore::ConstObjectPtr DeletePoints::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const PointsPrimitive *points = runTimeCast<const PointsPrimitive>( inputObject );
	if( !points )
	{
		return inputObject;
	}

	SelectionMode selectionMode = (SelectionMode)selectionModePlug()->getValue();

	IECoreScene::PrimitiveVariable toDelete;

	if( selectionMode == SelectionMode::VertexPrimitiveVariable )
	{
		std::string deletePrimVarName = pointsPlug()->getValue();

		if( deletePrimVarName.empty() )
		{
			return inputObject;
		}

		PrimitiveVariableMap::const_iterator it = points->variables.find( deletePrimVarName );
		if( it == points->variables.end() )
		{
			if( ignoreMissingVariablePlug()->getValue() )
			{
				return inputObject;
			}

			throw InvalidArgumentException( fmt::format( "DeletePoints : No primitive variable \"{}\" found", deletePrimVarName ) );
		}

		toDelete = it->second;
	}



	if( selectionMode == SelectionMode::IdListPrimitiveVariable || selectionMode == SelectionMode::IdList )
	{
		IdData idList;
		ConstInt64VectorDataPtr idListData;

		if( selectionMode == SelectionMode::IdListPrimitiveVariable )
		{
			std::string idListVarName = idListVariablePlug()->getValue();

			if( idListVarName.empty() )
			{
				return inputObject;
			}

			idList.initialize( points, idListVarName, /* throwIfMissing = */ true );
		}
		else
		{
			idListData = idListPlug()->getValue();
			idList.int64Elements = &idListData->readable();
		}


		IdData ids;
		ids.initialize( points, idPlug()->getValue() );

		size_t numPoints = points->getNumPoints();
		size_t numIds = idList.size();

		BoolVectorDataPtr inactiveData = new BoolVectorData();
		std::vector<bool> &inactive = inactiveData->writable();
		inactive.resize( numPoints, false );


		if( ids.size() )
		{
			std::unordered_set< int64_t > idSet;

			for( size_t i = 0; i < numIds; i++ )
			{
				idSet.insert( idList.element( i ) );

			}

			for( size_t j = 0; j < numPoints; j++ )
			{
				if( idSet.count( ids.element( j ) ) )
				{
					inactive[ j ] = true;
				}
			}
		}
		else
		{
			for( size_t i = 0; i < numIds; i++ )
			{
				inactive[ idList.element(i) ] = true;
			}
		}

		toDelete = IECoreScene::PrimitiveVariable( PrimitiveVariable::Interpolation::Vertex, inactiveData );
	}


	return PointsAlgo::deletePoints( points, toDelete, invertPlug()->getValue() );
}
