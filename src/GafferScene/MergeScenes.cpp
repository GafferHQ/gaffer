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
GAFFER_NODE_DEFINE_TYPE( MergeScenes );

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

enum class Count
{
	Zero,
	One,
	MoreThanOne
};

size_t firstAndCount( const std::vector<bool> &inputs, Count &count )
{
	count = Count::Zero;
	size_t first = 0;

	for( size_t i = 0; i < inputs.size(); ++i )
	{
		if( inputs[i] )
		{
			if( count == Count::Zero )
			{
				first = i;
				count = Count::One;
			}
			else
			{
				count = Count::MoreThanOne;
				return first;
			}
		}
	}

	return first;
}

class MergeContextHandler
{
public:
	MergeContextHandler( const MergeScenes* mergeNode, const Context *context )
		: m_mode( (MergeScenes::MergeMode)mergeNode->modePlug()->getValue() )
	{
		if( m_mode == MergeScenes::MergeMode::Collect )
		{
			m_contextValuesData = mergeNode->contextValuesPlug()->getValue();
			m_contextValues = &m_contextValuesData->readable();
			m_contextVariable = mergeNode->contextVariablePlug()->getValue();
			m_indexContextVariable = mergeNode->indexContextVariablePlug()->getValue();

			m_numContexts = m_contextValues->size();

			m_scope.emplace( context );

			m_context = m_scope->context();
		}
		else
		{
			m_numContexts = 1;
			m_context = context;
		}
	}

	int numContexts()
	{
		return m_numContexts;
	}

	int setContextAndGetPlugIndex( int index )
	{
		if( m_mode == MergeScenes::MergeMode::Collect )
		{
			m_contextIndex = index % m_numContexts;
			m_scope->set( m_contextVariable, &( (*m_contextValues)[m_contextIndex] ) );
			m_scope->set( m_indexContextVariable, &m_contextIndex );
			return index / m_numContexts;
		}
		else
		{
			return index;
		}
	}

	bool hasContextOverrides() const
	{
		return m_scope.has_value();
	}

	const Context *context()
	{
		return m_context;
	}

	// If we need to set a path, we should do it in the same scope that is already
	// being allocated in Collect mode.
	void setPath( const ScenePlug::ScenePath *scenePath )
	{
		if( !m_scope )
		{
			m_scope.emplace( m_context );
			m_context = m_scope->context();
		}
		m_scope->set( ScenePlug::scenePathContextName, scenePath );
	}

private:

	const MergeScenes::MergeMode m_mode;
	ConstStringVectorDataPtr m_contextValuesData;
	const std::vector<std::string> *m_contextValues;
	std::string m_contextVariable;
	std::string m_indexContextVariable;

	int m_numContexts;
	const Context *m_context;

	int m_contextIndex;

	std::optional<Context::EditableScope> m_scope;
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// MergeScenes
//////////////////////////////////////////////////////////////////////////

MergeScenes::MergeScenes( const std::string &name )
	:	SceneProcessor( name, /* minInputs = */ 2, /* maxInputs = */ 32 )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "transformMode", Plug::In, (int)Mode::Keep, (int)Mode::Keep, (int)Mode::Replace ) );
	addChild( new IntPlug( "attributesMode", Plug::In, (int)Mode::Keep, (int)Mode::Keep, (int)Mode::Merge ) );
	addChild( new IntPlug( "objectMode", Plug::In, (int)Mode::Keep, (int)Mode::Keep, (int)Mode::Replace ) );
	addChild( new IntPlug( "globalsMode", Plug::In, (int)Mode::Keep, (int)Mode::Keep, (int)Mode::Merge ) );
	addChild( new BoolPlug( "adjustBounds", Plug::In, true ) );

	addChild(
		new IntPlug(
			"mode",              // name
			Plug::In,            // direction
			(int)MergeMode::Standard, // default
			(int)MergeMode::Standard, // min
			(int)MergeMode::Collect   // max
		)
	);

	addChild( new StringVectorDataPlug( "contextValues", Plug::In ) );
	addChild( new StringPlug( "contextVariable", Plug::In, "merge:value" ) );
	addChild( new StringPlug( "indexContextVariable", Plug::In, "merge:index" ) );

	addChild( new BoolVectorDataPlug( "__activeInputs", Plug::Out ) );
	addChild( new AtomicBox3fPlug( "__mergedDescendantsBound", Plug::Out ) );

	outPlug()->childBoundsPlug()->setFlags( Plug::AcceptsDependencyCycles, true );
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

Gaffer::IntPlug *MergeScenes::modePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::IntPlug *MergeScenes::modePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

Gaffer::StringVectorDataPlug *MergeScenes::contextValuesPlug()
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::StringVectorDataPlug *MergeScenes::contextValuesPlug() const
{
	return getChild<StringVectorDataPlug>( g_firstPlugIndex + 6 );
}

Gaffer::StringPlug *MergeScenes::contextVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::StringPlug *MergeScenes::contextVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 7 );
}

Gaffer::StringPlug *MergeScenes::indexContextVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 8 );
}

const Gaffer::StringPlug *MergeScenes::indexContextVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 8 );
}

Gaffer::BoolVectorDataPlug *MergeScenes::activeInputsPlug()
{
	return getChild<BoolVectorDataPlug>( g_firstPlugIndex + 9 );
}

const Gaffer::BoolVectorDataPlug *MergeScenes::activeInputsPlug() const
{
	return getChild<BoolVectorDataPlug>( g_firstPlugIndex + 9 );
}

Gaffer::AtomicBox3fPlug *MergeScenes::mergedDescendantsBoundPlug()
{
	return getChild<AtomicBox3fPlug>( g_firstPlugIndex + 10 );
}

const Gaffer::AtomicBox3fPlug *MergeScenes::mergedDescendantsBoundPlug() const
{
	return getChild<AtomicBox3fPlug>( g_firstPlugIndex + 10 );
}

void MergeScenes::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );

	if(
		input == modePlug() || input == contextValuesPlug() ||
		input == contextVariablePlug() || input == indexContextVariablePlug()
	)
	{
		// Changing the context we evaluate the input in affects everything
		outputs.push_back( activeInputsPlug() );
		outputs.push_back( outPlug()->transformPlug() );
		outputs.push_back( mergedDescendantsBoundPlug() );
		outputs.push_back( outPlug()->boundPlug() );
		outputs.push_back( outPlug()->attributesPlug() );
		outputs.push_back( outPlug()->objectPlug() );
		outputs.push_back( outPlug()->childNamesPlug() );
		outputs.push_back( outPlug()->globalsPlug() );
		outputs.push_back( outPlug()->setNamesPlug() );
		outputs.push_back( outPlug()->setPlug() );
	}

	const ScenePlug *scene = inPlugs()->isAncestorOf( input ) ? input->parent<ScenePlug>() : nullptr;

	if( scene && input == scene->existsPlug() )
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
		input == mergedDescendantsBoundPlug() ||
		input == outPlug()->objectPlug() ||
		input == outPlug()->childBoundsPlug()
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
		static_cast<BoolVectorDataPlug *>( output )->setValue( computeActiveInputs( context ) );
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
	// We anticipate very few unique values for the active inputs, as in most
	// cases they are inherited directly down the hierarchy. So we want to use a
	// perfect hash to avoid making lots of duplicate cache entries containing
	// those repeated values. This means our hash needs to use
	// `scene->existsPlug()->getValue()` rather than
	// `scene->existsPlug()->hash()`. Which means our hash function is actually
	// _identical_ to our compute, so we might as well just call it rather than
	// duplicate the code.
	h.append( computeActiveInputs( context )->readable() );
}

ConstBoolVectorDataPtr MergeScenes::computeActiveInputs( const Gaffer::Context *context ) const
{
	const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );

	BoolVectorDataPtr resultData = new BoolVectorData();
	auto &result = resultData->writable();

	if( scenePath.empty() )
	{

		// Root. Every input is active here, but there's a wrinkle : the default
		// value for `ScenePlug.exists` is `true`, and this is the value we'll
		// get if the input is not from a computed output. This would mean that
		// the input would claim to be active for _any_ scene location. We deal
		// with this once here at the root rather than repeat the workaround at
		// each descendant location;

		std::vector<bool> connectedIns = connectedInputs( context );
		result.resize( connectedIns.size(), false );
		visit(
			connectedIns, context,
			[&result] ( InputType type, size_t index, const ScenePlug *scene ) {
				if( scene->childNamesPlug()->getValue()->readable().size() )
				{
					result[index] = true;
				}
				return true;
			}
		);
	}
	else
	{
		// Get active inputs from the parent.
		ConstBoolVectorDataPtr parentActiveInputsData;
		{
			ScenePath parentPath = scenePath; parentPath.pop_back();
			ScenePlug::PathScope parentScope( context, &parentPath );
			parentActiveInputsData = activeInputsPlug()->getValue();
		}

		const auto &parentActiveInputs = parentActiveInputsData->readable();

		Count parentActiveInputsCount;
		firstAndCount( parentActiveInputs, parentActiveInputsCount );
		if( parentActiveInputsCount == Count::One )
		{
			// It is forbidden for anyone to evaluate us for a location
			// that doesn't exist. Therefore, if our parent only has
			// one active input, then that input must still be active for
			// us.
			return parentActiveInputsData;
		}
		else
		{
			result.resize( parentActiveInputs.size(), false );

			// Figure out which of those parent inputs are
			// still active. Using the parent active inputs as
			// a mask reduces the number of existence queries
			// we must make when merging many sparsely overlapping
			// scenes.
			visit(
				parentActiveInputs, context,
				[&result] ( InputType type, size_t index, const ScenePlug *scene ) {
					if( scene->existsPlug()->getValue() )
					{
						result[index] = true;
					}
					return true;
				}
			);
		}
	}

	return resultData;
}

void MergeScenes::hashMergedDescendantsBound( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	#ifndef NDEBUG
	// mergedDescendantBound is never evaluated when there is a single input
	Count activeInputsCount;
	firstAndCount( activeInputsPlug()->getValue()->readable(), activeInputsCount );
	assert( activeInputsCount == Count::MoreThanOne );
	#endif

	ConstInternedStringVectorDataPtr childNamesData = outPlug()->childNamesPlug()->getValue();
	if( childNamesData->readable().empty() )
	{
		return;
	}

	ScenePath childPath = context->get<ScenePath>( ScenePlug::scenePathContextName );
	childPath.push_back( InternedString() ); // Room for child name

	MergeContextHandler contextHandler( this, context );

	// Make a PathScope independent from the context handler, so we can alternate evaluations
	// that don't include Collect context variables.
	ScenePlug::PathScope pathScope( context );

	for( const auto &childName : childNamesData->readable() )
	{
		childPath.back() = childName;
		pathScope.setPath( &childPath );

		ConstBoolVectorDataPtr childActiveInputsData = activeInputsPlug()->getValue();
		const auto &childActiveInputs = childActiveInputsData->readable();
		Count childActiveInputsCount;
		size_t childFirstActiveIndex = firstAndCount( childActiveInputs, childActiveInputsCount );

		// Get ready to evaluate the first active input
		int plugIndex = contextHandler.setContextAndGetPlugIndex( childFirstActiveIndex );
		const ScenePlug *childScene = inPlugs()->getChild<ScenePlug>( plugIndex );

		if( contextHandler.hasContextOverrides() )
		{
			// If the contextHandler has context overrides, we need to do some extra work here
			// since we're not using its context directly. Set the correct path on its context,
			// and then explicitly scope it using Context::Scope
			contextHandler.setPath( &childPath );
			Context::Scope handlerScope( contextHandler.context() );

			childScene->boundPlug()->hash( h );

			childScene->transformPlug()->hash( h );
		}
		else
		{
			childScene->boundPlug()->hash( h );
			childScene->transformPlug()->hash( h );
		}

		if( childActiveInputsCount == Count::MoreThanOne )
		{
			mergedDescendantsBoundPlug()->hash( h );
		}

	};
}

const Imath::Box3f MergeScenes::computeMergedDescendantsBound( const Gaffer::Context *context ) const
{
	#ifndef NDEBUG
	// mergedDescendantBound is never evaluated when there is a single input
	Count activeInputsCount;
	firstAndCount( activeInputsPlug()->getValue()->readable(), activeInputsCount );
	assert( activeInputsCount == Count::MoreThanOne );
	#endif

	ConstInternedStringVectorDataPtr childNamesData = outPlug()->childNamesPlug()->getValue();
	if( childNamesData->readable().empty() )
	{
		// No children. There can be no descendants to merge.
		return Box3f();
	}

	ScenePath childPath = context->get<ScenePath>( ScenePlug::scenePathContextName );
	childPath.push_back( InternedString() ); // Room for child name

	MergeContextHandler contextHandler( this, context );

	// Make a PathScope independent from the context handler, so we can alternate evaluations
	// that don't include Collect context variables.
	ScenePlug::PathScope pathScope( context );

	Box3f result;
	for( const auto &childName : childNamesData->readable() )
	{
		childPath.back() = childName;
		pathScope.setPath( &childPath );

		ConstBoolVectorDataPtr childActiveInputsData = activeInputsPlug()->getValue();
		const auto &childActiveInputs = childActiveInputsData->readable();
		Count childActiveInputsCount;
		size_t childFirstActiveIndex = firstAndCount( childActiveInputs, childActiveInputsCount );

		M44f childTransform;
		Box3f bound;

		// Get ready to evaluate the first active input
		int plugIndex = contextHandler.setContextAndGetPlugIndex( childFirstActiveIndex );
		const ScenePlug *childScene = inPlugs()->getChild<ScenePlug>( plugIndex );

		if( contextHandler.hasContextOverrides() )
		{
			// If the contextHandler has context overrides, we need to do some extra work here
			// since we're not using its context directly. Set the correct path on its context,
			// and then explicitly scope it using Context::Scope
			contextHandler.setPath( &childPath );
			Context::Scope handlerScope( contextHandler.context() );

			// We always need to include the bound from the active child, which will include the bound
			// of any object present at that location.
			bound = childScene->boundPlug()->getValue();

			childTransform = childScene->transformPlug()->getValue();
		}
		else
		{
			bound = childScene->boundPlug()->getValue();

			childTransform = childScene->transformPlug()->getValue();
		}

		if( childActiveInputsCount == Count::MoreThanOne )
		{
			// If there are multiple inputs, then the bound from the first active input may not
			// include other descendants being merged in lower in the hierarchy, and we need to
			// recurse.
			bound.extendBy( mergedDescendantsBoundPlug()->getValue() );
		}

		result.extendBy( transform( bound, childTransform ) );
	};
	return result;
}

void MergeScenes::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	// Pass through.
	Count activeInputsCount;
	const size_t firstActiveIndex = firstAndCount( activeInputsPlug()->getValue()->readable(), activeInputsCount );

	if( activeInputsCount == Count::Zero )
	{
		h = inPlugs()->getChild<ScenePlug>( 0 )->boundPlug()->defaultHash();
		return;
	}

	if( activeInputsCount == Count::One || !adjustBoundsPlug()->getValue() )
	{
		MergeContextHandler contextHandler( this, context );
		int plugIndex = contextHandler.setContextAndGetPlugIndex( firstActiveIndex );
		h = inPlugs()->getChild<ScenePlug>( plugIndex )->boundPlug()->hash();
		return;
	}

	// Objects/transforms always from first active input.

	if( objectModePlug()->getValue() == (int)Mode::Keep && transformModePlug()->getValue() == (int)Mode::Keep )
	{
		SceneProcessor::hashBound( path, context, parent, h );

		mergedDescendantsBoundPlug()->hash( h );

		MergeContextHandler contextHandler( this, context );
		int plugIndex = contextHandler.setContextAndGetPlugIndex( firstActiveIndex );
		inPlugs()->getChild<ScenePlug>( plugIndex )->boundPlug()->hash( h );
		return;
	}

	// Worst case scenario

	SceneProcessor::hashBound( path, context, parent, h );
	outPlug()->objectPlug()->hash( h );
	outPlug()->childBoundsPlug()->hash( h );
}

Imath::Box3f MergeScenes::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	// Pass through for simple cases.

	Count activeInputsCount;
	const size_t firstActiveIndex = firstAndCount( activeInputsPlug()->getValue()->readable(), activeInputsCount );

	if( activeInputsCount == Count::Zero )
	{
		return inPlugs()->getChild<ScenePlug>( 0 )->boundPlug()->defaultValue();
	}

	if( activeInputsCount == Count::One || !adjustBoundsPlug()->getValue() )
	{
		MergeContextHandler contextHandler( this, context );
		int plugIndex = contextHandler.setContextAndGetPlugIndex( firstActiveIndex );
		return inPlugs()->getChild<ScenePlug>( plugIndex )->boundPlug()->getValue();
	}

	// If objects and transforms always come from the first active input,
	// then the bound from the first input will already be correct for them.
	// We just need to extend it to account for any new descendants
	// being merged in from the other inputs.

	if( objectModePlug()->getValue() == (int)Mode::Keep && transformModePlug()->getValue() == (int)Mode::Keep )
	{
		Box3f result = mergedDescendantsBoundPlug()->getValue();

		MergeContextHandler contextHandler( this, context );
		int plugIndex = contextHandler.setContextAndGetPlugIndex( firstActiveIndex );
		result.extendBy( inPlugs()->getChild<ScenePlug>( plugIndex )->boundPlug()->getValue() );
		return result;
	}

	// Otherwise we're in the worst case scenario, and transforms and
	// objects can be taken from any input willy nilly. We have to
	// compute everything by brute force.

	Box3f result = SceneAlgo::bound( outPlug()->objectPlug()->getValue().get() );
	result.extendBy( outPlug()->childBoundsPlug()->getValue() );
	return result;
}

void MergeScenes::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ConstBoolVectorDataPtr activeInputsData = activeInputsPlug()->getValue();
	const auto &activeInputs = activeInputsData->readable();
	Count activeInputsCount;
	firstAndCount( activeInputs, activeInputsCount );

	if( activeInputsCount == Count::Zero )
	{
		h = inPlugs()->getChild<ScenePlug>( 0 )->transformPlug()->defaultHash();
		return;
	}

	visit(
		activeInputs, context,
		[&] ( InputType type, size_t index, const ScenePlug *scene ) {
			h = scene->transformPlug()->hash();
			return false;
		},
		visitOrder( (Mode)transformModePlug()->getValue() )
	);
}

Imath::M44f MergeScenes::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstBoolVectorDataPtr activeInputsData = activeInputsPlug()->getValue();
	const auto &activeInputs = activeInputsData->readable();
	Count activeInputsCount;
	firstAndCount( activeInputs, activeInputsCount );

	if( activeInputsCount == Count::Zero )
	{
		return inPlugs()->getChild<ScenePlug>( 0 )->transformPlug()->defaultValue();
	}

	M44f result;
	visit(
		activeInputs, context,
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
	ConstBoolVectorDataPtr activeInputsData = activeInputsPlug()->getValue();
	const auto &activeInputs = activeInputsData->readable();
	Count activeInputsCount;
	firstAndCount( activeInputs, activeInputsCount );

	if( activeInputsCount == Count::Zero )
	{
		h = inPlugs()->getChild<ScenePlug>( 0 )->attributesPlug()->defaultHash();
		return;
	}

	visit(
		activeInputs, context,
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
					[[fallthrough]];
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
	ConstBoolVectorDataPtr activeInputsData = activeInputsPlug()->getValue();
	const auto &activeInputs = activeInputsData->readable();
	Count activeInputsCount;
	firstAndCount( activeInputs, activeInputsCount );

	if( activeInputsCount == Count::Zero )
	{
		return inPlugs()->getChild<ScenePlug>( 0 )->attributesPlug()->defaultValue();
	}

	ConstCompoundObjectPtr result;
	CompoundObjectPtr merged;
	visit(
		activeInputs, context,
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
					[[fallthrough]];
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
	ConstBoolVectorDataPtr activeInputsData = activeInputsPlug()->getValue();
	const auto &activeInputs = activeInputsData->readable();
	Count activeInputsCount;
	firstAndCount( activeInputs, activeInputsCount );

	if( activeInputsCount == Count::Zero )
	{
		h = inPlugs()->getChild<ScenePlug>( 0 )->objectPlug()->defaultHash();
		return;
	}

	visit(
		activeInputs, context,
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
					[[fallthrough]];
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
	ConstBoolVectorDataPtr activeInputsData = activeInputsPlug()->getValue();
	const auto &activeInputs = activeInputsData->readable();
	Count activeInputsCount;
	firstAndCount( activeInputs, activeInputsCount );

	if( activeInputsCount == Count::Zero )
	{
		return inPlugs()->getChild<ScenePlug>( 0 )->objectPlug()->defaultValue();
	}

	ConstObjectPtr result = IECore::NullObject::defaultNullObject();
	visit(
		activeInputs, context,
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
	ConstBoolVectorDataPtr activeInputsData = activeInputsPlug()->getValue();
	const auto &activeInputs = activeInputsData->readable();
	Count activeInputsCount;
	firstAndCount( activeInputs, activeInputsCount );

	if( activeInputsCount == Count::Zero )
	{
		h = inPlugs()->getChild<ScenePlug>( 0 )->childNamesPlug()->defaultHash();
		return;
	}

	visit(
		activeInputs, context,
		[&] ( InputType type, size_t index, const ScenePlug *scene ) {
			switch( type )
			{
				case InputType::Sole :
					h = scene->childNamesPlug()->hash();
					break;
				case InputType::First :
					SceneProcessor::hashChildNames( path, context, parent, h );
					[[fallthrough]];
				case InputType::Other :
					scene->childNamesPlug()->hash( h );
			}
			return true;
		}
	);
}

IECore::ConstInternedStringVectorDataPtr MergeScenes::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstBoolVectorDataPtr activeInputsData = activeInputsPlug()->getValue();
	const auto &activeInputs = activeInputsData->readable();
	Count activeInputsCount;
	firstAndCount( activeInputs, activeInputsCount );

	if( activeInputsCount == Count::Zero )
	{
		return inPlugs()->getChild<ScenePlug>( 0 )->childNamesPlug()->defaultValue();
	}

	ConstInternedStringVectorDataPtr result;
	InternedStringVectorDataPtr merged;
	unordered_set<InternedString> visited;

	visit(
		activeInputs, context,
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
	const std::vector<bool> connectedIns( connectedInputs( context ) );
	Count connectedInputsCount;
	firstAndCount( connectedIns, connectedInputsCount );
	if( connectedInputsCount == Count::Zero )
	{
		h = inPlugs()->getChild<ScenePlug>( 0 )->globalsPlug()->defaultHash();
		return;
	}

	visit(
		connectedIns, context,
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
					[[fallthrough]];
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
	const std::vector<bool> connectedIns( connectedInputs( context ) );
	Count connectedInputsCount;
	firstAndCount( connectedIns, connectedInputsCount );
	if( connectedInputsCount == Count::Zero )
	{
		return inPlugs()->getChild<ScenePlug>( 0 )->globalsPlug()->defaultValue();
	}

	ConstCompoundObjectPtr result;
	CompoundObjectPtr merged;
	visit(
		connectedIns, context,
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
					[[fallthrough]];
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
	const std::vector<bool> connectedIns( connectedInputs( context ) );
	Count connectedInputsCount;
	firstAndCount( connectedIns, connectedInputsCount );
	if( connectedInputsCount == Count::Zero )
	{
		h = inPlugs()->getChild<ScenePlug>( 0 )->setNamesPlug()->defaultHash();
		return;
	}

	visit(
		connectedIns, context,
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
					[[fallthrough]];
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
	const std::vector<bool> connectedIns( connectedInputs( context ) );
	Count connectedInputsCount;
	firstAndCount( connectedIns, connectedInputsCount );
	if( connectedInputsCount == Count::Zero )
	{
		return inPlugs()->getChild<ScenePlug>( 0 )->setNamesPlug()->defaultValue();
	}

	ConstInternedStringVectorDataPtr result;
	InternedStringVectorDataPtr merged;
	visit(
		connectedIns, context,
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
					[[fallthrough]];
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
	const std::vector<bool> connectedIns( connectedInputs( context ) );
	Count connectedInputsCount;
	firstAndCount( connectedIns, connectedInputsCount );
	if( connectedInputsCount == Count::Zero )
	{
		h = inPlugs()->getChild<ScenePlug>( 0 )->setPlug()->defaultHash();
		return;
	}

	/// \todo It might be a good idea to implement a pass-through for
	/// the cases where the set only exists in one of the inputs.
	visit(
		connectedIns, context,
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
					[[fallthrough]];
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
	const std::vector<bool> connectedIns( connectedInputs( context ) );
	Count connectedInputsCount;
	firstAndCount( connectedIns, connectedInputsCount );
	if( connectedInputsCount == Count::Zero )
	{
		return inPlugs()->getChild<ScenePlug>( 0 )->setPlug()->defaultValue();
	}

	ConstPathMatcherDataPtr result;
	PathMatcherDataPtr merged;
	visit(
		connectedIns, context,
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
					[[fallthrough]];
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

std::vector<bool> MergeScenes::connectedInputs( const Gaffer::Context *context ) const
{
	MergeContextHandler contextHandler( this, context );
	int nContexts = contextHandler.numContexts();

	size_t numPlugs = inPlugs()->children().size();

	std::vector<bool> result;
	result.reserve( numPlugs * nContexts );

	for( size_t i = 0; i < numPlugs; ++i )
	{
		bool connected = inPlugs()->getChild<ScenePlug>( i )->getInput();
		// The connected value is the same across a plug, but we still output an element
		// per context per plug - that keeps these indices matching up with the indices
		// used in MergeContextHandler and visit()
		for( int j = 0; j < nContexts; j++ )
		{
			result.push_back( connected );
		}
	}

	return result;
}

template<typename Visitor>
void MergeScenes::visit( const std::vector<bool> &inputMask, const Gaffer::Context *context, Visitor &&visitor, VisitOrder order ) const
{
	Count inputMaskCount;
	firstAndCount( inputMask, inputMaskCount );
	assert( inputMaskCount != Count::Zero );

	MergeContextHandler contextHandler( this, context );
	int nContexts = contextHandler.numContexts();

	const bool backwards = order == VisitOrder::Backwards || order == VisitOrder::LastOnly;
	const int startIndex = backwards ? inPlugs()->children().size() * nContexts - 1 : 0;
	const int endIndex = backwards ? -1 : inPlugs()->children().size() * nContexts;
	const int increment = backwards ? -1 : 1;

	InputType type;
	if( order == VisitOrder::FirstOnly || order == VisitOrder::LastOnly || inputMaskCount == Count::One )
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
			int plugIndex = contextHandler.setContextAndGetPlugIndex( i );
			const bool c = visitor( type, i, inPlugs()->getChild<ScenePlug>( plugIndex ) );
			if( !c || order == VisitOrder::FirstOnly || order == VisitOrder::LastOnly )
			{
				break;
			}
			type = InputType::Other;
		}
	}
}
