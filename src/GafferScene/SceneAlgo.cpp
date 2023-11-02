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

#include "GafferScene/AttributeTweaks.h"
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

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/Monitor.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"
#include "Gaffer/Process.h"
#include "Gaffer/ScriptNode.h"

#include "IECoreScene/Camera.h"
#include "IECoreScene/ClippingPlane.h"
#include "IECoreScene/CoordinateSystem.h"
#include "IECoreScene/VisibleRenderable.h"

#include "IECore/MessageHandler.h"
#include "IECore/NullObject.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/unordered_map.hpp"

#include "tbb/concurrent_unordered_set.h"
#include "tbb/enumerable_thread_specific.h"
#include "tbb/parallel_for.h"
#include "tbb/spin_mutex.h"

#include "fmt/format.h"

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

	bool operator()( const GafferScene::ScenePlug *scene, const GafferScene::ScenePlug::ScenePath &path )
	{
		m_threadResults.local().addPath( path );
		return true;
	}

	IECore::PathMatcher result()
	{
		return m_threadResults.combine(
			[] ( const PathMatcher &a, const PathMatcher &b ) {
				PathMatcher c = a;
				c.addPaths( b );
				return c;
			}
		);
	}

	private :

		tbb::enumerable_thread_specific<PathMatcher> m_threadResults;

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

IECore::InternedString g_hashProcessType( ValuePlug::hashProcessType() );
IECore::InternedString g_computeProcessType( ValuePlug::computeProcessType() );

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
	ThreadablePathAccumulator f;
	GafferScene::SceneAlgo::filteredParallelTraverse( scene, filterPlug, f );
	paths = f.result();
}

void GafferScene::SceneAlgo::matchingPaths( const FilterPlug *filterPlug, const ScenePlug *scene, const ScenePlug::ScenePath &root, IECore::PathMatcher &paths )
{
	ThreadablePathAccumulator f;
	GafferScene::SceneAlgo::filteredParallelTraverse( scene, filterPlug, f, root );
	paths = f.result();
}

void GafferScene::SceneAlgo::matchingPaths( const PathMatcher &filter, const ScenePlug *scene, PathMatcher &paths )
{
	ThreadablePathAccumulator f;
	GafferScene::SceneAlgo::filteredParallelTraverse( scene, filter, f );
	paths = f.result();
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
// Searching
//////////////////////////////////////////////////////////////////////////

IECore::PathMatcher GafferScene::SceneAlgo::findAllWithAttribute( const ScenePlug *scene, IECore::InternedString name, const IECore::Object *value, const ScenePlug::ScenePath &root )
{
	return findAll(
		scene,
		[&] ( const ScenePlug *scene, const ScenePlug::ScenePath &path ) {
			ConstCompoundObjectPtr attributes = scene->attributesPlug()->getValue();
			if( const Object *attribute = attributes->member<Object>( name ) )
			{
				return !value || attribute->isEqualTo( value );
			}
			return false;
		},
		root
	);
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
				setScope.setSetName( &setNames[i] );
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

	using Ptr = std::unique_ptr<CapturedProcess>;
	using PtrVector = vector<Ptr>;

	InternedString type;
	ConstPlugPtr plug;
	ConstPlugPtr destinationPlug;
	ContextPtr context;

	PtrVector children;

};

const InternedString g_processedObjectPlugName( "__processedObject" );

/// \todo Perhaps add this to the Gaffer module as a
/// public class, and expose it within the stats app?
/// Give a bit more thought to the CapturedProcess
/// class if doing this.
class CapturingMonitor : public Monitor
{

	public :

		CapturingMonitor( IECore::InternedString scenePlugChildName ) : m_scenePlugChildName( scenePlugChildName )
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
			const Plug *p = process->plug();

			CapturedProcess::Ptr capturedProcess;
			ProcessOrScope entry;
			if( !shouldCapture( p ) )
			{
				// Parents may spawn other processes in support of the requested plug. This is one
				// of these other plugs that isn't directly the requested plug.  Instead of creating
				// a CapturedProcess record, we instead create a Monitor::Scope that turns off this
				// monitor, so that the child computations that we don't need to monitor can go faster.
				//
				// It's crucial that this Scope gets destructed while leaving this process, so that the
				// order of the stack is preserved - if this happens out of order, the stack will be
				// corrupted, and weird crashes will happen.  But as long as it is created in
				// processStarted, and released in processFinished, everything should line up.
				entry = std::make_unique<Monitor::Scope>( this, false );
			}
			else
			{
				capturedProcess = std::make_unique<CapturedProcess>();
				capturedProcess->type = process->type();
				capturedProcess->plug = p;
				capturedProcess->destinationPlug = process->destinationPlug();
				capturedProcess->context = new Context( *process->context(), /* omitCanceller = */ true );
				entry = capturedProcess.get();
			}

			Mutex::scoped_lock lock( m_mutex );
			m_processMap[process] = std::move( entry );

			if( capturedProcess )
			{
				ProcessMap::const_iterator it = m_processMap.find( process->parent() );
				if( it != m_processMap.end() )
				{
					CapturedProcess * const * parent = boost::get< CapturedProcess* >( &it->second );
					if( parent && *parent )
					{
						(*parent)->children.push_back( std::move( capturedProcess ) );
					}
				}
				else
				{
					// Either `process->parent()` was null, or was started
					// before we were made active via `Monitor::Scope`.
					m_rootProcesses.push_back( std::move( capturedProcess ) );
				}
			}
		}

		void processFinished( const Process *process ) override
		{
			Mutex::scoped_lock lock( m_mutex );
			m_processMap.erase( process );
		}

		bool mightForceMonitoring() override
		{
			return true;
		}

		bool forceMonitoring( const Plug *plug, const IECore::InternedString &processType ) override
		{
			if( processType == g_hashProcessType && shouldCapture( plug ) )
			{
				return true;
			}

			return false;
		}

	private :

		bool shouldCapture( const Plug *plug ) const
		{
			return
				( plug->parent<ScenePlug>() && plug->getName() == m_scenePlugChildName ) ||
				( (Gaffer::TypeId)plug->typeId() == Gaffer::TypeId::ObjectPlugTypeId && plug->getName() == g_processedObjectPlugName )
			;
		}

		using Mutex = tbb::spin_mutex;

		Mutex m_mutex;

		using ProcessOrScope = boost::variant<CapturedProcess *, std::unique_ptr< Monitor::Scope>>;
		using ProcessMap = boost::unordered_map<const Process *, ProcessOrScope>;

		ProcessMap m_processMap;
		CapturedProcess::PtrVector m_rootProcesses;
		IECore::InternedString m_scenePlugChildName;

};

IE_CORE_DECLAREPTR( CapturingMonitor )

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
			SceneAlgo::History::Ptr history = new SceneAlgo::History( scene, process->context );
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
		historyWalk( p.get(), scenePlugChildName, parent );
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

void addLocaliseAttributesPredecessors( const SceneAlgo::History::Predecessors &source, SceneAlgo::AttributeHistory *destination )
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

	if( !predecessor )
	{
		return;
	}

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

SceneAlgo::History::Ptr SceneAlgo::history( const Gaffer::ValuePlug *scenePlugChild, const ScenePlug::ScenePath &path )
{
	if( !scenePlugChild->parent<ScenePlug>() )
	{
		throw IECore::Exception(
			fmt::format( "Plug \"{}\" is not a child of a ScenePlug.", scenePlugChild->fullName() )
		);
	}

	CapturingMonitorPtr monitor = new CapturingMonitor( scenePlugChild->getName() );
	{
		ScenePlug::PathScope pathScope( Context::current(), &path );
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
		else if( runTimeCast<const LocaliseAttributes>( node ) )
		{
			addLocaliseAttributesPredecessors( attributesHistory->predecessors, result.get() );
		}
		else if( auto mergeScenes = runTimeCast<const MergeScenes>( node ) )
		{
			addMergeScenesPredecessors( mergeScenes, attributesHistory->predecessors, result.get() );
		}
		else if( runTimeCast<const AttributeTweaks>( node ) )
		{
			addLocaliseAttributesPredecessors( attributesHistory->predecessors, result.get() );
		}
		else if( runTimeCast<const ShaderTweaks>( node ) )
		{
			addLocaliseAttributesPredecessors( attributesHistory->predecessors, result.get() );
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

	ConstStringVectorDataPtr views = image->viewNames();

	for( const std::string &view : views->readable() )
	{
		GafferImage::ImagePlug::ViewScope viewScope( Context::current() );
		viewScope.setViewName( &view );
		ConstCompoundDataPtr metadata = image->metadata();
		const StringData *plugPathData = metadata->member<StringData>( "gaffer:sourceScene" );
		if( plugPathData )
		{
			return plugPathData->readable();
		}
	}

	return "";
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

InternedString g_lights( "__lights" );
InternedString g_linkedLights( "linkedLights" );

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
		[&lights, scene, context]( const std::string &setExpression, size_t &cost, const IECore::Canceller *canceller )
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
		pathScope.setPath( &p );

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

namespace
{

const InternedString g_emptyInternedString;
const InternedString g_ellipsisInternedString( "..." );
const InternedString g_parentInternedString( ".." );

} // namespace

void GafferScene::SceneAlgo::validateName( IECore::InternedString name )
{
	const char *invalidReason = nullptr;
	if( name == g_emptyInternedString )
	{
		invalidReason = "it is empty";
	}
	else if( name == g_ellipsisInternedString )
	{
		invalidReason = "`...` is a filter wildcard";
	}
	else if( name == g_parentInternedString )
	{
		invalidReason = "`..` denotes the parent location";
	}
	else if( name.string().find( '/' ) != string::npos )
	{
		invalidReason = "`/` is the path separator";
	}
	else if( StringAlgo::hasWildcards( name.string() ) )
	{
		invalidReason = "it contains filter wildcards";
	}

	if( invalidReason )
	{
		throw IECore::Exception(
			fmt::format( "Name `{}` is invalid (because {})", name.string(), invalidReason )
		);
	}
}

//////////////////////////////////////////////////////////////////////////
// Render Adaptor Registry
//////////////////////////////////////////////////////////////////////////

namespace
{

using RenderAdaptors = boost::container::flat_map<string, SceneAlgo::RenderAdaptor>;

RenderAdaptors &renderAdaptors()
{
	static RenderAdaptors a;
	return a;
}

}

void GafferScene::SceneAlgo::registerRenderAdaptor( const std::string &name, SceneAlgo::RenderAdaptor adaptor )
{
	renderAdaptors()[name] = adaptor;
}

void GafferScene::SceneAlgo::deregisterRenderAdaptor( const std::string &name )
{
	renderAdaptors().erase( name );
}

SceneProcessorPtr GafferScene::SceneAlgo::createRenderAdaptors()
{
	SceneProcessorPtr result = new SceneProcessor;

	ScenePlug *in = result->inPlug();

	const RenderAdaptors &a = renderAdaptors();
	for( RenderAdaptors::const_iterator it = a.begin(), eIt = a.end(); it != eIt; ++it )
	{
		SceneProcessorPtr adaptor = it->second();
		if( adaptor )
		{
			result->addChild( adaptor );
			adaptor->inPlug()->setInput( in );
			in = adaptor->outPlug();
		}
		else
		{
			IECore::msg(
				IECore::Msg::Warning, "SceneAlgo::createRenderAdaptors",
				fmt::format( "Adaptor \"{}\" returned null", it->first )
			);
		}
	}

	result->outPlug()->setInput( in );
	return result;
}

//////////////////////////////////////////////////////////////////////////
// Apply Camera Globals
//////////////////////////////////////////////////////////////////////////

void GafferScene::SceneAlgo::applyCameraGlobals( IECoreScene::Camera *camera, const IECore::CompoundObject *globals, const ScenePlug *scene )
{
	// Set any camera-relevant render globals that haven't been overridden on the camera
	const IntData *filmFitData = globals->member<IntData>( "option:render:filmFit" );
	if( !camera->hasFilmFit() && filmFitData )
	{
		camera->setFilmFit( (IECoreScene::Camera::FilmFit)filmFitData->readable() );
	}

	const V2iData *resolutionData = globals->member<V2iData>( "option:render:resolution" );
	if( !camera->hasResolution() && resolutionData )
	{
		camera->setResolution( resolutionData->readable() );
	}

	const FloatData *resolutionMultiplierData = globals->member<FloatData>( "option:render:resolutionMultiplier" );
	if( !camera->hasResolutionMultiplier() && resolutionMultiplierData )
	{
		camera->setResolutionMultiplier( resolutionMultiplierData->readable() );
	}

	const FloatData *pixelAspectRatioData = globals->member<FloatData>( "option:render:pixelAspectRatio" );
	if( !camera->hasPixelAspectRatio() && pixelAspectRatioData )
	{
		camera->setPixelAspectRatio( pixelAspectRatioData->readable() );
	}

	const BoolData *overscanData = globals->member<BoolData>( "option:render:overscan" );
	bool overscan = overscanData && overscanData->readable();
	if( camera->hasOverscan() ) overscan = camera->getOverscan();
	if( overscan )
	{
		if( !camera->hasOverscan() )
		{
			camera->setOverscan( true );
		}
		const FloatData *overscanLeftData = globals->member<FloatData>( "option:render:overscanLeft" );
		if( !camera->hasOverscanLeft() && overscanLeftData )
		{
			camera->setOverscanLeft( overscanLeftData->readable() );
		}
		const FloatData *overscanRightData = globals->member<FloatData>( "option:render:overscanRight" );
		if( !camera->hasOverscanRight() && overscanRightData )
		{
			camera->setOverscanRight( overscanRightData->readable() );
		}
		const FloatData *overscanTopData = globals->member<FloatData>( "option:render:overscanTop" );
		if( !camera->hasOverscanTop() && overscanTopData )
		{
			camera->setOverscanTop( overscanTopData->readable() );
		}
		const FloatData *overscanBottomData = globals->member<FloatData>( "option:render:overscanBottom" );
		if( !camera->hasOverscanBottom() && overscanBottomData )
		{
			camera->setOverscanBottom( overscanBottomData->readable() );
		}
	}

	const Box2fData *cropWindowData = globals->member<Box2fData>( "option:render:cropWindow" );
	if( !camera->hasCropWindow() && cropWindowData )
	{
		camera->setCropWindow( cropWindowData->readable() );
	}

	const BoolData *depthOfFieldData = globals->member<BoolData>( "option:render:depthOfField" );
	/*if( !camera->hasDepthOfField() && depthOfFieldData )
	{
		camera->setDepthOfField( depthOfFieldData->readable() );
	}*/
	// \todo - switch to the form above once we have officially added the depthOfField parameter to Cortex.
	// The plan then would be that the renderer backends should respect camera->getDepthOfField.
	// For the moment we bake into fStop instead
	bool depthOfField = false;
	if( depthOfFieldData )
	{
		// First set from render globals
		depthOfField = depthOfFieldData->readable();
	}
	if( const BoolData *d = camera->parametersData()->member<BoolData>( "depthOfField" ) )
	{
		// Override based on camera setting
		depthOfField = d->readable();
	}
	if( !depthOfField )
	{
		// If there is no depth of field, bake that into the fStop
		camera->setFStop( 0.0f );
	}

	// Bake the shutter from the globals into the camera before passing it to the renderer backend
	//
	// Before this bake, the shutter is an optional render setting override, with the shutter start
	// and end relative to the current frame.  After baking, the shutter is currently an absolute
	// shutter, with the frame added on.  Feels like it might be more consistent if we switched to
	// always storing a relative shutter in camera->setShutter()
	camera->setShutter( SceneAlgo::shutter( globals, scene ) );
}
