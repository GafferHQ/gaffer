//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Unencapsulate.h"

#include "GafferScene/Capsule.h"

#include "Gaffer/StringPlug.h"

#include "IECore/NullObject.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

namespace
{

ScenePlug::ScenePath concatScenePath( const ScenePlug::ScenePath &a, const ScenePlug::ScenePath &b )
{
	ScenePlug::ScenePath result;
	result.reserve( a.size() + b.size() );
	result.insert( result.end(), a.begin(), a.end() );
	result.insert( result.end(), b.begin(), b.end() );
	return result;
}

class CapsuleScope : boost::noncopyable
{
	private :
		// Base constructor used by the two public constructors
		CapsuleScope(
			const Gaffer::Context *context, const ScenePlug *inPlug, const ScenePlug::ScenePath &sourcePath
		)
		{
			m_object = inPlug->object( sourcePath );
			m_capsule = IECore::runTimeCast< const Capsule >( m_object.get() );
		}

	public :

		CapsuleScope(
			const Gaffer::Context *context, const ScenePlug *inPlug,
			const ScenePlug::ScenePath &sourcePath, const ScenePlug::ScenePath &branchPath
		) : CapsuleScope( context, inPlug, sourcePath )
		{
			if( m_capsule )
			{
				m_scope.emplace( m_capsule->context() );
				m_capsulePath = concatScenePath( m_capsule->root(), branchPath );
				m_scope->set( ScenePlug::scenePathContextName, &m_capsulePath );
			}
		}

		CapsuleScope(
			const Gaffer::Context *context, const ScenePlug *inPlug,
			const ScenePlug::ScenePath &sourcePath, const InternedString *setName
		) : CapsuleScope( context, inPlug, sourcePath )
		{
			if( m_capsule )
			{
				m_scope.emplace( m_capsule->context() );
				m_scope->set( ScenePlug::setNameContextName, setName );
			}
		}

		const IECore::Object* object() const
		{
			return m_object.get();
		}

		const ScenePlug* scene( bool throwIfNoCapsule ) const
		{
			if( !m_capsule )
			{
				if( throwIfNoCapsule )
				{
					throw IECore::Exception( "Accessing capsule scene, but capsule not found." );

				}
				return nullptr;
			}
			return m_capsule->scene();
		}

		const ScenePlug::ScenePath &root() const
		{
			if( !m_capsule )
			{
				throw IECore::Exception( "Coding error, only read root() when a capsule is found." );
			}
			return m_capsule->root();
		}

	private :

		// We use `optional` here to avoid the expense of constructing
		// an EditableScope when we don't need one.
		std::optional<Context::EditableScope> m_scope;
		IECore::ConstObjectPtr m_object;
		const Capsule* m_capsule;
		ScenePlug::ScenePath m_capsulePath;

};

}

GAFFER_NODE_DEFINE_TYPE( Unencapsulate );

size_t Unencapsulate::g_firstPlugIndex = 0;

Unencapsulate::Unencapsulate( const std::string &name )
	:	BranchCreator( name )
{
	// Hide `destination` plug until we resolve issues surrounding `processesRootObject()`.
	// See `BranchCreator::computeObject()`. Or perhaps we would never want to allow a
	// different destination anyway?
	destinationPlug()->setName( "__destination" );
	storeIndexOfNextChild( g_firstPlugIndex );
}

Unencapsulate::~Unencapsulate()
{
}

bool Unencapsulate::affectsBranchBound( const Gaffer::Plug *input ) const
{
	return input == inPlug()->objectPlug();
}

void Unencapsulate::hashBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	CapsuleScope cs( context, inPlug(), sourcePath, branchPath );
	h = cs.scene( true )->boundPlug()->hash();
}

Imath::Box3f Unencapsulate::computeBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	CapsuleScope cs( context, inPlug(), sourcePath, branchPath );
	return cs.scene( true )->boundPlug()->getValue();
}

bool Unencapsulate::affectsBranchTransform( const Gaffer::Plug *input ) const
{
	return input == inPlug()->objectPlug();
}

void Unencapsulate::hashBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	CapsuleScope cs( context, inPlug(), sourcePath, branchPath );
	h = cs.scene( true )->transformPlug()->hash();
}

Imath::M44f Unencapsulate::computeBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	CapsuleScope cs( context, inPlug(), sourcePath, branchPath );
	return cs.scene( true )->transformPlug()->getValue();
}

bool Unencapsulate::affectsBranchAttributes( const Gaffer::Plug *input ) const
{
	return input == inPlug()->objectPlug();
}

void Unencapsulate::hashBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	CapsuleScope cs( context, inPlug(), sourcePath, branchPath );
	h = cs.scene( true )->attributesPlug()->hash();
}

IECore::ConstCompoundObjectPtr Unencapsulate::computeBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	CapsuleScope cs( context, inPlug(), sourcePath, branchPath );
	return cs.scene( true )->attributesPlug()->getValue();
}

bool Unencapsulate::affectsBranchObject( const Gaffer::Plug *input ) const
{
	return input == inPlug()->objectPlug();
}

bool Unencapsulate::processesRootObject() const
{
	return true;
}

void Unencapsulate::hashBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	CapsuleScope cs( context, inPlug(), sourcePath, branchPath );
	if( branchPath.size() == 0 && !cs.scene( false ) )
	{
		h = inPlug()->objectPlug()->hash();
	}
	else
	{
		h = cs.scene( true )->objectPlug()->hash();
	}
}

IECore::ConstObjectPtr Unencapsulate::computeBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	CapsuleScope cs( context, inPlug(), sourcePath, branchPath );
	if( branchPath.size() == 0 && !cs.scene( false ) )
	{
		// Not inside capsule, just pass through input scene object
		return cs.object();
	}
	return cs.scene( true )->objectPlug()->getValue();
}

bool Unencapsulate::affectsBranchChildNames( const Gaffer::Plug *input ) const
{
	return input == inPlug()->objectPlug();
}

void Unencapsulate::hashBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	CapsuleScope cs( context, inPlug(), sourcePath, branchPath );
	if( !cs.scene( false ) )
	{
		h = outPlug()->childNamesPlug()->defaultValue()->Object::hash();
	}
	else
	{
		h = cs.scene( false )->childNamesPlug()->hash();
	}
}

IECore::ConstInternedStringVectorDataPtr Unencapsulate::computeBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	CapsuleScope cs( context, inPlug(), sourcePath, branchPath );
	if( !cs.scene( false ) )
	{
		return outPlug()->childNamesPlug()->defaultValue();
	}
	else
	{
		return cs.scene( false )->childNamesPlug()->getValue();
	}
}

bool Unencapsulate::affectsBranchSetNames( const Gaffer::Plug *input ) const
{
	return input == inPlug()->objectPlug();
}

void Unencapsulate::hashBranchSetNames( const ScenePath &sourcePath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inPlug()->setNamesPlug()->hash();
}

IECore::ConstInternedStringVectorDataPtr Unencapsulate::computeBranchSetNames( const ScenePath &sourcePath, const Gaffer::Context *context ) const
{
	// We have a standard that any scene containing capsules must contain all the sets used in the capsules
	// in their list of set names, even if those sets are empty until the capsules are expanded
	return inPlug()->setNamesPlug()->getValue();
}

bool Unencapsulate::affectsBranchSet( const Gaffer::Plug *input ) const
{
	return input == inPlug()->objectPlug();
}

void Unencapsulate::hashBranchSet( const ScenePath &sourcePath, const IECore::InternedString &setName, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	CapsuleScope cs( context, inPlug(), sourcePath, &setName );
	if( !cs.scene( false ) )
	{
		h = outPlug()->setPlug()->defaultValue()->Object::hash();
		return;
	}

	BranchCreator::hashBranchSet( sourcePath, setName, context, h );
	h.append( cs.scene( false )->setPlug()->hash() );
	h.append( cs.root().data(), cs.root().size() );
}

IECore::ConstPathMatcherDataPtr Unencapsulate::computeBranchSet( const ScenePath &sourcePath, const IECore::InternedString &setName, const Gaffer::Context *context ) const
{
	CapsuleScope cs( context, inPlug(), sourcePath, &setName );
	if( !cs.scene( false ) )
	{
		return outPlug()->setPlug()->defaultValue();
	}
	return new PathMatcherData( cs.scene( false )->setPlug()->getValue()->readable().subTree( cs.root() ) );
}
