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

#include "GafferScene/Private/ChildNamesMap.h"

#include "Gaffer/StringPlug.h"

#include "IECore/NullObject.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Scope classes
//////////////////////////////////////////////////////////////////////////

// Context scope that manages the context variable defined by the
// `Parent.parentVariable` plug. This derives from `GlobalScope` because we want
// to evaluate the `parentVariable` plug in a clean context, which is also
// convenient in `SourceScope` where we want to do the same for the `__mapping`
// plug. It is less convenient in `hashSet()/computeSet()` where we need to
// reintroduce the `scene:setName` variable, but on balance this approach is a
// win because it keeps context creation to a minimum.
class Parent::ParentScope : public ScenePlug::GlobalScope
{

	public :

		ParentScope( const Parent *parent, const ScenePlug::ScenePath &sourcePath, const Context *context )
			:	ScenePlug::GlobalScope( context )
		{
			const string parentVariable = parent->parentVariablePlug()->getValue();
			if( !parentVariable.empty() )
			{
				string parentString;
				ScenePlug::pathToString( sourcePath, parentString );
				set( parentVariable, parentString );
			}
		}

};

// Context scope used for evaluating the `children` plugs.
class Parent::SourceScope : public ParentScope
{

	public :

		SourceScope( const Parent *parent, const ScenePlug::ScenePath &sourcePath, const ScenePlug::ScenePath &branchPath, const Context *context )
			:	ParentScope( parent, sourcePath, context )
		{
			Private::ConstChildNamesMapPtr mapping = boost::static_pointer_cast<const Private::ChildNamesMap>( parent->mappingPlug()->getValue() );

			const Private::ChildNamesMap::Input &input = mapping->input( branchPath[0] );
			m_sourcePlug = parent->childrenPlug()->getChild<ScenePlug>( input.index );

			m_sourcePath.reserve( branchPath.size() );
			m_sourcePath.push_back( input.name );
			m_sourcePath.insert( m_sourcePath.end(), branchPath.begin() + 1, branchPath.end() );

			set( ScenePlug::scenePathContextName, m_sourcePath );
		}

		const ScenePlug *sourcePlug() const
		{
			return m_sourcePlug;
		}

	private :

		const ScenePlug *m_sourcePlug;
		ScenePlug::ScenePath m_sourcePath;

};

//////////////////////////////////////////////////////////////////////////
// Parent node
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Parent );

size_t Parent::g_firstPlugIndex = 0;

Parent::Parent( const std::string &name )
	:	BranchCreator( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ArrayPlug( "children", Plug::In, new ScenePlug( "child0" ) ) );
	addChild( new StringPlug( "parentVariable", Plug::In, "" ) );
	addChild( new Gaffer::ObjectPlug( "__mapping", Gaffer::Plug::Out, IECore::NullObject::defaultNullObject() ) );
}

Parent::~Parent()
{
}

Gaffer::ArrayPlug *Parent::childrenPlug()
{
	return getChild<ArrayPlug>( g_firstPlugIndex );
}

const Gaffer::ArrayPlug *Parent::childrenPlug() const
{
	return getChild<ArrayPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *Parent::parentVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *Parent::parentVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::ObjectPlug *Parent::mappingPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::ObjectPlug *Parent::mappingPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 2 );
}

void Parent::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	BranchCreator::affects( input, outputs );

	if( const ScenePlug *s = input->parent<ScenePlug>() )
	{
		if( s->parent<ArrayPlug>() == childrenPlug() )
		{
			if( input == s->childNamesPlug() )
			{
				outputs.push_back( mappingPlug() );
			}
		}
	}
}

void Parent::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hash( output, context, h );

	if( output == mappingPlug() )
	{
		ScenePlug::PathScope scope( context, ScenePath() );
		for( const auto &child : ScenePlug::Range( *childrenPlug() ) )
		{
			child->childNamesPlug()->hash( h );
		}
	}
}

void Parent::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == mappingPlug() )
	{
		ScenePlug::PathScope scope( context, ScenePath() );
		vector<ConstInternedStringVectorDataPtr> childNames;
		for( const auto &child : ScenePlug::Range( *childrenPlug() ) )
		{
			childNames.push_back( child->childNamesPlug()->getValue() );
		}

		static_cast<ObjectPlug *>( output )->setValue( new Private::ChildNamesMap( childNames ) );
	}

	return BranchCreator::compute( output, context );
}

bool Parent::affectsBranchBound( const Gaffer::Plug *input ) const
{
	return affectsSourceScope( input ) || isChildrenPlug( input, inPlug()->boundPlug()->getName() );
}

void Parent::hashBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() == 0 )
	{
		BranchCreator::hashBranchBound( sourcePath, branchPath, context, h );

		ParentScope s( this, sourcePath, context );
		s.set( ScenePlug::scenePathContextName, ScenePath() );

		for( auto &p : ScenePlug::Range( *childrenPlug() ) )
		{
			p->boundPlug()->hash( h );
		}
	}
	else
	{
		// pass through
		SourceScope s( this, sourcePath, branchPath, context );
		h = s.sourcePlug()->boundPlug()->hash();
	}
}

Imath::Box3f Parent::computeBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() == 0 )
	{
		// NOTE : that this branch is currently unused, since BranchCreator only calls computeBranchBound once we're
		// inside a branch ( at the top level, it assumes it needs to just merge all the child bounds anyway ).
		// Perhaps in the future, some of the use cases of BranchCreator could be optimized if we changed it so
		// it did use this path.
		ParentScope s( this, sourcePath, context );
		s.set( ScenePlug::scenePathContextName, ScenePath() );

		Box3f combinedBound;
		for( auto &p : ScenePlug::Range( *childrenPlug() ) )
		{
			// we don't need to transform these bounds, because the SceneNode
			// guarantees that the transform for root nodes is always identity.
			combinedBound.extendBy( p->boundPlug()->getValue() );
		}
		return combinedBound;
	}
	else
	{
		// pass through
		SourceScope s( this, sourcePath, branchPath, context );
		return s.sourcePlug()->boundPlug()->getValue();
	}
}

bool Parent::affectsBranchTransform( const Gaffer::Plug *input ) const
{
	return affectsSourceScope( input ) || isChildrenPlug( input, inPlug()->transformPlug()->getName() );
}

void Parent::hashBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SourceScope s( this, sourcePath, branchPath, context );
	h = s.sourcePlug()->transformPlug()->hash();
}

Imath::M44f Parent::computeBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	SourceScope s( this, sourcePath, branchPath, context );
	return s.sourcePlug()->transformPlug()->getValue();
}

bool Parent::affectsBranchAttributes( const Gaffer::Plug *input ) const
{
	return affectsSourceScope( input ) || isChildrenPlug( input, inPlug()->attributesPlug()->getName() );
}

void Parent::hashBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SourceScope s( this, sourcePath, branchPath, context );
	h = s.sourcePlug()->attributesPlug()->hash();
}

IECore::ConstCompoundObjectPtr Parent::computeBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	SourceScope s( this, sourcePath, branchPath, context );
	return s.sourcePlug()->attributesPlug()->getValue();
}

bool Parent::affectsBranchObject( const Gaffer::Plug *input ) const
{
	return affectsSourceScope( input ) || isChildrenPlug( input, inPlug()->objectPlug()->getName() );
}

void Parent::hashBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SourceScope s( this, sourcePath, branchPath, context );
	h = s.sourcePlug()->objectPlug()->hash();
}

IECore::ConstObjectPtr Parent::computeBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	SourceScope s( this, sourcePath, branchPath, context );
	return s.sourcePlug()->objectPlug()->getValue();
}

bool Parent::affectsBranchChildNames( const Gaffer::Plug *input ) const
{
	return affectsSourceScope( input ) || isChildrenPlug( input, inPlug()->childNamesPlug()->getName() );
}

void Parent::hashBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() == 0 )
	{
		BranchCreator::hashBranchChildNames( sourcePath, branchPath, context, h );
		ParentScope s( this, sourcePath, context );
		mappingPlug()->hash( h );
	}
	else
	{
		SourceScope s( this, sourcePath, branchPath, context );
		h = s.sourcePlug()->childNamesPlug()->hash();
	}
}

IECore::ConstInternedStringVectorDataPtr Parent::computeBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() == 0 )
	{
		ParentScope s( this, sourcePath, context );
		Private::ConstChildNamesMapPtr mapping = boost::static_pointer_cast<const Private::ChildNamesMap>( mappingPlug()->getValue() );
		return mapping->outputChildNames();
	}
	else
	{
		SourceScope s( this, sourcePath, branchPath, context );
		return s.sourcePlug()->childNamesPlug()->getValue();
	}
}

bool Parent::affectsBranchSetNames( const Gaffer::Plug *input ) const
{
	return affectsParentScope( input ) || isChildrenPlug( input, inPlug()->setNamesPlug()->getName() );
}

void Parent::hashBranchSetNames( const ScenePath &sourcePath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hashBranchSetNames( sourcePath, context, h );

	ParentScope s( this, sourcePath, context );
	for( auto &p : ScenePlug::Range( *childrenPlug() ) )
	{
		p->setNamesPlug()->hash( h );
	}
}

IECore::ConstInternedStringVectorDataPtr Parent::computeBranchSetNames( const ScenePath &sourcePath, const Gaffer::Context *context ) const
{
	ParentScope s( this, sourcePath, context );

	InternedStringVectorDataPtr resultData = new InternedStringVectorData;
	vector<InternedString> &result = resultData->writable();
	for( auto &p : ScenePlug::Range( *childrenPlug() ) )
	{
		// This naive approach to merging set names preserves the order of the incoming names,
		// but at the expense of using linear search. We assume that the number of sets is small
		// enough and the InternedString comparison fast enough that this is OK.
		ConstInternedStringVectorDataPtr inputSetNamesData = p->setNamesPlug()->getValue();
		for( const auto &setName : inputSetNamesData->readable() )
		{
			if( std::find( result.begin(), result.end(), setName ) == result.end() )
			{
				result.push_back( setName );
			}
		}
	}

	return resultData;
}

bool Parent::constantBranchSetNames() const
{
	return parentVariablePlug()->isSetToDefault() || parentVariablePlug()->getValue().empty();
}

bool Parent::affectsBranchSet( const Gaffer::Plug *input ) const
{
	return affectsParentScope( input ) || isChildrenPlug( input, inPlug()->setPlug()->getName() );
}

void Parent::hashBranchSet( const ScenePath &sourcePath, const IECore::InternedString &setName, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hashBranchSet( sourcePath, setName, context, h );

	ParentScope s( this, sourcePath, context );
	s.set( ScenePlug::setNameContextName, setName );

	for( auto &p : ScenePlug::Range( *childrenPlug() ) )
	{
		p->setPlug()->hash( h );
	}

	s.remove( ScenePlug::setNameContextName );
	mappingPlug()->hash( h );
}

IECore::ConstPathMatcherDataPtr Parent::computeBranchSet( const ScenePath &sourcePath, const IECore::InternedString &setName, const Gaffer::Context *context ) const
{
	ParentScope s( this, sourcePath, context );
	s.set( ScenePlug::setNameContextName, setName );

	vector<ConstPathMatcherDataPtr> inputSets; inputSets.reserve( childrenPlug()->children().size() );
	for( auto &p : ScenePlug::Range( *childrenPlug() ) )
	{
		inputSets.push_back( p->setPlug()->getValue() );
	}

	s.remove( ScenePlug::setNameContextName );
	Private::ConstChildNamesMapPtr mapping = boost::static_pointer_cast<const Private::ChildNamesMap>( mappingPlug()->getValue() );

	PathMatcherDataPtr resultData = new PathMatcherData;
	resultData->writable().addPaths( mapping->set( inputSets ) );

	return resultData;
}

bool Parent::affectsParentScope( const Gaffer::Plug *input ) const
{
	return input == parentVariablePlug();
}

bool Parent::affectsSourceScope( const Gaffer::Plug *input ) const
{
	return affectsParentScope( input ) || input == mappingPlug();
}

bool Parent::isChildrenPlug( const Gaffer::Plug *input, const IECore::InternedString &scenePlugChildName ) const
{
	const auto scene = input->parent<ScenePlug>();
	if( !scene || scene->parent() != childrenPlug() )
	{
		return false;
	}

	return input->getName() == scenePlugChildName;
}
