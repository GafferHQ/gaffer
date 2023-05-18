//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Scatter.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/MeshAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( Scatter );

size_t Scatter::g_firstPlugIndex = 0;

Scatter::Scatter( const std::string &name )
	:	BranchCreator( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	// "seeds" is the old default for backwards compatibility.  We set it to the new default of "scatter" using
	// a user default.
	addChild( new StringPlug( "name", Plug::In, "seeds" ) );

	addChild( new FloatPlug( "density", Plug::In, 1.0f, 0.0f ) );
	addChild( new StringPlug( "densityPrimitiveVariable" ) );
	addChild( new StringPlug( "referencePosition", Plug::In, "P" ) );
	addChild( new StringPlug( "uv", Plug::In, "uv" ) );
	addChild( new StringPlug( "primitiveVariables" ) );
	addChild( new StringPlug( "pointType", Plug::In, "gl:point" ) );
}

Scatter::~Scatter()
{
}

Gaffer::StringPlug *Scatter::namePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Scatter::namePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *Scatter::densityPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *Scatter::densityPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *Scatter::densityPrimitiveVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *Scatter::densityPrimitiveVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *Scatter::referencePositionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *Scatter::referencePositionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringPlug *Scatter::uvPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *Scatter::uvPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::StringPlug *Scatter::primitiveVariablesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::StringPlug *Scatter::primitiveVariablesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

Gaffer::StringPlug *Scatter::pointTypePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::StringPlug *Scatter::pointTypePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 6 );
}

bool Scatter::affectsBranchBound( const Gaffer::Plug *input ) const
{
	return input == inPlug()->boundPlug();
}

void Scatter::hashBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hashBranchBound( sourcePath, branchPath, context, h );
	h.append( inPlug()->boundHash( sourcePath ) );
}

Imath::Box3f Scatter::computeBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	Box3f b = inPlug()->bound( sourcePath );
	if( !b.isEmpty() )
	{
		// The PointsPrimitive we make has a default point width of 1,
		// so we must expand our bounding box to take that into account.
		b.min -= V3f( 0.5 );
		b.max += V3f( 0.5 );
	}
	return b;
}

bool Scatter::affectsBranchTransform( const Gaffer::Plug *input ) const
{
	return false;
}

void Scatter::hashBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hashBranchTransform( sourcePath, branchPath, context, h );
}

Imath::M44f Scatter::computeBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	return M44f();
}

bool Scatter::affectsBranchAttributes( const Gaffer::Plug *input ) const
{
	return false;
}

void Scatter::hashBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hashBranchAttributes( sourcePath, branchPath, context, h );
}

IECore::ConstCompoundObjectPtr Scatter::computeBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	return outPlug()->attributesPlug()->defaultValue();
}

bool Scatter::affectsBranchObject( const Gaffer::Plug *input ) const
{
	return
		input == inPlug()->objectPlug() ||
		input == densityPlug() ||
		input == densityPrimitiveVariablePlug() ||
		input == referencePositionPlug() ||
		input == uvPlug() ||
		input == primitiveVariablesPlug() ||
		input == pointTypePlug()
	;
}

void Scatter::hashBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() == 1 )
	{
		BranchCreator::hashBranchObject( sourcePath, branchPath, context, h );
		h.append( inPlug()->objectHash( sourcePath ) );
		densityPlug()->hash( h );
		densityPrimitiveVariablePlug()->hash( h );
		referencePositionPlug()->hash( h );
		uvPlug()->hash( h );
		primitiveVariablesPlug()->hash( h );
		pointTypePlug()->hash( h );
		return;
	}

	h = outPlug()->objectPlug()->defaultValue()->Object::hash();
}

IECore::ConstObjectPtr Scatter::computeBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() == 1 )
	{
		// do what we came for
		ConstMeshPrimitivePtr mesh = runTimeCast<const MeshPrimitive>( inPlug()->object( sourcePath ) );
		if( !mesh )
		{
			return outPlug()->objectPlug()->defaultValue();
		}

		PointsPrimitivePtr result = MeshAlgo::distributePoints(
			mesh.get(),
			densityPlug()->getValue(),
			V2f( 0 ),
			densityPrimitiveVariablePlug()->getValue(),
			uvPlug()->getValue(),
			referencePositionPlug()->getValue(),
			primitiveVariablesPlug()->getValue(),
			context->canceller()
		);
		result->variables["type"] = PrimitiveVariable( PrimitiveVariable::Constant, new StringData( pointTypePlug()->getValue() ) );

		return result;
	}
	return outPlug()->objectPlug()->defaultValue();
}

bool Scatter::affectsBranchChildNames( const Gaffer::Plug *input ) const
{
	return input == namePlug();
}

void Scatter::hashBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() == 0 )
	{
		BranchCreator::hashBranchChildNames( sourcePath, branchPath, context, h );
		namePlug()->hash( h );
	}
	else
	{
		h = outPlug()->childNamesPlug()->defaultValue()->Object::hash();
	}
}

IECore::ConstInternedStringVectorDataPtr Scatter::computeBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() == 0 )
	{
		std::string name = namePlug()->getValue();
		if( name.empty() )
		{
			return outPlug()->childNamesPlug()->defaultValue();
		}
		InternedStringVectorDataPtr result = new InternedStringVectorData();
		result->writable().push_back( name );
		return result;
	}
	else
	{
		return outPlug()->childNamesPlug()->defaultValue();
	}
}
