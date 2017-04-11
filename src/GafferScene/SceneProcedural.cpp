//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2013, John Haddon. All rights reserved.
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

#include "tbb/parallel_for.h"
#include "tbb/task_scheduler_init.h"

#include "boost/lexical_cast.hpp"

#include "OpenEXR/ImathBoxAlgo.h"
#include "OpenEXR/ImathFun.h"

#include "IECore/AttributeBlock.h"
#include "IECore/MessageHandler.h"
#include "IECore/StateRenderable.h"
#include "IECore/AngleConversion.h"
#include "IECore/MotionBlock.h"
#include "IECore/Primitive.h"

#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"

#include "GafferScene/SceneProcedural.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/RendererAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

// Static InternedStrings for attribute and option names. We don't want the overhead of
// constructing these each time.

static InternedString g_transformBlurOptionName( "option:render:transformBlur" );
static InternedString g_deformationBlurOptionName( "option:render:deformationBlur" );
static InternedString g_shutterOptionName( "option:render:shutter" );

static InternedString g_transformBlurGlobalAttributeName( "attribute:gaffer:transformBlur" );
static InternedString g_transformBlurSegmentsGlobalAttributeName( "attribute:gaffer:transformBlurSegments" );
static InternedString g_deformationBlurGlobalAttributeName( "attribute:gaffer:deformationBlur" );
static InternedString g_deformationBlurSegmentsGlobalAttributeName( "attribute:gaffer:deformationBlurSegments" );

static InternedString g_visibleAttributeName( "scene:visible" );
static InternedString g_transformBlurAttributeName( "gaffer:transformBlur" );
static InternedString g_transformBlurSegmentsAttributeName( "gaffer:transformBlurSegments" );
static InternedString g_deformationBlurAttributeName( "gaffer:deformationBlur" );
static InternedString g_deformationBlurSegmentsAttributeName( "gaffer:deformationBlurSegments" );

// TBB recommends that you defer decisions about how many threads to create
// to it, so you can write nice high level code and it can decide how best
// to schedule the work. Generally if left to do this, it schedules it by
// making as many threads as there are cores, to make best use of the hardware.
// This is all well and good, until you're running multiple renders side-by-side,
// telling the renderer to use a limited number of threads so they all play nicely
// together. Let's use the example of a 32 core machine with 4 8-thread 3delight
// renders running side by side.
//
// - 3delight will make 8 threads. TBB didn't make them itself, so it considers
//   them to be "master" threads.
// - 3delight will then call our procedurals on some subset of those 8 threads.
//   We'll execute graphs, which may or may not use TBB internally, but even if they
//   don't, we're using parallel_for for child procedural construction.
// - TBB will be invoked from these master threads, see that it hasn't been
//   initialised yet, and merrily initialise itself to use 32 threads.
// - We now have 4 side by side renders each trying to take over the machine,
//   and a not-so-happy IT department.
//
// The "solution" to this is to explicitly initialise TBB every time a procedural
// is invoked, limiting it to a certain number of threads. Problem solved? Maybe.
// There's another wrinkle, in that TBB is initialised separately for each master
// thread, and if each master asks for a maximum of N threads, and there are M masters,
// TBB might actually make up to `M * N` threads, clamped at the number of cores.
// So with N set to 8, you could still get a single process trying to use the
// whole machine. In practice, it appears that 3delight perhaps doesn't make great
// use of procedural concurrency, so the worst case of M procedurals in flight,
// each trying to use N threads may not occur. What other renderers do in this
// situation is unknown.
//
// I strongly suspect that the long term solution to this is to abandon using
// a procedural hierarchy matching the scene hierarchy, and to do our own
// threaded traversal of the scene, outputting the results to the renderer via
// a single master thread. We could then be sure of our resource usage, and
// also get better performance with renderers unable to make best use of
// procedural concurrency.
//
// In the meantime, we introduce a hack. The GAFFERSCENE_SCENEPROCEDURAL_THREADS
// environment variable may be used to clamp the number of threads used by any
// given master thread. We sincerely hope to have a better solution before too
// long.
//
// Worthwhile reading :
//
// https://software.intel.com/en-us/blogs/2011/04/09/tbb-initialization-termination-and-resource-management-details-juicy-and-gory/
//
void initializeTaskScheduler( tbb::task_scheduler_init &tsi )
{
	assert( !tsi.is_active() );

	static int g_maxThreads = -1;
	if( g_maxThreads == -1 )
	{
		if( const char *c = getenv( "GAFFERSCENE_SCENEPROCEDURAL_THREADS" ) )
		{
			g_maxThreads = boost::lexical_cast<int>( c );
		}
		else
		{
			g_maxThreads = 0;
		}
	}

	if( g_maxThreads > 0 )
	{
		tsi.initialize( g_maxThreads );
	}
}

tbb::atomic<int> SceneProcedural::g_pendingSceneProcedurals;
tbb::mutex SceneProcedural::g_allRenderedMutex;

SceneProcedural::AllRenderedSignal SceneProcedural::g_allRenderedSignal;

SceneProcedural::SceneProcedural( ConstScenePlugPtr scenePlug, const Gaffer::Context *context, const ScenePlug::ScenePath &scenePath, bool computeBound )
	:	m_scenePlug( scenePlug ), m_context( new Context( *context ) ), m_scenePath( scenePath ), m_rendered( false )
{
	tbb::task_scheduler_init tsi( tbb::task_scheduler_init::deferred );
	initializeTaskScheduler( tsi );

	// get a reference to the script node to prevent it being destroyed while we're doing a render:
	m_scriptNode = m_scenePlug->ancestor<ScriptNode>();

	m_context->set( ScenePlug::scenePathContextName, m_scenePath );

	// options

	Context::Scope scopedContext( m_context.get() );
	ConstCompoundObjectPtr globals = m_scenePlug->globalsPlug()->getValue();

	const BoolData *transformBlurData = globals->member<BoolData>( g_transformBlurOptionName );
	m_options.transformBlur = transformBlurData ? transformBlurData->readable() : false;

	const BoolData *deformationBlurData = globals->member<BoolData>( g_deformationBlurOptionName );
	m_options.deformationBlur = deformationBlurData ? deformationBlurData->readable() : false;

	const V2fData *shutterData = globals->member<V2fData>( g_shutterOptionName );
	m_options.shutter = shutterData ? shutterData->readable() : V2f( -0.25, 0.25 );
	m_options.shutter += V2f( m_context->getFrame() );

	// attributes

	transformBlurData = globals->member<BoolData>( g_transformBlurGlobalAttributeName );
	m_attributes.transformBlur = transformBlurData ? transformBlurData->readable() : true;

	const IntData *transformBlurSegmentsData = globals->member<IntData>( g_transformBlurSegmentsGlobalAttributeName );
	m_attributes.transformBlurSegments = transformBlurSegmentsData ? transformBlurSegmentsData->readable() : 1;

	deformationBlurData = globals->member<BoolData>( g_deformationBlurGlobalAttributeName );
	m_attributes.deformationBlur = deformationBlurData ? deformationBlurData->readable() : true;

	const IntData *deformationBlurSegmentsData = globals->member<IntData>( g_deformationBlurSegmentsGlobalAttributeName );
	m_attributes.deformationBlurSegments = deformationBlurSegmentsData ? deformationBlurSegmentsData->readable() : 1;

	updateAttributes();
	initBound( computeBound );

	++g_pendingSceneProcedurals;
}

SceneProcedural::SceneProcedural( const SceneProcedural &other, const ScenePlug::ScenePath &scenePath )
	:	m_scenePlug( other.m_scenePlug ), m_context( new Context( *(other.m_context), Context::Shared ) ), m_scenePath( scenePath ),
		m_options( other.m_options ), m_attributes( other.m_attributes ), m_rendered( false )
{
	tbb::task_scheduler_init tsi( tbb::task_scheduler_init::deferred );
	initializeTaskScheduler( tsi );

	// get a reference to the script node to prevent it being destroyed while we're doing a render:
	m_scriptNode = m_scenePlug->ancestor<ScriptNode>();

	m_context->set( ScenePlug::scenePathContextName, m_scenePath );

	updateAttributes();
	initBound( other.m_bound != Procedural::noBound );

	++g_pendingSceneProcedurals;
}

SceneProcedural::~SceneProcedural()
{
	if( !m_rendered )
	{
		decrementPendingProcedurals();
	}
}

void SceneProcedural::initBound( bool compute )
{
	if( !compute )
	{
		m_bound = Procedural::noBound;
		return;
	}

	/// \todo I think we should be able to remove this exception handling in the future.
	/// Either when we do better error handling in ValuePlug computations, or when
	/// the bug in IECoreGL that caused the crashes in SceneProceduralTest.testComputationErrors
	/// is fixed.
	try
	{
		Context::EditableScope timeScope( m_context.get() );

		/// \todo This doesn't take account of the unfortunate fact that our children may have differing
		/// numbers of segments than ourselves. To get an accurate bound we would need to know the different sample
		/// times the children may be using and evaluate a bound at those times as well. We don't want to visit
		/// the children to find the sample times out though, because that defeats the entire point of deferred loading.
		///
		/// Here are some possible approaches :
		///
		/// 1) Add a new attribute called boundSegments, which defines the number of segments used to calculate
		///    the bounding box. It would be the responsibility of the user to set this to an appropriate value
		///    at the parent levels, so that the parents calculate bounds appropriate for the children.
		///    This seems like a bit too much burden on the user.
		///
		/// 2) Add a global option called "maxSegments" - this will clamp the number of segments used on anything
		///    and will be set to 1 by default. The user will need to increase it to allow the leaf level attributes
		///    to take effect, and all bounding boxes everywhere will be calculated using that number of segments
		///    (actually I think it'll be that number of segments and all nondivisible smaller numbers). This should
		///    be accurate but potentially slower, because we'll be doing the extra work everywhere rather than only
		///    where needed. It still places a burden on the user (increasing the global clamp appropriately),
		///    but not quite such a bad one as they don't have to figure anything out and only have one number to set.
		///
		/// 3) Have the StandardOptions node secretly compute a global "maxSegments" behind the scenes. This would
		///    work as for 2) but remove the burden from the user. However, it would mean preventing any expressions
		///    or connections being used on the segments attributes, because they could be used to cheat the system.
		///    It could potentially be faster than 2) because it wouldn't have to do all nondivisible numbers - it
		///    could know exactly which numbers of segments were in existence. It still suffers from the
		///    "pay the price everywhere" problem.

		std::set<float> times;
		motionTimes( ( m_options.deformationBlur && m_attributes.deformationBlur ) ? m_attributes.deformationBlurSegments : 0, times );
		motionTimes( ( m_options.transformBlur && m_attributes.transformBlur ) ? m_attributes.transformBlurSegments : 0, times );

		m_bound = Imath::Box3f();
		for( std::set<float>::const_iterator it = times.begin(), eIt = times.end(); it != eIt; it++ )
		{
			timeScope.setFrame( *it );
			Box3f b = m_scenePlug->boundPlug()->getValue();
			M44f t = m_scenePlug->transformPlug()->getValue();
			m_bound.extendBy( transform( b, t ) );
		}
	}
	catch( const std::exception &e )
	{
		m_bound = Imath::Box3f();
		std::string name;
		ScenePlug::pathToString( m_scenePath, name );
		IECore::msg( IECore::Msg::Error, "SceneProcedural::bound() " + name, e.what() );
	}
}

Imath::Box3f SceneProcedural::bound() const
{
	return m_bound;
}

//////////////////////////////////////////////////////////////////////////
// SceneProceduralCreate implementation
//
// This uses tbb::parallel_for to fill up a preallocated array of
// SceneProceduralPtrs with new SceneProcedurals, based on the parent
// SceneProcedural and the child names we supply.
//
//////////////////////////////////////////////////////////////////////////

class SceneProcedural::SceneProceduralCreate
{

	public:
		typedef std::vector<SceneProceduralPtr> SceneProceduralContainer;

		SceneProceduralCreate(
			SceneProceduralContainer &childProcedurals,
			const SceneProcedural &parent,
			const vector<InternedString> &childNames

		) :
			m_childProcedurals( childProcedurals ),
			m_parent( parent ),
			m_childNames( childNames )
		{
		}

		void operator()( const tbb::blocked_range<int> &range ) const
		{
			for( int i=range.begin(); i!=range.end(); ++i )
			{
				ScenePlug::ScenePath childScenePath = m_parent.m_scenePath;
				childScenePath.push_back( m_childNames[i] );
				SceneProceduralPtr sceneProcedural = new SceneProcedural( m_parent, childScenePath );
				m_childProcedurals[ i ] = sceneProcedural;
			}
		}

	private:

		SceneProceduralContainer &m_childProcedurals;
		const SceneProcedural &m_parent;
		const vector<InternedString> &m_childNames;

};


void SceneProcedural::render( Renderer *renderer ) const
{
	tbb::task_scheduler_init tsi( tbb::task_scheduler_init::deferred );
	initializeTaskScheduler( tsi );

	Context::Scope scopedContext( m_context.get() );

	std::string name;
	ScenePlug::pathToString( m_scenePath, name );

	/// \todo See above.
	try
	{

		// get all the attributes, and early out if we're not visibile

		const BoolData *visibilityData = m_attributesObject->member<BoolData>( g_visibleAttributeName );
		if( visibilityData && !visibilityData->readable() )
		{

			if( !m_rendered )
			{
				decrementPendingProcedurals();
			}
			m_rendered = true;
			return;
		}

		// if we are visible then make an attribute block to contain everything, set the name
		// and get on with generating things.

		AttributeBlock attributeBlock( renderer );

		renderer->setAttribute( "name", new StringData( name ) );

		// transform

		RendererAlgo::outputTransform( m_scenePlug.get(), renderer, ( m_options.transformBlur && m_attributes.transformBlur ) ? m_attributes.transformBlurSegments : 0, m_options.shutter );

		// attributes

		RendererAlgo::outputAttributes( m_attributesObject.get(), renderer );

		// object

		RendererAlgo::outputObject( m_scenePlug.get(), renderer, ( m_options.deformationBlur && m_attributes.deformationBlur ) ? m_attributes.deformationBlurSegments : 0, m_options.shutter );

		// children

		ConstInternedStringVectorDataPtr childNames = m_scenePlug->childNamesPlug()->getValue();
		if( childNames->readable().size() )
		{
			// Creating a SceneProcedural involves an attribute/bound evaluation, which are
			// potentially expensive, so we're parallelizing them.

			// allocate space for child procedurals:
			SceneProceduralCreate::SceneProceduralContainer childProcedurals( childNames->readable().size() );

			// create procedurals in parallel:
			SceneProceduralCreate s(
				childProcedurals,
				*this,
				childNames->readable()
			);
			tbb::parallel_for( tbb::blocked_range<int>( 0, childNames->readable().size() ), s );

			// send to the renderer in series:

			std::vector<SceneProceduralPtr>::const_iterator procIt = childProcedurals.begin(), procEit = childProcedurals.end();
			for( ; procIt != procEit; ++procIt )
			{
				renderer->procedural( *procIt );
			}
		}
	}
	catch( const std::exception &e )
	{
		IECore::msg( IECore::Msg::Error, "SceneProcedural::render() " + name, e.what() );
	}
	if( !m_rendered )
	{
		decrementPendingProcedurals();
	}
	m_rendered = true;
}

void SceneProcedural::decrementPendingProcedurals() const
{
	if( --g_pendingSceneProcedurals == 0 )
	{
		try
		{
			tbb::mutex::scoped_lock l( g_allRenderedMutex );
			g_allRenderedSignal();
		}
		catch( const std::exception &e )
		{
			IECore::msg( IECore::Msg::Error, "SceneProcedural::allRenderedSignal() error", e.what() );
		}
	}
}

IECore::MurmurHash SceneProcedural::hash() const
{
	/// \todo Implement me properly.
	return IECore::MurmurHash();
}

void SceneProcedural::updateAttributes()
{
	Context::Scope scopedContext( m_context.get() );

	// We need to compute the attributes during construction so
	// that we have the right motion blur settings in bound(), and
	// we don't want to have to compute them again in render(), so
	// we store them. We only output attributes which are local to
	// the location we represent.
	m_attributesObject = m_scenePlug->attributesPlug()->getValue();

	// Some attributes have special meaning to us - we must track
	// the inherited values of these.
	if( const BoolData *transformBlurData = m_attributesObject->member<BoolData>( g_transformBlurAttributeName ) )
	{
		m_attributes.transformBlur = transformBlurData->readable();
	}

	if( const IntData *transformBlurSegmentsData = m_attributesObject->member<IntData>( g_transformBlurSegmentsAttributeName ) )
	{
		m_attributes.transformBlurSegments = transformBlurSegmentsData->readable();
	}

	if( const BoolData *deformationBlurData = m_attributesObject->member<BoolData>( g_deformationBlurAttributeName ) )
	{
		m_attributes.deformationBlur = deformationBlurData->readable();
	}

	if( const IntData *deformationBlurSegmentsData = m_attributesObject->member<IntData>( g_deformationBlurSegmentsAttributeName ) )
	{
		m_attributes.deformationBlurSegments = deformationBlurSegmentsData->readable();
	}
}

void SceneProcedural::motionTimes( unsigned segments, std::set<float> &times ) const
{
	if( !segments )
	{
		times.insert( m_context->getFrame() );
	}
	else
	{
		for( unsigned i = 0; i<segments + 1; i++ )
		{
			times.insert( lerp( m_options.shutter[0], m_options.shutter[1], (float)i / (float)segments ) );
		}
	}
}

SceneProcedural::AllRenderedSignal &SceneProcedural::allRenderedSignal()
{
	return g_allRenderedSignal;
}
