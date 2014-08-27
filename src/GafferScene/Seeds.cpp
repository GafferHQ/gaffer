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

#include "IECore/PointDistributionOp.h"

#include "GafferScene/Seeds.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Seeds );

size_t Seeds::g_firstPlugIndex = 0;

Seeds::Seeds( const std::string &name )
	:	BranchCreator( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "name", Plug::In, "seeds" ) );
	addChild( new FloatPlug( "density", Plug::In, 1.0f, 0.0f ) );
	addChild( new StringPlug( "pointType", Plug::In, "gl:point" ) );
}

Seeds::~Seeds()
{
}

Gaffer::StringPlug *Seeds::namePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Seeds::namePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *Seeds::densityPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *Seeds::densityPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *Seeds::pointTypePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *Seeds::pointTypePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

void Seeds::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	BranchCreator::affects( input, outputs );

	if( input == densityPlug() || input == pointTypePlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
	else if( input == namePlug() )
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}
}

void Seeds::hashBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->boundHash( parentPath );
}

Imath::Box3f Seeds::computeBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	return inPlug()->bound( parentPath );
}

void Seeds::hashBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hashBranchTransform( parentPath, branchPath, context, h );
}

Imath::M44f Seeds::computeBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	return M44f();
}

void Seeds::hashBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hashBranchAttributes( parentPath, branchPath, context, h );
}

IECore::ConstCompoundObjectPtr Seeds::computeBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	return outPlug()->attributesPlug()->defaultValue();
}

void Seeds::hashBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() == 1 )
	{
		BranchCreator::hashBranchObject( parentPath, branchPath, context, h );
		h.append( inPlug()->objectHash( parentPath ) );
		densityPlug()->hash( h );
		pointTypePlug()->hash( h );
		return;
	}

	h = outPlug()->objectPlug()->defaultValue()->Object::hash();
}

IECore::ConstObjectPtr Seeds::computeBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() == 1 )
	{
		// do what we came for
		ConstMeshPrimitivePtr mesh = runTimeCast<const MeshPrimitive>( inPlug()->object( parentPath ) );
		if( !mesh )
		{
			return outPlug()->objectPlug()->defaultValue();
		}

		PointDistributionOpPtr op = new PointDistributionOp();
		op->meshParameter()->setValue( mesh->copy() );
		op->densityParameter()->setNumericValue( densityPlug()->getValue() );

		PrimitivePtr result = runTimeCast<Primitive>( op->operate() );
		result->variables["type"] = PrimitiveVariable( PrimitiveVariable::Constant, new StringData( pointTypePlug()->getValue() ) );

		return result;
	}
	return outPlug()->objectPlug()->defaultValue();
}

void Seeds::hashBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() == 0 )
	{
		BranchCreator::hashBranchChildNames( parentPath, branchPath, context, h );
		namePlug()->hash( h );
	}
	else
	{
		h = outPlug()->childNamesPlug()->defaultValue()->Object::hash();
	}
}

IECore::ConstInternedStringVectorDataPtr Seeds::computeBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
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
