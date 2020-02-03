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
#include "GafferScene/Filter.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/ShaderTweaks.h"

#include "Gaffer/Context.h"
#include "Gaffer/Monitor.h"
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

#include "tbb/parallel_for.h"
#include "tbb/spin_mutex.h"
#include "tbb/task.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

bool GafferScene::SceneAlgo::exists( const ScenePlug *scene, const ScenePlug::ScenePath &path )
{
	ScenePlug::PathScope pathScope( Context::current() );

	ScenePlug::ScenePath p; p.reserve( path.size() );
	for( ScenePlug::ScenePath::const_iterator it = path.begin(), eIt = path.end(); it != eIt; ++it )
	{
		pathScope.setPath( p );
		ConstInternedStringVectorDataPtr childNamesData = scene->childNamesPlug()->getValue();
		const vector<InternedString> &childNames = childNamesData->readable();
		if( find( childNames.begin(), childNames.end(), *it ) == childNames.end() )
		{
			return false;
		}
		p.push_back( *it );
	}

	return true;
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

namespace
{

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

} // namespace

void GafferScene::SceneAlgo::matchingPaths( const Filter *filter, const ScenePlug *scene, PathMatcher &paths )
{
	matchingPaths( filter->outPlug(), scene, paths );
}

void GafferScene::SceneAlgo::matchingPaths( const Gaffer::IntPlug *filterPlug, const ScenePlug *scene, PathMatcher &paths )
{
	ThreadablePathAccumulator f( paths );
	GafferScene::SceneAlgo::filteredParallelTraverse( scene, filterPlug, f );
}

void GafferScene::SceneAlgo::matchingPaths( const PathMatcher &filter, const ScenePlug *scene, PathMatcher &paths )
{
	ThreadablePathAccumulator f( paths );
	GafferScene::SceneAlgo::filteredParallelTraverse( scene, filter, f );
}

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
	const BoolData *cameraBlurData = globals->member<BoolData>( "option:render:cameraBlur" );
	const bool cameraBlur = cameraBlurData ? cameraBlurData->readable() : false;

	const BoolData *transformBlurData = globals->member<BoolData>( "option:render:transformBlur" );
	const bool transformBlur = transformBlurData ? transformBlurData->readable() : false;

	const BoolData *deformationBlurData = globals->member<BoolData>( "option:render:deformationBlur" );
	const bool deformationBlur = deformationBlurData ? deformationBlurData->readable() : false;

	V2f shutter( Context::current()->getFrame() );
	if( cameraBlur || transformBlur || deformationBlur )
	{
		ConstCameraPtr camera = nullptr;
		const StringData *cameraOption = globals->member<StringData>( "option:render:camera" );
		if( cameraOption && !cameraOption->readable().empty() )
		{
			ScenePlug::ScenePath cameraPath;
			ScenePlug::stringToPath( cameraOption->readable(), cameraPath );
			if( SceneAlgo::exists( scene, cameraPath ) )
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
			capturedProcess->context = new Context( *process->context() );

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

InternedString g_contextUniquefierName = "__sceneAlgoHistory:uniquefier";
uint64_t g_contextUniquefierValue = 0;

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

/// \todo It's error prone to have to use SceneScope like this. Consider
/// improvements to the FilterPlug so that you're forced to pass a scene
/// somehow. The use of the context to provide the input scene is questionable
/// anyway, and we don't tend to cache evaluations for `Filter.out`. So perhaps
/// Filters shouldn't even be ComputeNodes, and FilterPlug shouldn't be an
/// IntPlug, and instead we should pass a scene directly to some sort of
/// `FilterPlug::match( const ScenePlug *scene )` method?
int filterResult( const FilterPlug *filter, const ScenePlug *scene )
{
	FilterPlug::SceneScope scope( Context::current(), scene );
	return filter->getValue();
}

SceneProcessor *objectTweaksWalk( const SceneAlgo::History *h )
{
	if( auto tweaks = h->scene->parent<CameraTweaks>() )
	{
		if( h->scene == tweaks->outPlug() )
		{
			Context::Scope contextScope( h->context.get() );
			if( filterResult( tweaks->filterPlug(), tweaks->inPlug() ) & PathMatcher::ExactMatch )
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

ShaderTweaks *shaderTweaksWalk( const SceneAlgo::History *h, const IECore::InternedString &attributeName )
{
	if( auto tweaks = h->scene->parent<ShaderTweaks>() )
	{
		if( h->scene == tweaks->outPlug() )
		{
			Context::Scope contextScope( h->context.get() );
			if(
				StringAlgo::matchMultiple( attributeName, tweaks->shaderPlug()->getValue() ) &&
				( filterResult( tweaks->filterPlug(), tweaks->inPlug() ) & PathMatcher::ExactMatch )
			)
			{
				return tweaks;
			}
		}
	}

	for( const auto &p : h->predecessors )
	{
		if( auto tweaks = shaderTweaksWalk( p.get(), attributeName ) )
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
		throw IECore::Exception( boost::str(
			boost::format( "Plug \"%1%\" is not a child of a ScenePlug." ) % scenePlugChild->fullName()
		) );
	}

	CapturingMonitorPtr monitor = new CapturingMonitor;
	{
		ScenePlug::PathScope pathScope( Context::current(), path );
		// Trick to bypass the hash cache and get a full upstream evaluation.
		pathScope.set( g_contextUniquefierName, g_contextUniquefierValue++ );
		Monitor::Scope monitorScope( monitor );
		scenePlugChild->hash();
	}

	if( monitor->rootProcesses().size() == 0 )
	{
		return new History(
			const_cast<ScenePlug *>( scenePlugChild->parent<ScenePlug>() ),
			new Context( *Context::current() )
		);
	}

	assert( monitor->rootProcesses().size() == 1 );
	return historyWalk( monitor->rootProcesses().front().get(), scenePlugChild->getName(), nullptr );
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
		ConstCompoundObjectPtr attributes = scene->attributes( inheritancePath );
		if( attributes->member<Object>( attributeName ) )
		{
			History::ConstPtr h = history( scene->attributesPlug(), inheritancePath );
			if( h )
			{
				return shaderTweaksWalk( h.get(), attributeName );
			}
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
