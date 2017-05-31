//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "IECore/MeshPrimitive.h"
#include "IECore/PointsPrimitive.h"
#include "IECore/AngleConversion.h"
#include "Gaffer/StringPlug.h"

#include "GafferScene/MeshToPoints.h"

#include "ImathMatrixAlgo.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( MeshToPoints );

size_t MeshToPoints::g_firstPlugIndex = 0;

MeshToPoints::MeshToPoints( const std::string &name )
	:	SceneElementProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "type", Plug::In, "particle" ) );
	addChild( new StringPlug( "mode", Plug::In, "vertex") );
	addChild( new FloatPlug( "rotation", Plug::In, 0.0f) );

	// Fast pass-throughs for things we don't modify
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
}

MeshToPoints::~MeshToPoints()
{
}

Gaffer::StringPlug *MeshToPoints::typePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *MeshToPoints::typePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *MeshToPoints::modePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1);
}

const Gaffer::StringPlug *MeshToPoints::modePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1);
}

Gaffer::FloatPlug *MeshToPoints::rotationPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2);
}
const Gaffer::FloatPlug *MeshToPoints::rotationPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2);
}

void MeshToPoints::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( input == typePlug() || input == modePlug() || input == rotationPlug()  )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
	else if( input == outPlug()->objectPlug() )
	{
		outputs.push_back( outPlug()->boundPlug() );
	}
}

bool MeshToPoints::processesBound() const
{
	return true;
}

void MeshToPoints::hashProcessedBound( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	hashProcessedObject( path, context, h );
}

Imath::Box3f MeshToPoints::computeProcessedBound( const ScenePath &path, const Gaffer::Context *context, const Imath::Box3f &inputBound ) const
{
	ConstObjectPtr object = outPlug()->objectPlug()->getValue();
	if( const PointsPrimitive *points = runTimeCast<const PointsPrimitive>( object.get() ) )
	{
		return points->bound();
	}
	return inputBound;
}

bool MeshToPoints::processesObject() const
{
	return true;
}

void MeshToPoints::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	typePlug()->hash( h );
	modePlug()->hash( h );
	rotationPlug()->hash( h );
}

IECore::ConstObjectPtr MeshToPoints::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	const MeshPrimitive *mesh = runTimeCast<const MeshPrimitive>( inputObject.get() );
	if( !mesh )
	{
		return inputObject;
	}

	IECore::PointsPrimitivePtr result;

	if( modePlug()->getValue() == "polygon" )
	{

		float rotation = IECore::degreesToRadians(rotationPlug()->getValue());
		size_t numFaces = mesh->numFaces();
		IECore::V3fVectorDataPtr positions = new IECore::V3fVectorData();
		IECore::V3fVectorData::ValueType &positionVector = positions->writable();

		positionVector.resize( numFaces );

		const IECore::V3fVectorData *meshPositions = mesh->variableData<IECore::V3fVectorData>( "P" );

		QuatfVectorDataPtr orientationData = new QuatfVectorData();
		orientationData->writable().resize( numFaces );

		IntVectorDataPtr idData = new IntVectorData();
		idData->writable().resize(numFaces);

		size_t vertex = 0;
		for( size_t f = 0; f < numFaces; ++f )
		{
			int positionIndex = mesh->vertexIds()->readable()[vertex];

			Imath::V3f p0 = meshPositions->readable()[positionIndex + 0];
			Imath::V3f p1 = meshPositions->readable()[positionIndex + 1];
			Imath::V3f p2 = meshPositions->readable()[positionIndex + 2];

			positionVector[f] = p0;

			Imath::V3f d02 = p2 - p0;
			Imath::V3f d01 = p1 - p0;

			Imath::V3f n = d02.cross( d01 );
			n.normalize();
			Imath::V3f t = d01;
			t.normalize();

			Imath::V3f b = n.cross( t );
			b.normalize();

			//@formatter:off
			Imath::M44f matrix(
				t.x, t.y, t.z, 0.0f,
				b.x, b.y, b.z, 0.0f,
				n.x, n.y, n.z, 0.0f,
				0.0f, 0.0f, 0.0f, 1.0f
			);
			//@formatter:on

			Imath::M44f preRotation;
			preRotation.setAxisAngle(Imath::V3f(0.0f, 0.0f, 1.0f), rotation);

			matrix = preRotation * matrix;
			Imath::Quatf quat = Imath::extractQuat( matrix );

			orientationData->writable()[f] = quat;
			idData->writable()[f] = (int) f;
			vertex += mesh->verticesPerFace()->readable()[f];
		}

		result = new PointsPrimitive( positions );
		result->variables["orient"] = PrimitiveVariable( PrimitiveVariable::Vertex, orientationData );
		result->variables["id"] = PrimitiveVariable( PrimitiveVariable::Vertex, idData );
	}
	else
	{
		result = new PointsPrimitive( mesh->variableSize( PrimitiveVariable::Vertex ) );
		for( PrimitiveVariableMap::const_iterator it = mesh->variables.begin(), eIt = mesh->variables.end(); it != eIt; ++it )
		{
			PrimitiveVariable::Interpolation interpolation = it->second.interpolation;
			switch( interpolation )
			{
				case PrimitiveVariable::Uniform :
				case PrimitiveVariable::FaceVarying :
					// Skip these, since they make no sense
					// on points.
					continue;
				case PrimitiveVariable::Varying :
					interpolation = PrimitiveVariable::Vertex;
					break;
				default :
					break;
			}

			result->variables[it->first] = PrimitiveVariable( interpolation, it->second.data );
		}
	}

	result->variables["type"] = PrimitiveVariable( PrimitiveVariable::Constant, new StringData( typePlug()->getValue() ) );

	return result;
}
