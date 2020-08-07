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

#include "GafferScene/SceneNode.h"

#include "Gaffer/Context.h"

#include "IECore/MessageHandler.h"

#include "boost/bind.hpp"

#include "tbb/blocked_range.h"
#include "tbb/parallel_reduce.h"

using namespace std;
using namespace tbb;
using namespace Imath;
using namespace IECore;
using namespace GafferScene;
using namespace Gaffer;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( SceneNode );

size_t SceneNode::g_firstPlugIndex = 0;

ValuePlug::CachePolicy childBoundsCachePolicy()
{
	ValuePlug::CachePolicy result = ValuePlug::CachePolicy::TaskIsolation;
	if( const char *policy = getenv( "GAFFERSCENE_CHILDBOUNDS_CACHEPOLICY"  ))
	{
		if( !strcmp( policy, "TaskCollaboration" ) )
		{
			result = ValuePlug::CachePolicy::TaskCollaboration;
		}
		else if( strcmp( policy, "TaskIsolation" ) )
		{
			IECore::msg( IECore::Msg::Warning, "SceneNode", "Invalid value for GAFFERSCENE_CHILDBOUNDS_CACHEPOLICY. Must be TaskIsolation or TaskCollaboration." );
		}
	}
	return result;
}

const ValuePlug::CachePolicy g_childBoundsCachePolicy = childBoundsCachePolicy();

SceneNode::SceneNode( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "out", Gaffer::Plug::Out ) );
	addChild( new BoolPlug( "enabled", Gaffer::Plug::In, true ) );

	plugInputChangedSignal().connect( boost::bind( &SceneNode::plugInputChanged, this, ::_1 ) );
}

SceneNode::~SceneNode()
{
}

ScenePlug *SceneNode::outPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *SceneNode::outPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

BoolPlug *SceneNode::enabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const BoolPlug *SceneNode::enabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

void SceneNode::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input == enabledPlug() )
	{
		for( ValuePlugIterator it( outPlug() ); !it.done(); ++it )
		{
			if( (*it)->getInput() )
			{
				// If the output has been connected as a pass-through,
				// then it clearly can't be affected by the enabled plug,
				// because there won't even be a compute() call for it.
				continue;
			}
			outputs.push_back( it->get() );
		}
	}

	if( auto scenePlug = input->parent<ScenePlug>() )
	{
		if( scenePlug->direction() == Plug::Out )
		{
			if( input == scenePlug->childNamesPlug() )
			{
				outputs.push_back( scenePlug->sortedChildNamesPlug() );
			}

			if( input == scenePlug->sortedChildNamesPlug() )
			{
				outputs.push_back( scenePlug->existsPlug() );
			}

			if(
				input == scenePlug->childNamesPlug() ||
				input == scenePlug->boundPlug() ||
				input == scenePlug->transformPlug()
			)
			{
				outputs.push_back( scenePlug->childBoundsPlug() );
			}
		}
	}
}

void SceneNode::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	const ScenePlug *scenePlug = output->parent<ScenePlug>();
	if( scenePlug && enabledPlug()->getValue() )
	{
		// We don't call ComputeNode::hash() immediately here, because for subclasses which
		// want to pass through a specific hash in the hash*() methods it's a waste of time (the
		// hash will get overwritten anyway). Instead we call ComputeNode::hash() in our
		// hash*() implementations, and allow subclass implementations to not call the base class
		// if they intend to overwrite the hash.
		if( output == scenePlug->boundPlug() )
		{
			const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
			hashBound( scenePath, context, scenePlug, h );
		}
		else if( output == scenePlug->transformPlug() )
		{
			const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
			if( scenePath.empty() )
			{
				// the result of compute() will actually be different if we're at the root, so
				// we hash an identity M44fData:
				h.append( IECore::M44fData::staticTypeId() );
				h.append( Imath::M44f() );
			}
			else
			{
				hashTransform( scenePath, context, scenePlug, h );
			}
		}
		else if( output == scenePlug->attributesPlug() )
		{
			const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
			if( scenePath.empty() )
			{
				// the result of compute() will actually be different if we're at the root, so
				// we just hash the default value:
				scenePlug->attributesPlug()->defaultValue()->hash( h );
			}
			else
			{
				hashAttributes( scenePath, context, scenePlug, h );
			}
		}
		else if( output == scenePlug->objectPlug() )
		{
			const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
			if( scenePath.empty() )
			{
				// the result of compute() will actually be different if we're at the root, so
				// we just hash the default value:
				scenePlug->objectPlug()->defaultValue()->hash( h );
			}
			else
			{
				hashObject( scenePath, context, scenePlug, h );
			}
		}
		else if( output == scenePlug->childNamesPlug() )
		{
			const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
			hashChildNames( scenePath, context, scenePlug, h );
		}
		else if( output == scenePlug->globalsPlug() )
		{
			hashGlobals( context, scenePlug, h );
		}
		else if( output == scenePlug->setNamesPlug() )
		{
			hashSetNames( context, scenePlug, h );
		}
		else if( output == scenePlug->setPlug() )
		{
			const IECore::InternedString &setName = context->get<IECore::InternedString>( ScenePlug::setNameContextName );
			hashSet( setName, context, scenePlug, h );
		}
		else if( output == scenePlug->existsPlug() )
		{
			hashExists( context, scenePlug, h );
		}
		else if( output == scenePlug->sortedChildNamesPlug() )
		{
			hashSortedChildNames( context, scenePlug, h );
		}
		else if( output == scenePlug->childBoundsPlug() )
		{
			hashChildBounds( context, scenePlug, h );
		}
	}
	else
	{
		ComputeNode::hash( output, context, h );
	}
}

void SceneNode::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->boundPlug(), context, h );
}

void SceneNode::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->transformPlug(), context, h );
}

void SceneNode::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->attributesPlug(), context, h );
}

void SceneNode::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->objectPlug(), context, h );
}

void SceneNode::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->childNamesPlug(), context, h );
}

void SceneNode::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->globalsPlug(), context, h );
}

void SceneNode::hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->setNamesPlug(), context, h );
}

void SceneNode::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->setPlug(), context, h );
}

void SceneNode::compute( ValuePlug *output, const Context *context ) const
{
	ScenePlug *scenePlug = output->parent<ScenePlug>();
	if( scenePlug )
	{
		if( enabledPlug()->getValue() )
		{
			if( output == scenePlug->boundPlug() )
			{
				const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
				static_cast<AtomicBox3fPlug *>( output )->setValue(
					computeBound( scenePath, context, scenePlug )
				);
			}
			else if( output == scenePlug->transformPlug() )
			{
				const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
				M44f transform;
				if( scenePath.size() ) // scene root must have identity transform
				{
					transform = computeTransform( scenePath, context, scenePlug );
				}
				static_cast<M44fPlug *>( output )->setValue( transform );
			}
			else if( output == scenePlug->attributesPlug() )
			{
				const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
				CompoundObjectPlug *attributesPlug = static_cast<CompoundObjectPlug *>( output );
				if( scenePath.size() ) // scene root must have no attributes
				{
					attributesPlug->setValue( computeAttributes( scenePath, context, scenePlug ) );
				}
				else
				{
					attributesPlug->setValue( attributesPlug->defaultValue() );
				}
			}
			else if( output == scenePlug->objectPlug() )
			{
				const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
				ObjectPlug *objectPlug = static_cast<ObjectPlug *>( output );
				if( scenePath.size() ) // scene root must have no object
				{
					objectPlug->setValue( computeObject( scenePath, context, scenePlug ) );
				}
				else
				{
					objectPlug->setValue( objectPlug->defaultValue() );
				}
			}
			else if( output == scenePlug->childNamesPlug() )
			{
				const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
				static_cast<InternedStringVectorDataPlug *>( output )->setValue(
					computeChildNames( scenePath, context, scenePlug )
				);
			}
			else if( output == scenePlug->globalsPlug() )
			{
				static_cast<CompoundObjectPlug *>( output )->setValue(
					computeGlobals( context, scenePlug )
				);
			}
			else if( output == scenePlug->setNamesPlug() )
			{
				static_cast<InternedStringVectorDataPlug *>( output )->setValue(
					computeSetNames( context, scenePlug )
				);
			}
			else if( output == scenePlug->setPlug() )
			{
				const IECore::InternedString &setName = context->get<IECore::InternedString>( ScenePlug::setNameContextName );
				static_cast<ObjectPlug *>( output )->setValue(
					computeSet( setName, context, scenePlug )
				);
			}
			else if( output == scenePlug->existsPlug() )
			{
				static_cast<BoolPlug *>( output )->setValue( computeExists( context, scenePlug ) );
			}
			else if( output == scenePlug->sortedChildNamesPlug() )
			{
				static_cast<InternedStringVectorDataPlug *>( output )->setValue( computeSortedChildNames( context, scenePlug ) );
			}
			else if( output == scenePlug->childBoundsPlug() )
			{
				static_cast<AtomicBox3fPlug *>( output )->setValue( computeChildBounds( context, scenePlug ) );
			}
		}
		else
		{
			// node is disabled.
			output->setToDefault();
		}
	}
}

Imath::Box3f SceneNode::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	throw IECore::NotImplementedException( string( typeName() ) + "::computeBound" );
}

Imath::M44f SceneNode::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	throw IECore::NotImplementedException( string( typeName() ) + "::computeTransform" );
}

IECore::ConstCompoundObjectPtr SceneNode::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	throw IECore::NotImplementedException( string( typeName() ) + "::computeAttributes" );
}

IECore::ConstObjectPtr SceneNode::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	throw IECore::NotImplementedException( string( typeName() ) + "::computeObject" );
}

IECore::ConstInternedStringVectorDataPtr SceneNode::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	throw IECore::NotImplementedException( string( typeName() ) + "::computeChildNames" );
}

IECore::ConstCompoundObjectPtr SceneNode::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	throw IECore::NotImplementedException( string( typeName() ) + "::computeGlobals" );
}

IECore::ConstInternedStringVectorDataPtr SceneNode::computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	throw IECore::NotImplementedException( string( typeName() ) + "::computeSetNames" );
}

IECore::ConstPathMatcherDataPtr SceneNode::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	throw IECore::NotImplementedException( string( typeName() ) + "::computeSet" );
}

Gaffer::ValuePlug::CachePolicy SceneNode::hashCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( auto parent = output->parent<ScenePlug>() )
	{
		if( output == parent->childBoundsPlug() )
		{
			return g_childBoundsCachePolicy;
		}
	}

	return ComputeNode::hashCachePolicy( output );
}

Gaffer::ValuePlug::CachePolicy SceneNode::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( auto parent = output->parent<ScenePlug>() )
	{
		if( output == parent->childBoundsPlug() )
		{
			return g_childBoundsCachePolicy;
		}
	}

	return ComputeNode::computeCachePolicy( output );
}

IECore::MurmurHash SceneNode::hashOfTransformedChildBounds( const ScenePath &path, const ScenePlug *out, const IECore::InternedStringVectorData *childNamesData ) const
{
	ScenePlug::PathScope pathScope( Context::current(), path );
	return out->childBoundsPlug()->hash();
}

Imath::Box3f SceneNode::unionOfTransformedChildBounds( const ScenePath &path, const ScenePlug *out, const IECore::InternedStringVectorData *childNamesData ) const
{
	ScenePlug::PathScope pathScope( Context::current(), path );
	return out->childBoundsPlug()->getValue();
}

void SceneNode::plugInputChanged( Gaffer::Plug *plug )
{
	// If a node makes a pass-through connection for a `childNamesPlug()` then we
	// want to automatically create the equivalent pass-throughs for the
	// `existsPlug()` and `sortedChildNamesPlug()`, to avoid unnecessary computes.
	// We can't expect derived classes to do this for us, because those plugs are
	// private, so we do it ourselves here.

	if( plug->direction() != Plug::Out )
	{
		return;
	}

	auto scene = plug->parent<ScenePlug>();
	if( !scene || plug != scene->childNamesPlug() )
	{
		return;
	}

	ScenePlug *sourceScene = nullptr;
	if( Plug *source = plug->getInput() )
	{
		sourceScene = source->parent<ScenePlug>();
	}

	scene->existsPlug()->setInput( sourceScene ? sourceScene->existsPlug() : nullptr );
	scene->sortedChildNamesPlug()->setInput( sourceScene ? sourceScene->sortedChildNamesPlug() : nullptr );
}

void SceneNode::hashExists( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->existsPlug(), context, h );

	const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
	if( scenePath.empty() )
	{
		h.append( true );
		return;
	}

	ScenePath parentPath( scenePath ); parentPath.pop_back();
	ScenePlug::PathScope parentScope( context, parentPath );
	if( !parent->existsPlug()->getValue() )
	{
		h.append( false );
		return;
	}

	parent->sortedChildNamesPlug()->hash( h );
	h.append( scenePath.back() );
}

bool SceneNode::computeExists( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	const ScenePath &scenePath = context->get<ScenePath>( ScenePlug::scenePathContextName );
	if( scenePath.empty() )
	{
		// Root always exists
		return true;
	}

	ScenePath parentPath( scenePath ); parentPath.pop_back();
	ScenePlug::PathScope parentScope( context, parentPath );
	if( !parent->existsPlug()->getValue() )
	{
		// If `parentPath` doesn't exist, then neither can `scenePath`
		return false;
	}

	// Search in the sorted child names of our parent.

	auto sortedChildNamesData = parent->sortedChildNamesPlug()->getValue();
	auto &sortedChildNames = sortedChildNamesData->readable();
	return std::binary_search( sortedChildNames.begin(), sortedChildNames.end(), scenePath.back() );
}

void SceneNode::hashSortedChildNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->sortedChildNamesPlug(), context, h );
	parent->childNamesPlug()->hash( h );
}

IECore::ConstInternedStringVectorDataPtr SceneNode::computeSortedChildNames( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstInternedStringVectorDataPtr childNamesData = parent->childNamesPlug()->getValue();
	if( childNamesData->readable().size() <= 1 )
	{
		// Already sorted
		return childNamesData;
	}

	InternedStringVectorDataPtr sorted = new InternedStringVectorData;
	sorted->writable() = childNamesData->readable();
	std::sort( sorted->writable().begin(), sorted->writable().end() );
	return sorted;
}

void SceneNode::hashChildBounds( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	ComputeNode::hash( parent->childBoundsPlug(), context, h );
	ConstInternedStringVectorDataPtr childNamesData = parent->childNamesPlug()->getValue();
	const vector<InternedString> &childNames = childNamesData->readable();
	if( childNames.empty() )
	{
		return;
	}

	const ThreadState &threadState = ThreadState::current();
	using Range = blocked_range<size_t>;
	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

	const IECore::MurmurHash reduction = parallel_deterministic_reduce(
		Range( 0, childNames.size() ),
		h,
		[&] ( const Range &range, const MurmurHash &hash ) {

			ScenePlug::PathScope pathScope( threadState );
			auto childPath = context->get<ScenePath>( ScenePlug::scenePathContextName );
			childPath.push_back( InternedString() ); // room for the child name

			MurmurHash result = hash;
			for( size_t i = range.begin(); i != range.end(); ++i )
			{
				childPath.back() = childNames[i];
				pathScope.setPath( childPath );
				parent->boundPlug()->hash( result );
				parent->transformPlug()->hash( result );
			}
			return result;

		},
		[] ( const MurmurHash &x, const MurmurHash &y ) {

			MurmurHash result = x;
			result.append( y );
			return result;
		},
		simple_partitioner(),
		taskGroupContext
	);

	h.append( reduction );
}

Imath::Box3f SceneNode::computeChildBounds( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstInternedStringVectorDataPtr childNamesData = parent->childNamesPlug()->getValue();
	const vector<InternedString> &childNames = childNamesData->readable();
	if( childNames.empty() )
	{
		return Box3f();
	}

	const ThreadState &threadState = ThreadState::current();
	using Range = blocked_range<size_t>;
	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );

	return tbb::parallel_reduce(
		Range( 0, childNames.size() ),
		Box3f(),
		[&] ( const Range &range, const Box3f &bound ) {

			ScenePlug::PathScope pathScope( threadState );
			auto childPath = context->get<ScenePath>( ScenePlug::scenePathContextName );
			childPath.push_back( InternedString() ); // room for the child name

			Box3f result = bound;
			for( size_t i = range.begin(); i != range.end(); ++i )
			{
				childPath.back() = childNames[i];
				pathScope.setPath( childPath );
				Box3f childBound = parent->boundPlug()->getValue();
				childBound = transform( childBound, parent->transformPlug()->getValue() );
				result.extendBy( childBound );
			}
			return result;

		},
		[] ( const Box3f &x, const Box3f &y ) {

			Box3f result = x;
			result.extendBy( y );
			return result;

		},
		tbb::auto_partitioner(),
		taskGroupContext
	);
}
