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

#include "GafferScene/SceneAlgo.h"

#include "GafferScene/CameraTweaks.h"
#include "GafferScene/CopyAttributes.h"
#include "GafferScene/Filter.h"
#include "GafferScene/FilterProcessor.h"
#include "GafferScene/LocaliseAttributes.h"
#include "GafferScene/MergeScenes.h"
#include "GafferScene/PathFilter.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/SetAlgo.h"
#include "GafferScene/ShaderTweaks.h"
#include "GafferScene/ShuffleAttributes.h"

#include "Gaffer/Context.h"
#include "Gaffer/Monitor.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"
#include "Gaffer/Process.h"
#include "Gaffer/ScriptNode.h"

#include "IECoreScene/Camera.h"
#include "IECoreScene/ClippingPlane.h"
#include "IECoreScene/CoordinateSystem.h"
#include "IECoreScene/MatrixMotionTransform.h"
#include "IECoreScene/VisibleRenderable.h"

#include "IECore/MessageHandler.h"
#include "IECore/NullObject.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/unordered_map.hpp"

#include "tbb/concurrent_unordered_set.h"
#include "tbb/parallel_for.h"
#include "tbb/spin_mutex.h"
#include "tbb/task.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Filter queries
//////////////////////////////////////////////////////////////////////////

namespace
{

void filteredNodesWalk( Plug *filterPlug, std::unordered_set<FilteredSceneProcessor *> &result )
{
	for( const auto &o : filterPlug->outputs() )
	{
		if( auto filteredSceneProcessor = runTimeCast<FilteredSceneProcessor>( o->node() ) )
		{
			if( o == filteredSceneProcessor->filterPlug() )
			{
				result.insert( filteredSceneProcessor );
			}
		}
		else if( auto filterProcessor = runTimeCast<FilterProcessor>( o->node() ) )
		{
			if( o == filterProcessor->inPlug() || o->parent() == filterProcessor->inPlugs() )
			{
				filteredNodesWalk( filterProcessor->outPlug(), result );
			}
		}
		else if( auto pathFilter = runTimeCast<PathFilter>( o->node() ) )
		{
			if( o == pathFilter->rootsPlug() )
			{
				filteredNodesWalk( pathFilter->outPlug(), result );
			}
		}
		filteredNodesWalk( o, result );
	}
}

struct ThreadablePathAccumulator
{
	ThreadablePathAccumulator( PathMatcher &result): m_result( result ){}

	bool operator()( const GafferScene::ScenePlug *scene, const GafferScene::ScenePlug::ScenePath &path )
	{
		tbb::spin_mutex::scoped_lock lock( m_mutex );
		m_result.addPath( path );
		return true;
	}

	tbb::spin_mutex m_mutex;
	PathMatcher &m_result;

};

struct ThreadablePathHashAccumulator
{
	ThreadablePathHashAccumulator(): m_h1Accum( 0 ), m_h2Accum( 0 ){}

	bool operator()( const GafferScene::ScenePlug *scene, const GafferScene::ScenePlug::ScenePath &path )
	{
		// The hash should depend on all the paths visited, but doesn't depend on the order we visit them
		// - in fact it must be consistent even when parallel traversal visits in a non-deterministic order.
		// We can achieve this by summing all the element hashes into an atomic accumulator - because any
		// change gets evenly distributed into the bit pattern of the MurmurHash, this sum will change if
		// any element changes, but is not affected by what order the sum runs in.
		// There isn't an easy way to do a 128 bit atomic sum, but two 64 bit sums should be pretty well
		// as good ( the only weakness I can see is that if you summed 2**64 identical hashes, they would
		// cancel out, but I can't see that arising here ).
		IECore::MurmurHash h;
		if( path.size() )
		{
			h.append( path.data(), path.size() );
		}
		else
		{
			h.append( 0 );
		}
		m_h1Accum += h.h1();
		m_h2Accum += h.h2();
		return true;
	}

	std::atomic<uint64_t> m_h1Accum, m_h2Accum;
};

} // namespace

std::unordered_set<FilteredSceneProcessor *> GafferScene::SceneAlgo::filteredNodes( Filter *filter )
{
	std::unordered_set<FilteredSceneProcessor *> result;
	filteredNodesWalk( filter->outPlug(), result );
	return result;
}

void GafferScene::SceneAlgo::matchingPaths( const Filter *filter, const ScenePlug *scene, PathMatcher &paths )
{
	matchingPaths( filter->outPlug(), scene, paths );
}

void GafferScene::SceneAlgo::matchingPaths( const FilterPlug *filterPlug, const ScenePlug *scene, PathMatcher &paths )
{
	ThreadablePathAccumulator f( paths );
	GafferScene::SceneAlgo::filteredParallelTraverse( scene, filterPlug, f );
}

void GafferScene::SceneAlgo::matchingPaths( const FilterPlug *filterPlug, const ScenePlug *scene, const ScenePlug::ScenePath &root, IECore::PathMatcher &paths )
{
	ThreadablePathAccumulator f( paths );
	GafferScene::SceneAlgo::filteredParallelTraverse( scene, filterPlug, f, root );
}

void GafferScene::SceneAlgo::matchingPaths( const PathMatcher &filter, const ScenePlug *scene, PathMatcher &paths )
{
	ThreadablePathAccumulator f( paths );
	GafferScene::SceneAlgo::filteredParallelTraverse( scene, filter, f );
}

IECore::MurmurHash GafferScene::SceneAlgo::matchingPathsHash( const Filter *filter, const ScenePlug *scene )
{
	return matchingPathsHash( filter->outPlug(), scene );
}

IECore::MurmurHash GafferScene::SceneAlgo::matchingPathsHash( const GafferScene::FilterPlug *filterPlug, const ScenePlug *scene )
{
	ThreadablePathHashAccumulator f;
	GafferScene::SceneAlgo::filteredParallelTraverse( scene, filterPlug, f );
	return IECore::MurmurHash( f.m_h1Accum, f.m_h2Accum );
}

IECore::MurmurHash GafferScene::SceneAlgo::matchingPathsHash( const GafferScene::FilterPlug *filterPlug, const ScenePlug *scene, const ScenePlug::ScenePath &root )
{
	ThreadablePathHashAccumulator f;
	GafferScene::SceneAlgo::filteredParallelTraverse( scene, filterPlug, f, root );
	return IECore::MurmurHash( f.m_h1Accum, f.m_h2Accum );
}

IECore::MurmurHash GafferScene::SceneAlgo::matchingPathsHash( const PathMatcher &filter, const ScenePlug *scene )
{
	ThreadablePathHashAccumulator f;
	GafferScene::SceneAlgo::filteredParallelTraverse( scene, filter, f );
	return IECore::MurmurHash( f.m_h1Accum, f.m_h2Accum );
}

//////////////////////////////////////////////////////////////////////////
// Globals
//////////////////////////////////////////////////////////////////////////

IECore::ConstCompoundObjectPtr GafferScene::SceneAlgo::globalAttributes( const IECore::CompoundObject *globals )
{
	static const std::string prefix( "attribute:" );

	CompoundObjectPtr result = new CompoundObject;

	CompoundObject::ObjectMap::const_iterator it, eIt;
	for( it = globals->members().begin(), eIt = globals->members().end(); it != eIt; ++it )
	{
		if( !boost::starts_with( it->first.c_str(), "attribute:" ) )
		{
			continue;
		}
		// Cast is justified because we don't modify the data, and will return it
		// as const from this function.
		result->members()[it->first.string().substr( prefix.size() )] = boost::const_pointer_cast<Object>(
			it->second
		);
	}

	return result;
}

Imath::V2f GafferScene::SceneAlgo::shutter( const IECore::CompoundObject *globals, const ScenePlug *scene )
{
	const BoolData *transformBlurData = globals->member<BoolData>( "option:render:transformBlur" );
	const bool transformBlur = transformBlurData ? transformBlurData->readable() : false;

	const BoolData *deformationBlurData = globals->member<BoolData>( "option:render:deformationBlur" );
	const bool deformationBlur = deformationBlurData ? deformationBlurData->readable() : false;

	V2f shutter( Context::current()->getFrame() );
	if( transformBlur || deformationBlur )
	{
		ConstCameraPtr camera = nullptr;
		const StringData *cameraOption = globals->member<StringData>( "option:render:camera" );
		if( cameraOption && !cameraOption->readable().empty() )
		{
			ScenePlug::ScenePath cameraPath;
			ScenePlug::stringToPath( cameraOption->readable(), cameraPath );
			if( scene->exists( cameraPath ) )
			{
				camera = runTimeCast< const Camera>( scene->object( cameraPath ).get() );
			}
		}

		V2f relativeShutter;
		if( camera && camera->hasShutter() )
		{
			relativeShutter = camera->getShutter();
		}
		else
		{
			const V2fData *shutterData = globals->member<V2fData>( "option:render:shutter" );
			relativeShutter = shutterData ? shutterData->readable() : V2f( -0.25, 0.25 );
		}
		shutter += relativeShutter;
	}

	return shutter;
}

//////////////////////////////////////////////////////////////////////////
// Sets Algo
//////////////////////////////////////////////////////////////////////////

bool GafferScene::SceneAlgo::setExists( const ScenePlug *scene, const IECore::InternedString &setName )
{
	IECore::ConstInternedStringVectorDataPtr setNamesData = scene->setNamesPlug()->getValue();
	const std::vector<IECore::InternedString> &setNames = setNamesData->readable();
	return std::find( setNames.begin(), setNames.end(), setName ) != setNames.end();
}

IECore::ConstCompoundDataPtr GafferScene::SceneAlgo::sets( const ScenePlug *scene )
{
	ConstInternedStringVectorDataPtr setNamesData = scene->setNamesPlug()->getValue();
	return sets( scene, setNamesData->readable() );
}

IECore::ConstCompoundDataPtr GafferScene::SceneAlgo::sets( const ScenePlug *scene, const std::vector<IECore::InternedString> &setNames )
{
	std::vector<IECore::ConstPathMatcherDataPtr> setsVector;
	setsVector.resize( setNames.size(), nullptr );

	const ThreadState &threadState = ThreadState::current();

	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );
	parallel_for(

		tbb::blocked_range<size_t>( 0, setsVector.size() ),

		[scene, &setNames, &threadState, &setsVector]( const tbb::blocked_range<size_t> &r ) {

			ScenePlug::SetScope setScope( threadState );
			for( size_t i=r.begin(); i!=r.end(); ++i )
			{
				setScope.setSetName( setNames[i] );
				setsVector[i] = scene->setPlug()->getValue();
			}

		},

		taskGroupContext // Prevents outer tasks silently cancelling our tasks

	);

	CompoundDataPtr result = new CompoundData;
	for( size_t i = 0, e = setsVector.size(); i < e; ++i )
	{
		// The const_pointer_cast is ok because we're just using it to put the set into
		// a container that will be const on return - we never modify the set itself.
		result->writable()[setNames[i]] = boost::const_pointer_cast<PathMatcherData>( setsVector[i] );
	}
	return result;
}

//////////////////////////////////////////////////////////////////////////
// History
//////////////////////////////////////////////////////////////////////////

namespace
{

struct CapturedProcess
{

	typedef std::unique_ptr<CapturedProcess> Ptr;
	typedef vector<Ptr> PtrVector;

	InternedString type;
	ConstPlugPtr plug;
	ConstPlugPtr destinationPlug;
	ContextPtr context;

	PtrVector children;

};

/// \todo Perhaps add this to the Gaffer module as a
/// public class, and expose it within the stats app?
/// Give a bit more thought to the CapturedProcess
/// class if doing this.
class CapturingMonitor : public Monitor
{

	public :

		CapturingMonitor()
		{
		}

		~CapturingMonitor() override
		{
		}

		IE_CORE_DECLAREMEMBERPTR( CapturingMonitor )

		const CapturedProcess::PtrVector &rootProcesses()
		{
			return m_rootProcesses;
		}

	protected :

		void processStarted( const Process *process ) override
		{
			CapturedProcess::Ptr capturedProcess( new CapturedProcess );
			capturedProcess->type = process->type();
			capturedProcess->plug = process->plug();
			capturedProcess->destinationPlug = process->destinationPlug();
			capturedProcess->context = new Context( *process->context(), /* omitCanceller = */ true );

			Mutex::scoped_lock lock( m_mutex );

			m_processMap[process] = capturedProcess.get();

			ProcessMap::const_iterator it = m_processMap.find( process->parent() );
			if( it != m_processMap.end() )
			{
				it->second->children.push_back( std::move( capturedProcess ) );
			}
			else
			{
				// Either `process->parent()` was null, or was started
				// before we were made active via `Monitor::Scope`.
				m_rootProcesses.push_back( std::move( capturedProcess ) );
			}
		}

		void processFinished( const Process *process ) override
		{
			Mutex::scoped_lock lock( m_mutex );
			m_processMap.erase( process );
		}

	private :

		typedef tbb::spin_mutex Mutex;

		Mutex m_mutex;
		typedef boost::unordered_map<const Process *, CapturedProcess *> ProcessMap;
		ProcessMap m_processMap;
		CapturedProcess::PtrVector m_rootProcesses;

};

IE_CORE_DECLAREPTR( CapturingMonitor )

uint64_t g_historyID = 0;

SceneAlgo::History::Ptr historyWalk( const CapturedProcess *process, InternedString scenePlugChildName, SceneAlgo::History *parent )
{
	// Add a history item for each plug in the input chain
	// between `process->destinationPlug()` and `process->plug()`
	// (inclusive of each).

	SceneAlgo::History::Ptr result;
	Plug *plug = const_cast<Plug *>( process->destinationPlug.get() );
	while( plug )
	{
		ScenePlug *scene = plug->parent<ScenePlug>();
		if( scene && plug == scene->getChild( scenePlugChildName ) )
		{
			ContextPtr cleanContext = new Context( *process->context );
			cleanContext->remove( SceneAlgo::historyIDContextName() );
			SceneAlgo::History::Ptr history = new SceneAlgo::History( scene, cleanContext );
			if( !result )
			{
				result = history;
			};
			if( parent )
			{
				parent->predecessors.push_back( history );
			}
			parent = history.get();
		}
		plug = plug != process->plug ? plug->getInput() : nullptr;
	}

	// Add history items for upstream processes.

	for( const auto &p : process->children )
	{
		// Parents may spawn other processes in support of the requested plug.
		// We don't want these to show up in history output, so we only include
		// ones that are directly in service of the requested plug.
		if( p->plug->parent<ScenePlug>() && p->plug->getName() == scenePlugChildName )
		{
			historyWalk( p.get(), scenePlugChildName, parent );
		}
	}

	return result;
}

void addGenericAttributePredecessors( const SceneAlgo::History::Predecessors &source, SceneAlgo::AttributeHistory *destination )
{
	for( auto &h : source )
	{
		if( auto ah = SceneAlgo::attributeHistory( h.get(), destination->attributeName ) )
		{
			destination->predecessors.push_back( ah );
		}
	}
}

void addCopyAttributesPredecessors( const CopyAttributes *copyAttributes, const SceneAlgo::History::Predecessors &source, SceneAlgo::AttributeHistory *destination )
{
	const ScenePlug *sourceScene = copyAttributes->inPlug();
	if(
		( copyAttributes->filterPlug()->match( copyAttributes->inPlug() ) & PathMatcher::ExactMatch ) &&
		StringAlgo::matchMultiple( destination->attributeName, copyAttributes->attributesPlug()->getValue() )
	)
	{
		ConstCompoundObjectPtr sourceAttributes;
		const std::string sourceLocation = copyAttributes->sourceLocationPlug()->getValue();
		if( sourceLocation.empty() )
		{
			if( copyAttributes->sourcePlug()->exists() )
			{
				sourceAttributes = copyAttributes->sourcePlug()->attributesPlug()->getValue();
			}
		}
		else
		{
			ScenePlug::ScenePath sourcePath; ScenePlug::stringToPath( sourceLocation, sourcePath );
			if( copyAttributes->sourcePlug()->exists( sourcePath ) )
			{
				sourceAttributes = copyAttributes->sourcePlug()->attributes( sourcePath );
			}
		}
		if( sourceAttributes && sourceAttributes->members().count( destination->attributeName ) )
		{
			sourceScene = copyAttributes->sourcePlug();
		}
	}

	for( auto &h : source )
	{
		if( h->scene == sourceScene )
		{
			destination->predecessors.push_back( SceneAlgo::attributeHistory( h.get(), destination->attributeName ) );
		}
	}
}

void addShuffleAttributesPredecessors( const ShuffleAttributes *shuffleAttributes, const SceneAlgo::History::Predecessors &source, SceneAlgo::AttributeHistory *destination )
{
	// We have no way of introspecting the operation of a ShufflePlug, so we resort
	// to shuffling	`name = name, value = name` pairs to figure out where the attribute
	// has come from.

	InternedString sourceAttributeName = destination->attributeName;
	if( shuffleAttributes->filterPlug()->match( shuffleAttributes->inPlug() ) & PathMatcher::ExactMatch )
	{
		auto inputAttributes = shuffleAttributes->inPlug()->attributesPlug()->getValue();
		map<InternedString, InternedString> shuffledNames;
		for( auto &a : inputAttributes->members() )
		{
			shuffledNames.insert( { a.first, a.first } );
		}
		shuffledNames = shuffleAttributes->shufflesPlug()->shuffle( shuffledNames );
		sourceAttributeName = shuffledNames[destination->attributeName];
	}

	assert( source.size() == 1 );
	destination->predecessors.push_back( SceneAlgo::attributeHistory( source[0].get(), sourceAttributeName ) );
}

void addLocaliseAttributesPredecessors( const LocaliseAttributes *localiseAttributes, const SceneAlgo::History::Predecessors &source, SceneAlgo::AttributeHistory *destination )
{
	// No need to check if the node is filtered to this location.
	// Filtered or unfiltered, it's all the same : the predecessor
	// we want is the most local one. i.e. the one with the longest
	// path.

	int longestPath = -1;
	SceneAlgo::AttributeHistory::Ptr predecessor;
	for( auto &h : source )
	{
		const auto &sourcePath = h->context->get<ScenePlug::ScenePath>( ScenePlug::scenePathContextName );
		if( (int)sourcePath.size() <= longestPath )
		{
			continue;
		}
		if( auto p = attributeHistory( h.get(), destination->attributeName ) )
		{
			predecessor = p;
			longestPath = sourcePath.size();
		}
	}

	assert( predecessor );
	destination->predecessors.push_back( predecessor );
}

void addMergeScenesPredecessors( const MergeScenes *mergeScenes, const SceneAlgo::History::Predecessors &source, SceneAlgo::AttributeHistory *destination )
{
	// MergeScenes only evaluates input locations that exist, and in an order
	// whereby the last input with the attribute wins.

	SceneAlgo::AttributeHistory::Ptr predecessor;
	for( auto &h : source )
	{
		if( auto p = attributeHistory( h.get(), destination->attributeName ) )
		{
			predecessor = p;
		}
	}

	assert( predecessor );
	destination->predecessors.push_back( predecessor );
}

SceneProcessor *objectTweaksWalk( const SceneAlgo::History *h )
{
	if( auto tweaks = h->scene->parent<CameraTweaks>() )
	{
		if( h->scene == tweaks->outPlug() )
		{
			Context::Scope contextScope( h->context.get() );
			if( tweaks->filterPlug()->match( tweaks->inPlug() ) & PathMatcher::ExactMatch )
			{
				return tweaks;
			}
		}
	}

	for( const auto &p : h->predecessors )
	{
		if( auto tweaks = objectTweaksWalk( p.get() ) )
		{
			return tweaks;
		}
	}

	return nullptr;
}

ShaderTweaks *shaderTweaksWalk( const SceneAlgo::AttributeHistory *h )
{
	if( auto tweaks = h->scene->parent<ShaderTweaks>() )
	{
		if( h->scene == tweaks->outPlug() )
		{
			Context::Scope contextScope( h->context.get() );
			if(
				StringAlgo::matchMultiple( h->attributeName, tweaks->shaderPlug()->getValue() ) &&
				( tweaks->filterPlug()->match( tweaks->inPlug() ) & PathMatcher::ExactMatch )
			)
			{
				return tweaks;
			}
		}
	}

	for( const auto &p : h->predecessors )
	{
		if( auto tweaks = shaderTweaksWalk( static_cast<SceneAlgo::AttributeHistory *>( p.get() ) ) )
		{
			return tweaks;
		}
	}

	return nullptr;
}

} // namespace

InternedString SceneAlgo::historyIDContextName()
{
	static InternedString s( "__sceneAlgoHistory:id" );
	return s;
}

SceneAlgo::History::Ptr SceneAlgo::history( const Gaffer::ValuePlug *scenePlugChild, const ScenePlug::ScenePath &path )
{
	if( !scenePlugChild->parent<ScenePlug>() )
	{
		throw IECore::Exception( boost::str(
			boost::format( "Plug \"%1%\" is not a child of a ScenePlug." ) % scenePlugChild->fullName()
		) );
	}

	CapturingMonitorPtr monitor = new CapturingMonitor;
	{
		ScenePlug::PathScope pathScope( Context::current(), path );
		// Trick to bypass the hash cache and get a full upstream evaluation.
		pathScope.set( historyIDContextName(), g_historyID++ );
		Monitor::Scope monitorScope( monitor );
		scenePlugChild->hash();
	}

	if( monitor->rootProcesses().size() == 0 )
	{
		return new History(
			const_cast<ScenePlug *>( scenePlugChild->parent<ScenePlug>() ),
			new Context( *Context::current(), /* omitCanceller = */ true )
		);
	}

	assert( monitor->rootProcesses().size() == 1 );
	return historyWalk( monitor->rootProcesses().front().get(), scenePlugChild->getName(), nullptr );
}

SceneAlgo::AttributeHistory::Ptr SceneAlgo::attributeHistory( const SceneAlgo::History *attributesHistory, const IECore::InternedString &attribute )
{
	Context::Scope scopedContext( attributesHistory->context.get() );
	ConstCompoundObjectPtr attributes = attributesHistory->scene->attributesPlug()->getValue();
	ConstObjectPtr attributeValue = attributes->member<Object>( attribute );

	if( !attributeValue )
	{
		return nullptr;
	}

	SceneAlgo::AttributeHistory::Ptr result = new AttributeHistory(
		attributesHistory->scene, attributesHistory->context,
		attribute, attributeValue
	);

	// Filter the _attributes_ history to include only predecessors which
	// contribute specifically to our single _attribute_. In the absence of
	// a SceneNode-level API for querying attribute sources, we resort to
	// special case code for backtracking through certain node types.
	/// \todo Consider an official API that allows the nodes themselves to
	/// take responsibility for this backtracking.

	auto node = runTimeCast<const SceneNode>( attributesHistory->scene->node() );
	if( node && node->enabledPlug()->getValue() && attributesHistory->scene == node->outPlug() )
	{
		if( auto copyAttributes = runTimeCast<const CopyAttributes>( node ) )
		{
			addCopyAttributesPredecessors( copyAttributes, attributesHistory->predecessors, result.get() );
		}
		else if( auto shuffleAttributes = runTimeCast<const ShuffleAttributes>( node ) )
		{
			addShuffleAttributesPredecessors( shuffleAttributes, attributesHistory->predecessors, result.get() );
		}
		else if( auto localiseAttributes = runTimeCast<const LocaliseAttributes>( node ) )
		{
			addLocaliseAttributesPredecessors( localiseAttributes, attributesHistory->predecessors, result.get() );
		}
		else if( auto mergeScenes = runTimeCast<const MergeScenes>( node ) )
		{
			addMergeScenesPredecessors( mergeScenes, attributesHistory->predecessors, result.get() );
		}
		else
		{
			addGenericAttributePredecessors( attributesHistory->predecessors, result.get() );
		}
	}
	else
	{
		addGenericAttributePredecessors( attributesHistory->predecessors, result.get() );
	}

	return result;
}

ScenePlug *SceneAlgo::source( const ScenePlug *scene, const ScenePlug::ScenePath &path )
{
	History::ConstPtr h = history( scene->objectPlug(), path );
	if( h )
	{
		const History *c = h.get();
		while( c )
		{
			if( c->predecessors.empty() )
			{
				return c->scene.get();
			}
			else
			{
				c = c->predecessors.front().get();
			}
		}
	}
	return nullptr;
}

SceneProcessor *SceneAlgo::objectTweaks( const ScenePlug *scene, const ScenePlug::ScenePath &path )
{
	History::ConstPtr h = history( scene->objectPlug(), path );
	if( h )
	{
		return objectTweaksWalk( h.get() );
	}
	return nullptr;
}

ShaderTweaks *SceneAlgo::shaderTweaks( const ScenePlug *scene, const ScenePlug::ScenePath &path, const IECore::InternedString &attributeName )
{
	ScenePlug::ScenePath inheritancePath = path;
	while( inheritancePath.size() )
	{
		History::ConstPtr h = history( scene->attributesPlug(), inheritancePath );
		if( auto ah = attributeHistory( h.get(), attributeName ) )
		{
			return shaderTweaksWalk( ah.get() );
		}
		inheritancePath.pop_back();
	}
	return nullptr;
}

std::string SceneAlgo::sourceSceneName( const GafferImage::ImagePlug *image )
{
	if( !image )
	{
		return "";
	}

	// See if the image has the `gaffer:sourceScene` metadata entry that gives
	// the root-relative path to the source scene plug
	const ConstCompoundDataPtr metadata = image->metadata();
	const StringData *plugPathData = metadata->member<StringData>( "gaffer:sourceScene" );

	return plugPathData ? plugPathData->readable() : "";
}

ScenePlug *SceneAlgo::sourceScene( GafferImage::ImagePlug *image )
{
	const std::string path = sourceSceneName( image );
	if( path.empty() )
	{
		return nullptr;
	}

	ScriptNode *scriptNode = image->source()->node()->scriptNode();
	if( !scriptNode )
	{
		return nullptr;
	}

	return scriptNode->descendant<ScenePlug>( path );
}

//////////////////////////////////////////////////////////////////////////
// Light linking
//////////////////////////////////////////////////////////////////////////

namespace
{

static InternedString g_lights( "__lights" );
static InternedString g_linkedLights( "linkedLights" );

template<typename AttributesPredicate>
struct AttributesFinder
{

	AttributesFinder( const AttributesPredicate &predicate, tbb::spin_mutex &resultMutex, IECore::PathMatcher &result )
		:	m_predicate( predicate ), m_resultMutex( resultMutex ), m_result( result )
	{
	}

	bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &path )
	{
		bool inheritPredicateResult = false;
		ConstCompoundObjectPtr attributes = scene->attributesPlug()->getValue();
		if( path.empty() )
		{
			// Root
			m_fullAttributes = attributes;
		}
		else
		{
			if( attributes->members().empty() )
			{
				inheritPredicateResult = true;
			}
			else
			{
				CompoundObjectPtr fullAttributes = new CompoundObject;
				fullAttributes->members() = m_fullAttributes->members();
				for( const auto &a : attributes->members() )
				{
					fullAttributes->members()[a.first] = a.second;
				}
				m_fullAttributes = fullAttributes;
			}
		}

		if( !inheritPredicateResult )
		{
			m_predicateResult = m_predicate( m_fullAttributes.get() );
		}
		else
		{
			// `m_predicateResult` is inherited automatically because `parallelProcessLocations()`
			// copy-constructs child functors from the parent.
		}

		if( m_predicateResult && !path.empty() )
		{
			/// \todo We could avoid this locking if we added a `functor.gatherChildren()`
			/// phase to `parallelProcessLocations()` and built the result recursively.
			tbb::spin_mutex::scoped_lock lock( m_resultMutex );
			m_result.addPath( path );
		}

		return true;
	}

	private :

		const AttributesPredicate &m_predicate;

		ConstCompoundObjectPtr m_fullAttributes;
		bool m_predicateResult;

		tbb::spin_mutex &m_resultMutex;
		IECore::PathMatcher &m_result;

};

/// \todo Perhaps this is worthy of inclusion in the public API?
template<typename AttributesPredicate>
IECore::PathMatcher findAttributes( const ScenePlug *scene, const AttributesPredicate &predicate )
{
	tbb::spin_mutex resultMutex;
	IECore::PathMatcher result;
	AttributesFinder<AttributesPredicate> attributesFinder( predicate, resultMutex, result );
	SceneAlgo::parallelProcessLocations( scene, attributesFinder );
	return result;
}

} // namespace

IECore::PathMatcher GafferScene::SceneAlgo::linkedObjects( const ScenePlug *scene, const ScenePlug::ScenePath &light )
{
	PathMatcher lights;
	lights.addPath( light );
	return linkedObjects( scene, lights );
}

GAFFERSCENE_API IECore::PathMatcher GafferScene::SceneAlgo::linkedObjects( const ScenePlug *scene, const IECore::PathMatcher &lights )
{
	// We expect many locations to have the exact same expression for `linkedLights`,
	// and evaluating the expression is fairly expensive. So we cache the results for
	// sharing between locations. The cache only lives for the lifetime of this query.
	using QueryCache = IECorePreview::LRUCache<std::string, bool, IECorePreview::LRUCachePolicy::TaskParallel>;
	const Context *context = Context::current();
	QueryCache queryCache(
		[&lights, scene, context]( const std::string &setExpression, size_t &cost )
		{
			cost = 1;
			Context::Scope scopedContext( context );
			const IECore::PathMatcher linkedLights = SetAlgo::evaluateSetExpression( setExpression, scene );
			for( PathMatcher::Iterator lightIt = lights.begin(), eIt = lights.end(); lightIt != eIt; ++lightIt )
			{
				if( linkedLights.match( *lightIt ) & PathMatcher::ExactMatch )
				{
					return true;
				}
			}
			return false;
		},
		10000
	);

	IECore::PathMatcher result = findAttributes(
		scene,
		[&queryCache] ( const CompoundObject *fullAttributes ) {
			auto *linkedLights = fullAttributes->member<StringData>( g_linkedLights );
			return queryCache.get( linkedLights ? linkedLights->readable() : "defaultLights" );
		}
	);

	result.removePaths( scene->set( g_lights )->readable() );
	return result;
}

IECore::PathMatcher GafferScene::SceneAlgo::linkedLights( const ScenePlug *scene, const ScenePlug::ScenePath &object )
{
	IECore::ConstCompoundObjectPtr attributes = scene->fullAttributes( object );
	auto *linkedLightsAttribute = attributes->member<StringData>( g_linkedLights );
	const string linkedLights = linkedLightsAttribute ? linkedLightsAttribute->readable() : "defaultLights";
	IECore::PathMatcher linkedPaths = SetAlgo::evaluateSetExpression( linkedLights, scene );
	return linkedPaths.intersection( scene->set( g_lights )->readable() );
}

IECore::PathMatcher GafferScene::SceneAlgo::linkedLights( const ScenePlug *scene, const IECore::PathMatcher &objects )
{
	tbb::spin_mutex resultMutex;
	IECore::PathMatcher result;
	tbb::concurrent_unordered_set<std::string> processed;

	auto functor = [&resultMutex, &result, &processed] ( const ScenePlug *scene, const ScenePlug::ScenePath &path ) {
		IECore::ConstCompoundObjectPtr attributes = scene->fullAttributes( path );
		auto *linkedLightsAttribute = attributes->member<StringData>( g_linkedLights );
		const string linkedLights = linkedLightsAttribute ? linkedLightsAttribute->readable() : "defaultLights";
		if( processed.insert( linkedLights ).second )
		{
			ScenePlug::GlobalScope globalScope( Context::current() );
			IECore::PathMatcher linkedPaths = SetAlgo::evaluateSetExpression( linkedLights, scene );
			tbb::spin_mutex::scoped_lock resultLock( resultMutex );
			result.addPaths( linkedPaths );
		}
		return true;
	};

	filteredParallelTraverse( scene, objects, functor );
	return result.intersection( scene->set( g_lights )->readable() );
}

//////////////////////////////////////////////////////////////////////////
// Miscellaneous
//////////////////////////////////////////////////////////////////////////

bool GafferScene::SceneAlgo::exists( const ScenePlug *scene, const ScenePlug::ScenePath &path )
{
	return scene->exists( path );
}

bool GafferScene::SceneAlgo::visible( const ScenePlug *scene, const ScenePlug::ScenePath &path )
{
	ScenePlug::PathScope pathScope( Context::current() );

	ScenePlug::ScenePath p; p.reserve( path.size() );
	for( ScenePlug::ScenePath::const_iterator it = path.begin(), eIt = path.end(); it != eIt; ++it )
	{
		p.push_back( *it );
		pathScope.setPath( p );

		ConstCompoundObjectPtr attributes = scene->attributesPlug()->getValue();
		const BoolData *visibilityData = attributes->member<BoolData>( "scene:visible" );
		if( visibilityData && !visibilityData->readable() )
		{
			return false;
		}
	}

	return true;
}

Imath::Box3f GafferScene::SceneAlgo::bound( const IECore::Object *object )
{
	if( const IECoreScene::VisibleRenderable *renderable = IECore::runTimeCast<const IECoreScene::VisibleRenderable>( object ) )
	{
		return renderable->bound();
	}
	else if( object->isInstanceOf( IECoreScene::Camera::staticTypeId() ) )
	{
		return Imath::Box3f( Imath::V3f( -0.5, -0.5, 0 ), Imath::V3f( 0.5, 0.5, 2.0 ) );
	}
	else if( object->isInstanceOf( IECoreScene::CoordinateSystem::staticTypeId() ) )
	{
		return Imath::Box3f( Imath::V3f( 0 ), Imath::V3f( 1 ) );
	}
	else if( object->isInstanceOf( IECoreScene::ClippingPlane::staticTypeId() ) )
	{
		return Imath::Box3f( Imath::V3f( -0.5, -0.5, 0 ), Imath::V3f( 0.5 ) );
	}
	else if( !object->isInstanceOf( IECore::NullObject::staticTypeId() ) )
	{
		return Imath::Box3f( Imath::V3f( -0.5 ), Imath::V3f( 0.5 ) );
	}
	else
	{
		return Imath::Box3f();
	}
}
