//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Parent.h"

using namespace GafferScene;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Parent );

size_t Parent::g_firstPlugIndex = 0;

Parent::Parent( const std::string &name )
	:	BranchCreator( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "child" ) );
}

Parent::~Parent()
{
}

ScenePlug *Parent::childPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *Parent::childPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

bool Parent::affectsBranchBound( const Gaffer::Plug *input ) const
{
	return input == childPlug()->boundPlug();
}

void Parent::hashBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = childPlug()->boundHash( branchPath );
}

Imath::Box3f Parent::computeBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	return childPlug()->bound( branchPath );
}

bool Parent::affectsBranchTransform( const Gaffer::Plug *input ) const
{
	return input == childPlug()->transformPlug();
}

void Parent::hashBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = childPlug()->transformHash( branchPath );
}

Imath::M44f Parent::computeBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	return childPlug()->transform( branchPath );
}

bool Parent::affectsBranchAttributes( const Gaffer::Plug *input ) const
{
	return input == childPlug()->attributesPlug();
}

void Parent::hashBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = childPlug()->attributesHash( branchPath );
}

IECore::ConstCompoundObjectPtr Parent::computeBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	return childPlug()->attributes( branchPath );
}

bool Parent::affectsBranchObject( const Gaffer::Plug *input ) const
{
	return input == childPlug()->objectPlug();
}

void Parent::hashBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = childPlug()->objectHash( branchPath );
}

IECore::ConstObjectPtr Parent::computeBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	return childPlug()->object( branchPath );
}

bool Parent::affectsBranchChildNames( const Gaffer::Plug *input ) const
{
	return input == childPlug()->childNamesPlug();
}

void Parent::hashBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = childPlug()->childNamesHash( branchPath );
}

IECore::ConstInternedStringVectorDataPtr Parent::computeBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	return childPlug()->childNames( branchPath );
}

bool Parent::affectsBranchSetNames( const Gaffer::Plug *input ) const
{
	return input == childPlug()->setNamesPlug();
}

void Parent::hashBranchSetNames( const ScenePath &parentPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	assert( parentPath.size() == 0 ); // Expectation driven by `constantBranchSetNames() == true`
	h = childPlug()->setNamesPlug()->hash();
}

IECore::ConstInternedStringVectorDataPtr Parent::computeBranchSetNames( const ScenePath &parentPath, const Gaffer::Context *context ) const
{
	assert( parentPath.size() == 0 ); // Expectation driven by `constantBranchSetNames() == true`
	return childPlug()->setNamesPlug()->getValue();
}

bool Parent::affectsBranchSet( const Gaffer::Plug *input ) const
{
	return input == childPlug()->setPlug();
}

void Parent::hashBranchSet( const ScenePath &parentPath, const IECore::InternedString &setName, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = childPlug()->setHash( setName );
}

IECore::ConstPathMatcherDataPtr Parent::computeBranchSet( const ScenePath &parentPath, const IECore::InternedString &setName, const Gaffer::Context *context ) const
{
	return childPlug()->set( setName );
}
