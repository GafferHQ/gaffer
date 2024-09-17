//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, John Haddon. All rights reserved.
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

#include "GafferScene/Duplicate.h"

#include "GafferScene/SceneAlgo.h"

#include "Gaffer/StringPlug.h"

#include "IECore/NullObject.h"
#include "IECore/StringAlgo.h"

#include <unordered_map>

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

class Duplicate::DuplicatesData : public IECore::Data
{

	public :

		DuplicatesData( const Duplicate *node, const Context *context )
		{
			const ScenePath &source = context->get<ScenePath>( ScenePlug::scenePathContextName );

			// The names of the duplicates are composed of a stem and possibly a
			// numeric suffix.

			std::string stem;
			int suffix;

			const std::string name = node->namePlug()->getValue();
			const int copies = node->copiesPlug()->getValue();

			if( name.size() )
			{
				const int nameSuffix = StringAlgo::numericSuffix( name, &stem );
				suffix = copies == 1 ? nameSuffix : max( nameSuffix, 1 );
			}
			else if( !source.size() )
			{
				stem = "root";
				suffix = 1;
			}
			else
			{
				// No explicit name provided. Derive stem and suffix from source.
				suffix = StringAlgo::numericSuffix( source.back(), 0, &stem );
				suffix++;
			}

			// Generate names, and at the same time, the transforms associated with them.

			m_names = new InternedStringVectorData;
			std::vector<InternedString> &names = m_names->writable();
			names.reserve( copies );

			const Imath::M44f matrix = node->transformPlug()->matrix();

			if( suffix == -1 )
			{
				assert( copies == 1 );
				names.push_back( stem );
				m_transforms[stem] = matrix;
			}
			else
			{
				Imath::M44f m = matrix;
				for( int i = 0; i < copies; ++i )
				{
					InternedString name = stem + std::to_string( suffix++ );
					names.push_back( name );
					m_transforms[name] = m;
					m = m * matrix;
				}
			}
		}

		static bool affectedBy( const Duplicate *node, const Plug *input )
		{
			return
				input == node->copiesPlug() ||
				input == node->namePlug() ||
				node->transformPlug()->isAncestorOf( input )
			;
		}

		static void hash( const Duplicate *node, const Context *context, IECore::MurmurHash &h )
		{
			node->copiesPlug()->hash( h );
			node->namePlug()->hash( h );
			const ScenePath &source = context->get<ScenePath>( ScenePlug::scenePathContextName );
			if( !source.size() )
			{
				h.append( false );
			}
			else
			{
				h.append( source.back() );
			}
			node->transformPlug()->hash( h );
		}

		ConstInternedStringVectorDataPtr names() const
		{
			return m_names;
		}

		const Imath::M44f &transform( const IECore::InternedString &name ) const
		{
			return m_transforms.at( name );
		}

	private :

		InternedStringVectorDataPtr m_names;
		unordered_map<InternedString, Imath::M44f> m_transforms;

};

GAFFER_NODE_DEFINE_TYPE( Duplicate );

size_t Duplicate::g_firstPlugIndex = 0;

Duplicate::Duplicate( const std::string &name )
	:	BranchCreator( name )
{

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "target" ) );
	addChild( new IntPlug( "copies", Plug::In, 1, 0 ) );
	addChild( new StringPlug( "name" ) );
	addChild( new TransformPlug( "transform" ) );
	addChild( new ObjectPlug( "__duplicates", Plug::Out, NullObject::defaultNullObject() ) );

	parentPlug()->setInput( targetPlug() );
	parentPlug()->setFlags( Plug::Serialisable, false );

	destinationPlug()->setValue( "${scene:path}/.." );
	destinationPlug()->resetDefault();

	// Since we don't introduce any new sets, but just duplicate parts
	// of existing ones, we can save the BranchCreator base class some
	// trouble by making the setNamesPlug into a pass-through.
	outPlug()->setNamesPlug()->setInput( inPlug()->setNamesPlug() );
}

Duplicate::~Duplicate()
{
}

Gaffer::StringPlug *Duplicate::targetPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Duplicate::targetPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *Duplicate::copiesPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *Duplicate::copiesPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *Duplicate::namePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *Duplicate::namePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::TransformPlug *Duplicate::transformPlug()
{
	return getChild<TransformPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::TransformPlug *Duplicate::transformPlug() const
{
	return getChild<TransformPlug>( g_firstPlugIndex + 3 );
}

Gaffer::ObjectPlug *Duplicate::duplicatesPlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::ObjectPlug *Duplicate::duplicatesPlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 4 );
}

void Duplicate::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	BranchCreator::affects( input, outputs );

	if( DuplicatesData::affectedBy( this, input ) )
	{
		outputs.push_back( duplicatesPlug() );
	}
}

void Duplicate::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hash( output, context, h );

	if( output == duplicatesPlug() )
	{
		DuplicatesData::hash( this, context, h );
	}
}

void Duplicate::compute( ValuePlug *output, const Context *context ) const
{
	if( output == duplicatesPlug() )
	{
		static_cast<ObjectPlug *>( output )->setValue( new DuplicatesData( this, context ) );
		return;
	}

	BranchCreator::compute( output, context );
}

bool Duplicate::affectsBranchBound( const Gaffer::Plug *input ) const
{
	return input == inPlug()->boundPlug();
}

void Duplicate::hashBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePath source;
	branchSource( sourcePath, branchPath, source );
	h = inPlug()->boundHash( source );
}

Imath::Box3f Duplicate::computeBranchBound( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	ScenePath source;
	branchSource( sourcePath, branchPath, source );
	return inPlug()->bound( source );
}

bool Duplicate::affectsBranchTransform( const Gaffer::Plug *input ) const
{
	return
		input == inPlug()->transformPlug() ||
		input == duplicatesPlug()
	;
}

void Duplicate::hashBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() == 1 )
	{
		BranchCreator::hashBranchTransform( sourcePath, branchPath, context, h );
		ScenePlug::PathScope s( context, &sourcePath );
		duplicatesPlug()->hash( h );
		h.append( branchPath[0] );
	}
	else
	{
		ScenePath source;
		branchSource( sourcePath, branchPath, source );
		h = inPlug()->transformHash( source );
	}
}

Imath::M44f Duplicate::computeBranchTransform( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() == 1 )
	{
		ScenePlug::PathScope s( context, &sourcePath );
		ConstDuplicatesDataPtr duplicates = static_pointer_cast<const DuplicatesData>( duplicatesPlug()->getValue() );
		return duplicates->transform( branchPath[0] );
	}
	else
	{
		ScenePath source;
		branchSource( sourcePath, branchPath, source );
		return inPlug()->transform( source );
	}
}

bool Duplicate::affectsBranchAttributes( const Gaffer::Plug *input ) const
{
	return input == inPlug()->attributesPlug();
}

void Duplicate::hashBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePath source;
	branchSource( sourcePath, branchPath, source );
	h = inPlug()->attributesHash( source );
}

IECore::ConstCompoundObjectPtr Duplicate::computeBranchAttributes( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	ScenePath source;
	branchSource( sourcePath, branchPath, source );
	return inPlug()->attributes( source );
}

bool Duplicate::affectsBranchObject( const Gaffer::Plug *input ) const
{
	return input == inPlug()->objectPlug();
}

void Duplicate::hashBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePath source;
	branchSource( sourcePath, branchPath, source );
	h = inPlug()->objectHash( source );
}

IECore::ConstObjectPtr Duplicate::computeBranchObject( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	ScenePath source;
	branchSource( sourcePath, branchPath, source );
	return inPlug()->object( source );
}

bool Duplicate::affectsBranchChildNames( const Gaffer::Plug *input ) const
{
	return input == inPlug()->childNamesPlug() || input == duplicatesPlug();
}

void Duplicate::hashBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() == 0 )
	{
		BranchCreator::hashBranchChildNames( sourcePath, branchPath, context, h );
		ScenePlug::PathScope s( context, &sourcePath );
		duplicatesPlug()->hash( h );
	}
	else
	{
		ScenePath source;
		branchSource( sourcePath, branchPath, source );
		h = inPlug()->childNamesHash( source );
	}
}

IECore::ConstInternedStringVectorDataPtr Duplicate::computeBranchChildNames( const ScenePath &sourcePath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() == 0 )
	{
		ScenePlug::PathScope s( context, &sourcePath );
		ConstDuplicatesDataPtr duplicates = static_pointer_cast<const DuplicatesData>( duplicatesPlug()->getValue() );
		return duplicates->names();
	}
	else
	{
		ScenePath source;
		branchSource( sourcePath, branchPath, source );
		return inPlug()->childNames( source );
	}
}

bool Duplicate::affectsBranchSetNames( const Gaffer::Plug *input ) const
{
	return input == inPlug()->setNamesPlug();
}

void Duplicate::hashBranchSetNames( const ScenePath &sourcePath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	assert( sourcePath.size() == 0 ); // Expectation driven by `constantBranchSetNames() == true`
	h = inPlug()->setNamesPlug()->hash();
}

IECore::ConstInternedStringVectorDataPtr Duplicate::computeBranchSetNames( const ScenePath &sourcePath, const Gaffer::Context *context ) const
{
	assert( sourcePath.size() == 0 ); // Expectation driven by `constantBranchSetNames() == true`
	return inPlug()->setNamesPlug()->getValue();
}

bool Duplicate::affectsBranchSet( const Gaffer::Plug *input ) const
{
	return
		input == inPlug()->setPlug() ||
		input == duplicatesPlug()
	;
}

void Duplicate::hashBranchSet( const ScenePath &sourcePath, const IECore::InternedString &setName, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( inPlug()->setHash( setName ) );
	h.append( sourcePath.data(), sourcePath.size() );
	ScenePlug::PathScope s( context, &sourcePath );
	duplicatesPlug()->hash( h );
}

IECore::ConstPathMatcherDataPtr Duplicate::computeBranchSet( const ScenePath &sourcePath, const IECore::InternedString &setName, const Gaffer::Context *context ) const
{
	ConstPathMatcherDataPtr inputSetData = inPlug()->set( setName );
	const PathMatcher &inputSet = inputSetData->readable();
	if( inputSet.isEmpty() )
	{
		return outPlug()->setPlug()->defaultValue();
	}

	PathMatcher subTree = inputSet.subTree( sourcePath );
	if( subTree.isEmpty() )
	{
		return outPlug()->setPlug()->defaultValue();
	}

	ConstDuplicatesDataPtr duplicates;
	{
		ScenePlug::PathScope s( context, &sourcePath );
		duplicates = static_pointer_cast<const DuplicatesData>( duplicatesPlug()->getValue() );
	}

	PathMatcherDataPtr resultData = new PathMatcherData;
	PathMatcher &result = resultData->writable();
	ScenePath prefix( 1 );
	for( const auto &name : duplicates->names()->readable() )
	{
		prefix.back() = name;
		result.addPaths( subTree, prefix );
	}

	return resultData;
}

void Duplicate::branchSource( const ScenePath &sourcePath, const ScenePath &branchPath, ScenePath &source ) const
{
	assert( branchPath.size() );
	source = sourcePath;
	copy( ++branchPath.begin(), branchPath.end(), back_inserter( source ) );
}
