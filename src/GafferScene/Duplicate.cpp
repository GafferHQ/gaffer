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

#include "IECore/StringAlgo.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

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
	addChild( new StringPlug( "__outParent", Plug::Out ) );
	addChild( new InternedStringVectorDataPlug( "__outChildNames", Plug::Out, inPlug()->childNamesPlug()->defaultValue() ) );

	parentPlug()->setInput( outParentPlug() );
	parentPlug()->setFlags( Plug::Serialisable, false );

	// Make the filter plug private. We do want to support this one
	// day, but the filter should be specifying the objects to duplicate,
	// not the parent locations to duplicate them under. Until we implement
	// that, its best not to allow folks to become dependent upon behaviour
	// that will change.
	filterPlug()->setName( "__filter" );

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

Gaffer::StringPlug *Duplicate::outParentPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringPlug *Duplicate::outParentPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 4 );
}

Gaffer::InternedStringVectorDataPlug *Duplicate::childNamesPlug()
{
	return getChild<InternedStringVectorDataPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::InternedStringVectorDataPlug *Duplicate::childNamesPlug() const
{
	return getChild<InternedStringVectorDataPlug>( g_firstPlugIndex + 5 );
}

void Duplicate::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	BranchCreator::affects( input, outputs );

	if( input == targetPlug() )
	{
		outputs.push_back( outParentPlug() );
	}

	if(
		input == inPlug()->existsPlug() ||
		input == targetPlug() ||
		input == copiesPlug() ||
		input == namePlug()
	)
	{
		outputs.push_back( childNamesPlug() );
	}
}

void Duplicate::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	BranchCreator::hash( output, context, h );

	if( output == outParentPlug() )
	{
		targetPlug()->hash( h );
	}
	else if( output == childNamesPlug() )
	{
		ScenePath target;
		ScenePlug::stringToPath( targetPlug()->getValue(), target );
		if( !inPlug()->exists( target ) )
		{
			h = childNamesPlug()->defaultValue()->Object::hash();
			return;
		}
		h.append( target.data(), target.size() );
		copiesPlug()->hash( h );
		namePlug()->hash( h );
	}
}

void Duplicate::compute( ValuePlug *output, const Context *context ) const
{
	if( output == outParentPlug() )
	{
		ScenePath target;
		ScenePlug::stringToPath( targetPlug()->getValue(), target );
		string parent;
		for( size_t i = 0; i < target.size(); ++i )
		{
			parent += "/";
			if( i < target.size() - 1 )
			{
				parent += target[i];
			}
		}
		static_cast<StringPlug *>( output )->setValue( parent );
		return;
	}
	else if( output == childNamesPlug() )
	{
		// Get the path to our target, and check it exists.
		ScenePath target;
		ScenePlug::stringToPath( targetPlug()->getValue(), target );
		if( !inPlug()->exists( target ) )
		{
			output->setToDefault();
			return;
		}

		// go ahead and generate our childnames.
		// these are composed of a stem and possibly
		// a numeric suffix. we default to deriving
		// these from the name of the target.

		std::string stem;
		int suffix = StringAlgo::numericSuffix( target.back(), 0, &stem );
		suffix++;

		const int copies = copiesPlug()->getValue();
		const std::string name = namePlug()->getValue();

		// if a name is provided explicitly, then
		// it overrides the name and suffix derived
		// from the target.
		if( name.size() )
		{
			std::string nameStem;
			const int nameSuffix = StringAlgo::numericSuffix( name, &nameStem );
			stem = nameStem;
			suffix = copies == 1 ? nameSuffix : max( nameSuffix, 1 );
		}

		InternedStringVectorDataPtr childNamesData = new InternedStringVectorData;
		std::vector<InternedString> &childNames = childNamesData->writable();
		childNames.reserve( copies );

		if( suffix == -1 )
		{
			assert( copies == 1 );
			childNames.push_back( stem );
		}
		else
		{
			boost::format formatter( "%s%d" );
			for( int i = 0; i < copies; ++i )
			{
				childNames.push_back( boost::str( formatter % stem % suffix++ ) );
			}
		}

		static_cast<InternedStringVectorDataPlug *>( output )->setValue( childNamesData );
		return;
	}

	BranchCreator::compute( output, context );
}

bool Duplicate::affectsBranchBound( const Gaffer::Plug *input ) const
{
	return input == inPlug()->boundPlug();
}

void Duplicate::hashBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePath source;
	sourcePath( branchPath, source );
	h = inPlug()->boundHash( source );
}

Imath::Box3f Duplicate::computeBranchBound( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	ScenePath source;
	sourcePath( branchPath, source );
	return inPlug()->bound( source );
}

bool Duplicate::affectsBranchTransform( const Gaffer::Plug *input ) const
{
	return
		input == inPlug()->transformPlug() ||
		transformPlug()->isAncestorOf( input ) ||
		input == childNamesPlug()
	;
}

void Duplicate::hashBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePath source;
	sourcePath( branchPath, source );
	if( branchPath.size() == 1 )
	{
		BranchCreator::hashBranchTransform( parentPath, branchPath, context, h );
		h.append( inPlug()->transformHash( source ) );
		transformPlug()->hash( h );
		childNamesPlug()->hash( h );
		h.append( branchPath[0] );
	}
	else
	{
		h = inPlug()->transformHash( source );
	}
}

Imath::M44f Duplicate::computeBranchTransform( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	ScenePath source;
	sourcePath( branchPath, source );
	Imath::M44f result = inPlug()->transform( source );
	if( branchPath.size() == 1 )
	{
		const Imath::M44f matrix = transformPlug()->matrix();
		ConstInternedStringVectorDataPtr childNamesData = childNamesPlug()->getValue();
		const vector<InternedString> &childNames = childNamesData->readable();

		size_t i = 0;
		do
		{
			result = result * matrix;
		} while( i < childNames.size() && branchPath[0] != childNames[i++] );
	}
	return result;
}

bool Duplicate::affectsBranchAttributes( const Gaffer::Plug *input ) const
{
	return input == inPlug()->attributesPlug();
}

void Duplicate::hashBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePath source;
	sourcePath( branchPath, source );
	h = inPlug()->attributesHash( source );
}

IECore::ConstCompoundObjectPtr Duplicate::computeBranchAttributes( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	ScenePath source;
	sourcePath( branchPath, source );
	return inPlug()->attributes( source );
}

bool Duplicate::affectsBranchObject( const Gaffer::Plug *input ) const
{
	return input == inPlug()->objectPlug();
}

void Duplicate::hashBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePath source;
	sourcePath( branchPath, source );
	h = inPlug()->objectHash( source );
}

IECore::ConstObjectPtr Duplicate::computeBranchObject( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	ScenePath source;
	sourcePath( branchPath, source );
	return inPlug()->object( source );
}

bool Duplicate::affectsBranchChildNames( const Gaffer::Plug *input ) const
{
	return input == inPlug()->childNamesPlug() || input == childNamesPlug();
}

void Duplicate::hashBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( branchPath.size() == 0 )
	{
		h = childNamesPlug()->hash();
	}
	else
	{
		ScenePath source;
		sourcePath( branchPath, source );
		h = inPlug()->childNamesHash( source );
	}
}

IECore::ConstInternedStringVectorDataPtr Duplicate::computeBranchChildNames( const ScenePath &parentPath, const ScenePath &branchPath, const Gaffer::Context *context ) const
{
	if( branchPath.size() == 0 )
	{
		return childNamesPlug()->getValue();
	}
	else
	{
		ScenePath source;
		sourcePath( branchPath, source );
		return inPlug()->childNames( source );
	}
}

bool Duplicate::affectsBranchSet( const Gaffer::Plug *input ) const
{
	return
		input == inPlug()->setPlug() ||
		input == targetPlug() ||
		input == childNamesPlug()
	;
}

void Duplicate::hashBranchSet( const ScenePath &parentPath, const IECore::InternedString &setName, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h.append( inPlug()->setHash( setName ) );
	targetPlug()->hash( h );
	childNamesPlug()->hash( h );
}

IECore::ConstPathMatcherDataPtr Duplicate::computeBranchSet( const ScenePath &parentPath, const IECore::InternedString &setName, const Gaffer::Context *context ) const
{
	ConstPathMatcherDataPtr inputSetData = inPlug()->set( setName );
	const PathMatcher &inputSet = inputSetData->readable();
	if( inputSet.isEmpty() )
	{
		return outPlug()->setPlug()->defaultValue();
	}

	PathMatcher subTree = inputSet.subTree( targetPlug()->getValue() );
	if( subTree.isEmpty() )
	{
		return outPlug()->setPlug()->defaultValue();
	}

	ConstInternedStringVectorDataPtr childNamesData = childNamesPlug()->getValue();
	const vector<InternedString> &childNames = childNamesData->readable();

	PathMatcherDataPtr resultData = new PathMatcherData;
	PathMatcher &result = resultData->writable();
	ScenePath prefix( 1 );
	for( vector<InternedString>::const_iterator it = childNames.begin(), eIt = childNames.end(); it != eIt; ++it )
	{
		prefix.back() = *it;
		result.addPaths( subTree, prefix );
	}

	return resultData;
}

void Duplicate::sourcePath( const ScenePath &branchPath, ScenePath &source ) const
{
	assert( branchPath.size() );
	ScenePlug::stringToPath( targetPlug()->getValue(), source );
	copy( ++branchPath.begin(), branchPath.end(), back_inserter( source ) );
}
