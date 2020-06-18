//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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

// Workaround for this bug in GCC 4.8 :
// https://gcc.gnu.org/bugzilla/show_bug.cgi?id=59483
#include "boost/config.hpp"
#if defined(BOOST_GCC) && BOOST_GCC < 40900
	#define protected public
#endif

#include "GafferScene/MergeScenes.h"

#include "GafferScene/SceneAlgo.h"

#include "Gaffer/ArrayPlug.h"

#include "IECore/NullObject.h"

#include "unordered_set"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

size_t MergeScenes::g_firstPlugIndex = 0;
GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( MergeScenes );

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

size_t first( const std::bitset<32> &inputs )
{
	for( size_t i = 0; i < inputs.size(); ++i )
	{
		if( inputs[i] )
		{
			return i;
		}
	}

	// We shouldn't get here, because all valid locations should
	// have at least one active input.
	assert( false );
	return 0;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// MergeScenes
//////////////////////////////////////////////////////////////////////////

MergeScenes::MergeScenes( const std::string &name )
	:	SceneProcessor( name, /* minInputs = */ 2, /* maxInputs = */ InputMask().size() )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "transformMode", Plug::In, (int)Mode::Keep, (int)Mode::Keep, (int)Mode::Replace ) );
	addChild( new IntPlug( "attributesMode", Plug::In, (int)Mode::Keep, (int)Mode::Keep, (int)Mode::Merge ) );
	addChild( new IntPlug( "objectMode", Plug::In, (int)Mode::Keep, (int)Mode::Keep, (int)Mode::Replace ) );
	addChild( new IntPlug( "globalsMode", Plug::In, (int)Mode::Keep, (int)Mode::Keep, (int)Mode::Merge ) );
	addChild( new BoolPlug( "adjustBounds", Plug::In, true ) );
	addChild( new IntPlug( "__activeInputs", Plug::Out, 0 ) );
	addChild( new AtomicBox3fPlug( "__mergedDescendantsBound", Plug::Out ) );
}

MergeScenes::~MergeScenes()
{
}

Gaffer::IntPlug *MergeScenes::transformModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *MergeScenes::transformModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *MergeScenes::attributesModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *MergeScenes::attributesModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *MergeScenes::objectModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *MergeScenes::objectModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

Gaffer::IntPlug *MergeScenes::globalsModePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::IntPlug *MergeScenes::globalsModePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

Gaffer::BoolPlug *MergeScenes::adjustBoundsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::BoolPlug *MergeScenes::adjustBoundsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 4 );
}

Gaffer::IntPlug *MergeScenes::activeInputsPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::IntPlug *MergeScenes::activeInputsPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

Gaffer::AtomicBox3fPlug *MergeScenes::mergedDescendantsBoundPlug()
{
	return getChild<AtomicBox3fPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::AtomicBox3fPlug *MergeScenes::mergedDescendantsBoundPlug() const
{
	return getChild<AtomicBox3fPlug>( g_firstPlugIndex + 6 );
}

void MergeScenes::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );

	const ScenePlug *scene = inPlugs()->isAncestorOf( input ) ? input->parent<ScenePlug>() : nullptr;

	if( scene && input == scene->childNamesPlug() )
	{
		outputs.push_back( activeInputsPlug() );
	}

	if(
		( scene && input == scene->transformPlug() ) ||
		input == transformModePlug() ||
		input == activeInputsPlug()
	)
	{
		outputs.push_back( outPlug()->transformPlug() );
	}

	if(
		( scene && input == scene->boundPlug() ) ||
		( scene && input == scene->transformPlug() ) ||
		input == activeInputsPlug()
	)
	{
		outputs.push_back( mergedDescendantsBoundPlug() );
	}

	if(
		( scene && input == scene->boundPlug() ) ||
		( scene && input == scene->objectPlug() ) ||
		( scene && input == scene->transformPlug() ) ||
		input == transformModePlug() ||
		input == objectModePlug() ||
		input == adjustBoundsPlug() ||
		input == activeInputsPlug() ||
		input == mergedDescendantsBoundPlug()
	)
	{
		outputs.push_back( outPlug()->boundPlug() );
	}

	if(
		( scene && input == scene->attributesPlug() ) ||
		input == attributesModePlug() ||
		input == activeInputsPlug()
	)
	{
		outputs.push_back( outPlug()->attributesPlug() );
	}

	if(
		( scene && input == scene->objectPlug() ) ||
		input == objectModePlug() ||
		input == activeInputsPlug()
	)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}

	if(
		( scene && input == scene->childNamesPlug() ) ||
		input == activeInputsPlug()
	)
	{
		outputs.push_back( outPlug()->childNamesPlug() );
	}

	if(
		( scene && input == scene->globalsPlug() ) ||
		input == globalsModePlug()
	)
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}

	if( scene && input == scene->setNamesPlug() )
	{
		outputs.push_back( outPlug()->setNamesPlug() );
	}

	if( scene && input == scene->setPlug() )
	{
		outputs.push_back( outPlug()->setPlug() );
	}

}

void MergeScenes::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneProcessor::hash( output, context, h );

	if( output == activeInputsPlug() )
	{
		hashActiveInputs( context, h );
	}
	else if( output == mergedDescendantsBoundPlug() )
	{
		hashMergedDescendantsBound( context, h );
	}
}

void MergeScenes::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == activeInputsPlug() )
	{
		static_cast<IntPlug *>( output )->setValue( computeActiveInputs( context ) );
	}
	else if( output == mergedDescendantsBoundPlug() )
	{
		static_cast<AtomicBox3fPlug *>( output )->setValue( computeMergedDescendantsBound( context ) );
	}
	else
	{
		SceneProcessor::compute( output, context );
	}
}

void MergeScenes::hashActiveInputs( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );

	if( scenePath.empty() )
	{
		h.append( (uint64_t)connectedInputs().to_ulong() );
	}
	else
	{
		InputMask parentActiveInputs;
		{
			ScenePath parentPath = scenePath; parentPath.pop_back();
			ScenePlug::PathScope parentScope( context, parentPath );
			parentActiveInputs = activeInputsPlug()->getValue();
		}

		if( parentActiveInputs.count() == 1 )
		{
			h.append( (uint64_t)parentActiveInputs.to_ulong() );
		}
		else
		{
			InputMask activeInputs;
			visit(
				parentActiveInputs,
				[&scenePath, &activeInputs] ( InputType type, size_t index, const ScenePlug *scene ) {
					if( SceneAlgo::exists( scene, scenePath ) )
					{
						activeInputs[index] = true;
					}
					return true;
				}
			);
			h.append( (uint64_t)activeInputs.to_ulong() );
		}
	}
}

int MergeScenes::computeActiveInputs( const Gaffer::Context *context ) const
{
	const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );

	InputMask result;
	if( scenePath.empty() )
	{
		// Root
		result = connectedInputs();
	}
	else
	{
		// Get active inputs from the parent.
		InputMask parentActiveInputs;
		{
			ScenePath parentPath = scenePath; parentPath.pop_back();
			ScenePlug::PathScope parentScope( context, parentPath );
			parentActiveInputs = activeInputsPlug()->getValue();
		}

		if( parentActiveInputs.count() == 1 )
		{
			// It is forbidden for anyone to evaluate us for a location
			// that doesn't exist. Therefore, if our parent only has
			// one active input, then that input must still be active for
			// us.
			result = parentActiveInputs;
		}
		else
		{
			// Figure out which of those parent inputs are
			// still active. Using the parent active inputs as
			// a mask reduces the number of existence queries
			// we must make when merging many sparsely overlapping
			// scenes.
			visit(
				parentActiveInputs,
				[&result, &scenePath] ( InputType type, size_t index, const ScenePlug *scene ) {
					if( SceneAlgo::exists( scene, scenePath ) )
					{
						result[index] = true;
					}
					return true;
				}
			);
		}
	}

	return result.to_ulong();
}

void MergeScenes::hashMergedDescendantsBound( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const InputMask activeInputs( activeInputsPlug()->getValue() );
	if( activeInputs.count() == 1 )
	{
		return;
	}

	ConstInternedStringVectorDataPtr childNamesData = outPlug()->childNamesPlug()->getValue();
	if( childNamesData->readable().empty() )
	{
		return;
	}

	const size_t firstActiveIndex = first( activeInputs );

	ScenePath childPath = context->get<ScenePath>( ScenePlug::scenePathContextName );
	childPath.push_back( InternedString() ); // Room for child name
	ScenePlug::PathScope childScope( context );

	for( const auto &childName : childNamesData->readable() )
	{
		childPath.back() = childName;
		childScope.setPath( childPath );
		const InputMask childActiveInputs( activeInputsPlug()->getValue() );
		if( childActiveInputs.count() == 1 && childActiveInputs[firstActiveIndex] )
		{
			continue;
		}

		const ScenePlug *childScene = inPlugs()->getChild<ScenePlug>( first( childActiveInputs ) );

		if( childActiveInputs.count() == 1 )
		{
			childScene->boundPlug()->hash( h );
		}
		else
		{
			mergedDescendantsBoundPlug()->hash( h );
		}

		childScene->transformPlug()->hash( h );
	};
}

const Imath::Box3f MergeScenes::computeMergedDescendantsBound( const Gaffer::Context *context ) const
{
	const InputMask activeInputs( activeInputsPlug()->getValue() );
	if( activeInputs.count() == 1 )
	{
		// All children coming from the first input. There can be no descendants to merge.
		return Box3f();
	}

	ConstInternedStringVectorDataPtr childNamesData = outPlug()->childNamesPlug()->getValue();
	if( childNamesData->readable().empty() )
	{
		// No children. There can be no descendants to merge.
		return Box3f();
	}

	const size_t firstActiveIndex = first( activeInputs );

	ScenePath childPath = context->get<ScenePath>( ScenePlug::scenePathContextName );
	childPath.push_back( InternedString() ); // Room for child name
	ScenePlug::PathScope childScope( context );

	Box3f result;
	for( const auto &childName : childNamesData->readable() )
	{
		childPath.back() = childName;
		childScope.setPath( childPath );
		const InputMask childActiveInputs( activeInputsPlug()->getValue() );
		if( childActiveInputs.count() == 1 && childActiveInputs[firstActiveIndex] )
		{
			// Child coming from first input only.
			// There can be no descendants to merge.
			continue;
		}

		const ScenePlug *childScene = inPlugs()->getChild<ScenePlug>( first( childActiveInputs ) );

		Box3f bound;
		if( childActiveInputs.count() == 1 )
		{
			// Child being merged in from another input.
			bound = childScene->boundPlug()->getValue();
		}
		else
		{
			// No child being merged in at this point, but
			// there may still be a descendant merge lower
			// in the hierarchy. Recurse.
			bound = mergedDescendantsBoundPlug()->getValue();
		}

		result.extendBy( transform( bound, childScene->transformPlug()->getValue() ) );
	};
	return result;
}

void MergeScenes::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	// Pass through.

	const InputMask activeInputs( activeInputsPlug()->getValue() );
	if( activeInputs.count() == 1 || !adjustBoundsPlug()->getValue() )
	{
		h = inPlugs()->getChild<ScenePlug>( first( activeInputs ) )->boundPlug()->hash();
		return;
	}

	// Objects/transforms always from first active input.

	if( objectModePlug()->getValue() == (int)Mode::Keep && transformModePlug()->getValue() == (int)Mode::Keep )
	{
		SceneProcessor::hashBound( path, context, parent, h );
		inPlugs()->getChild<ScenePlug>( first( activeInputs ) )->boundPlug()->hash( h );
		mergedDescendantsBoundPlug()->hash( h );
		return;
	}

	// Worst case scenario

	SceneProcessor::hashBound( path, context, parent, h );
	outPlug()->objectPlug()->hash( h );
	h.append( hashOfTransformedChildBounds( path, outPlug() ) );
}

Imath::Box3f MergeScenes::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	// Pass through for simple cases.

	const InputMask activeInputs( activeInputsPlug()->getValue() );
	if( activeInputs.count() == 1 || !adjustBoundsPlug()->getValue() )
	{
		return inPlugs()->getChild<ScenePlug>( first( activeInputs ) )->boundPlug()->getValue();
	}

	// If objects and transforms always come from the first active input,
	// then the bound from the first input will already be correct for them.
	// We just need to extend it to account for any new descendants
	// being merged in from the other inputs.

	if( objectModePlug()->getValue() == (int)Mode::Keep && transformModePlug()->getValue() == (int)Mode::Keep )
	{
		Box3f result = inPlugs()->getChild<ScenePlug>( first( activeInputs ) )->boundPlug()->getValue();
		result.extendBy( mergedDescendantsBoundPlug()->getValue() );
		return result;
	}

	// Otherwise we're in the worst case scenario, and transforms and
	// objects can be taken from any input willy nilly. We have to
	// compute everything by brute force.

	Box3f result = SceneAlgo::bound( outPlug()->objectPlug()->getValue().get() );
	result.extendBy( unionOfTransformedChildBounds( path, outPlug() ) );
	return result;
}

void MergeScenes::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	visit(
		activeInputsPlug()->getValue(),
		[&] ( InputType type, size_t index, const ScenePlug *scene ) {
			h = scene->transformPlug()->hash();
			return false;
		},
		visitOrder( (Mode)transformModePlug()->getValue() )
	);
}

Imath::M44f MergeScenes::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	M44f result;
	visit(
		activeInputsPlug()->getValue(),
		[&result] ( InputType type, size_t index, const ScenePlug *scene ) {
			result = scene->transformPlug()->getValue();
			return false;
		},
		visitOrder( (Mode)transformModePlug()->getValue() )
	);

	return result;
}

void MergeScenes::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	visit(
		activeInputsPlug()->getValue(),
		[&] ( InputType type, size_t index, const ScenePlug *scene ) {
			switch( type )
			{
				case InputType::Sole :
					// Pass hash through unchanged
					h = scene->attributesPlug()->hash();
					break;
				case InputType::First :
					// Initialise hash and fall through
					SceneProcessor::hashAttributes( path, context, parent, h );
				case InputType::Other :
					// Merge input hash
					scene->attributesPlug()->hash( h );
			}
			return true;
		},
		visitOrder( (Mode)attributesModePlug()->getValue() )
	);
}

IECore::ConstCompoundObjectPtr MergeScenes::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstCompoundObjectPtr result;
	CompoundObjectPtr merged;
	visit(
		activeInputsPlug()->getValue(),
		[&] ( InputType type, size_t index, const ScenePlug *scene ) {
			switch( type )
			{
				case InputType::Sole :
					// Pass input through unchanged.
					result = scene->attributesPlug()->getValue();
					break;
				case InputType::First :
					// Initialise merged result and
					// fall through.
					merged = new CompoundObject();
					result = merged;
				case InputType::Other :
					// Merge input attributes into result.
					ConstCompoundObjectPtr attributes = scene->attributesPlug()->getValue();
					for( const auto &a : attributes->members() )
					{
						merged->members()[a.first] = a.second;
					}
			}
			return true;
		},
		visitOrder( (Mode)attributesModePlug()->getValue() )
	);

	return result;
}

void MergeScenes::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	visit(
		activeInputsPlug()->getValue(),
		[&] ( InputType type, size_t index, const ScenePlug *scene ) {
			switch( type )
			{
				case InputType::Sole :
					// Pass hash through unchanged.
					h = scene->objectPlug()->hash();
					break;
				case InputType::First :
					// Initialise hash and fall through.
					SceneProcessor::hashObject( path, context, parent, h );
				case InputType::Other :
					// Merge input hash.
					scene->objectPlug()->hash( h );
			}
			return true;
		},
		visitOrder( (Mode)objectModePlug()->getValue(), /* replaceOrder = */ VisitOrder::Backwards )
	);
}

IECore::ConstObjectPtr MergeScenes::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstObjectPtr result = IECore::NullObject::defaultNullObject();
	visit(
		activeInputsPlug()->getValue(),
		[&result] ( InputType type, size_t index, const ScenePlug *scene ) {
			ConstObjectPtr o = scene->objectPlug()->getValue();
			if( runTimeCast<const NullObject>( o.get() ) )
			{
				// No object here, visit next input.
				return true;
			}
			else
			{
				result = o;
				// We found what we want, so no need to
				// visit any more inputs.
				return false;
			}
		},
		visitOrder( (Mode)objectModePlug()->getValue(), /* replaceOrder = */ VisitOrder::Backwards )
	);
	return result;
}

void MergeScenes::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	visit(
		activeInputsPlug()->getValue(),
		[&] ( InputType type, size_t index, const ScenePlug *scene ) {
			switch( type )
			{
				case InputType::Sole :
					h = scene->childNamesPlug()->hash();
					break;
				case InputType::First :
					SceneProcessor::hashChildNames( path, context, parent, h );
				case InputType::Other :
					scene->childNamesPlug()->hash( h );
			}
			return true;
		}
	);
}

IECore::ConstInternedStringVectorDataPtr MergeScenes::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstInternedStringVectorDataPtr result;
	InternedStringVectorDataPtr merged;
	unordered_set<InternedString> visited;

	visit(
		activeInputsPlug()->getValue(),
		[&] ( InputType type, size_t index, const ScenePlug *scene ) {
			switch( type )
			{
				case InputType::Sole :
				case InputType::First :
					result = scene->childNamesPlug()->getValue();
					break;
				case InputType::Other :
					ConstInternedStringVectorDataPtr toMerge = scene->childNamesPlug()->getValue();
					if( toMerge->readable().size() )
					{
						if( !merged )
						{
							merged = result->copy();
							result = merged;
							visited.insert( merged->readable().begin(), merged->readable().end() );
						}

						for( const auto & n : toMerge->readable() )
						{
							if( visited.insert( n ).second )
							{
								merged->writable().push_back( n );
							}
						}
					}
			}
			return true;
		}
	);

	return result;
}

void MergeScenes::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	visit(
		connectedInputs(),
		[&] ( InputType type, size_t index, const ScenePlug *scene ) {
			switch( type )
			{
				case InputType::Sole :
					// Pass hash through unchanged.
					h = scene->globalsPlug()->hash();
					break;
				case InputType::First :
					// Initialise hash and fall through.
					SceneProcessor::hashGlobals( context, parent, h );
				case InputType::Other :
					// Merge input hash.
					scene->globalsPlug()->hash( h );
			}
			return true;
		},
		visitOrder( (Mode)globalsModePlug()->getValue() )
	);
}

IECore::ConstCompoundObjectPtr MergeScenes::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstCompoundObjectPtr result;
	CompoundObjectPtr merged;
	visit(
		connectedInputs(),
		[&] ( InputType type, size_t index, const ScenePlug *scene ) {
			switch( type )
			{
				case InputType::Sole :
					// Pass input through unchanged.
					result = scene->globalsPlug()->getValue();
					break;
				case InputType::First :
					// Initialise merged result and
					// fall through.
					merged = new CompoundObject();
					result = merged;
				case InputType::Other :
					// Merge input globals into result.
					ConstCompoundObjectPtr globals = scene->globalsPlug()->getValue();
					for( const auto &g : globals->members() )
					{
						merged->members()[g.first] = g.second;
					}
			}
			return true;
		},
		visitOrder( (Mode)globalsModePlug()->getValue() )
	);

	return result;
}

void MergeScenes::hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	visit(
		connectedInputs(),
		[&] ( InputType type, size_t index, const ScenePlug *scene ) {
			switch( type )
			{
				case InputType::Sole :
					// Pass hash through unchanged.
					h = scene->setNamesPlug()->hash();
					break;
				case InputType::First :
					// Initialise hash and fall through.
					SceneProcessor::hashSetNames( context, parent, h );
				case InputType::Other :
					// Merge input hash.
					scene->setNamesPlug()->hash( h );
			}
			return true;
		}
	);
}

IECore::ConstInternedStringVectorDataPtr MergeScenes::computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstInternedStringVectorDataPtr result;
	InternedStringVectorDataPtr merged;
	visit(
		connectedInputs(),
		[&] ( InputType type, size_t index, const ScenePlug *scene ) {
			switch( type )
			{
				case InputType::Sole :
					// Pass input through unchanged.
					result = scene->setNamesPlug()->getValue();
					break;
				case InputType::First :
					// Initialise merged result and
					// fall through.
					merged = new InternedStringVectorData();
					result = merged;
				case InputType::Other :
					// This naive approach to merging set names preserves the order of the incoming names,
					// but at the expense of using linear search. We assume that the number of sets is small
					// enough and the InternedString comparison fast enough that this is OK.
					ConstInternedStringVectorDataPtr setNames = scene->setNamesPlug()->getValue();
					for( const auto &setName : setNames->readable() )
					{
						if( std::find( merged->readable().begin(), merged->readable().end(), setName ) == merged->readable().end() )
						{
							 merged->writable().push_back( setName );
						}
					}
			}
			return true;
		}
	);

	return result;
}

void MergeScenes::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	visit(
		connectedInputs(),
		[&] ( InputType type, size_t index, const ScenePlug *scene ) {
			switch( type )
			{
				case InputType::Sole :
					// Pass hash through unchanged.
					h = scene->setPlug()->hash();
					break;
				case InputType::First :
					// Initialise hash and fall through.
					SceneProcessor::hashSet( setName, context, parent, h );
				case InputType::Other :
					// Merge input hash.
					scene->setPlug()->hash( h );
			}
			return true;
		}
	);
}

IECore::ConstPathMatcherDataPtr MergeScenes::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstPathMatcherDataPtr result;
	PathMatcherDataPtr merged;
	visit(
		connectedInputs(),
		[&] ( InputType type, size_t index, const ScenePlug *scene ) {
			switch( type )
			{
				case InputType::Sole :
					// Pass input through unchanged.
					result = scene->setPlug()->getValue();
					break;
				case InputType::First :
					// Initialise merged result and
					// fall through.
					merged = new PathMatcherData();
					result = merged;
				case InputType::Other :
					ConstPathMatcherDataPtr paths = scene->setPlug()->getValue();
					merged->writable().addPaths( paths->readable() );
			}
			return true;
		}
	);

	return result;
}

MergeScenes::VisitOrder MergeScenes::visitOrder( Mode mode, VisitOrder replaceOrder ) const
{
	switch( mode )
	{
		case Mode::Replace :
			return replaceOrder;
		case Mode::Keep :
			return VisitOrder::FirstOnly;
		default :
			return VisitOrder::Forwards;
	}
}

MergeScenes::InputMask MergeScenes::connectedInputs() const
{
	InputMask result;
	for( size_t i = 0, e = inPlugs()->children().size(); i < e; ++i )
	{
		result[i] = (bool)inPlugs()->getChild<ScenePlug>( i )->getInput();
	}

	if( !result.count() )
	{
		result[0] = true;
	}

	return result;
}

template<typename Visitor>
void MergeScenes::visit( InputMask inputMask, Visitor &&visitor, VisitOrder order ) const
{
	assert( inputMask.count() );

	const bool backwards = order == VisitOrder::Backwards || order == VisitOrder::LastOnly;
	const int startIndex = backwards ? inPlugs()->children().size() - 1 : 0;
	const int endIndex = backwards ? -1 : inPlugs()->children().size();
	const int increment = backwards ? -1 : 1;

	InputType type;
	if( order == VisitOrder::FirstOnly || order == VisitOrder::LastOnly || inputMask.count() == 1 )
	{
		type = InputType::Sole;
	}
	else
	{
		type = InputType::First;
	}

	for( int i = startIndex; i != endIndex; i += increment )
	{
		if( inputMask[i] )
		{
			const bool c = visitor( type, i, inPlugs()->getChild<ScenePlug>( i ) );
			if( !c || order == VisitOrder::FirstOnly || order == VisitOrder::LastOnly )
			{
				break;
			}
			type = InputType::Other;
		}
	}
}
