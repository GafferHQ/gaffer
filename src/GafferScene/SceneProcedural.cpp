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

#include "OpenEXR/ImathBoxAlgo.h"
#include "OpenEXR/ImathFun.h"

#include "IECore/AttributeBlock.h"
#include "IECore/MessageHandler.h"
#include "IECore/StateRenderable.h"
#include "IECore/AngleConversion.h"
#include "IECore/MotionBlock.h"

#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"

#include "GafferScene/SceneProcedural.h"
#include "GafferScene/ScenePlug.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

tbb::atomic<int> SceneProcedural::g_pendingSceneProcedurals;
tbb::mutex SceneProcedural::g_allRenderedMutex;

SceneProcedural::AllRenderedSignal SceneProcedural::g_allRenderedSignal;

SceneProcedural::SceneProcedural( ConstScenePlugPtr scenePlug, const Gaffer::Context *context, const ScenePlug::ScenePath &scenePath )
	:	m_scenePlug( scenePlug ), m_context( new Context( *context ) ), m_scenePath( scenePath ), m_rendered( false )
{
	// get a reference to the script node to prevent it being destroyed while we're doing a render:
	m_scriptNode = m_scenePlug->ancestor<ScriptNode>();

	m_context->set( ScenePlug::scenePathContextName, m_scenePath );

	// options

	Context::Scope scopedContext( m_context.get() );
	ConstCompoundObjectPtr globals = m_scenePlug->globalsPlug()->getValue();

	const BoolData *transformBlurData = globals->member<BoolData>( "option:render:transformBlur" );
	m_options.transformBlur = transformBlurData ? transformBlurData->readable() : false;

	const BoolData *deformationBlurData = globals->member<BoolData>( "option:render:deformationBlur" );
	m_options.deformationBlur = deformationBlurData ? deformationBlurData->readable() : false;

	const V2fData *shutterData = globals->member<V2fData>( "option:render:shutter" );
	m_options.shutter = shutterData ? shutterData->readable() : V2f( -0.25, 0.25 );
	m_options.shutter += V2f( m_context->getFrame() );

	// attributes

	transformBlurData = globals->member<BoolData>( "attribute:gaffer:transformBlur" );
	m_attributes.transformBlur = transformBlurData ? transformBlurData->readable() : true;
	
	const IntData *transformBlurSegmentsData = globals->member<IntData>( "attribute:gaffer:transformBlurSegments" );
	m_attributes.transformBlurSegments = transformBlurSegmentsData ? transformBlurSegmentsData->readable() : 1;
	
	deformationBlurData = globals->member<BoolData>( "attribute:gaffer:deformationBlur" );
	m_attributes.deformationBlur = deformationBlurData ? deformationBlurData->readable() : true;
	
	const IntData *deformationBlurSegmentsData = globals->member<IntData>( "attribute:gaffer:deformationBlurSegments" );
	m_attributes.deformationBlurSegments = deformationBlurSegmentsData ? deformationBlurSegmentsData->readable() : 1;

	updateAttributes( true );
	++g_pendingSceneProcedurals;

}

SceneProcedural::SceneProcedural( const SceneProcedural &other, const ScenePlug::ScenePath &scenePath )
	:	m_scenePlug( other.m_scenePlug ), m_context( new Context( *(other.m_context), Context::Shared ) ), m_scenePath( scenePath ),
		m_options( other.m_options ), m_attributes( other.m_attributes ), m_rendered( false )
{
	// get a reference to the script node to prevent it being destroyed while we're doing a render:
	m_scriptNode = m_scenePlug->ancestor<ScriptNode>();

	m_context->set( ScenePlug::scenePathContextName, m_scenePath );

	updateAttributes( false );
	
	// precompute the bounds here, as this gets executed in parallel and bounds computation is potentially expensive:
	m_bound = bound();
	
	++g_pendingSceneProcedurals;
}

SceneProcedural::~SceneProcedural()
{
	if( !m_rendered )
	{
		decrementPendingProcedurals();
	}
}

Imath::Box3f SceneProcedural::bound() const
{
	if( !m_bound.isEmpty() )
	{
		// if this has been precomputed, return precomputed value:
		return m_bound;
	}
	
	/// \todo I think we should be able to remove this exception handling in the future.
	/// Either when we do better error handling in ValuePlug computations, or when
	/// the bug in IECoreGL that caused the crashes in SceneProceduralTest.testComputationErrors
	/// is fixed.
	try
	{
		ContextPtr timeContext = new Context( *m_context, Context::Borrowed );
		Context::Scope scopedTimeContext( timeContext.get() );

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

		Box3f result;
		for( std::set<float>::const_iterator it = times.begin(), eIt = times.end(); it != eIt; it++ )
		{
			timeContext->setFrame( *it );
			Box3f b = m_scenePlug->boundPlug()->getValue();
			M44f t = m_scenePlug->transformPlug()->getValue();
			result.extendBy( transform( b, t ) );
		}

		return result;
	}
	catch( const std::exception &e )
	{
		IECore::msg( IECore::Msg::Error, "SceneProcedural::bound()", e.what() );
	}
	return Box3f();
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
			SceneProceduralContainer& childProcedurals,
			const SceneProcedural& parent,
			const vector<InternedString>& childNames
			
		) :
			m_childProcedurals( childProcedurals ),
			m_parent( parent ),
			m_childNames( childNames )
		{
		}

		void operator()( const tbb::blocked_range<int>& range ) const
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
	
		SceneProceduralContainer& m_childProcedurals;
		const SceneProcedural& m_parent;
		const vector<InternedString>& m_childNames;
		
};


void SceneProcedural::render( Renderer *renderer ) const
{
	Context::Scope scopedContext( m_context.get() );

	/// \todo See above.
	try
	{

		// get all the attributes, and early out if we're not visibile

		ConstCompoundObjectPtr attributes = m_scenePlug->attributesPlug()->getValue();
		const BoolData *visibilityData = attributes->member<BoolData>( "scene:visible" );
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

		std::string name = "";
		for( ScenePlug::ScenePath::const_iterator it = m_scenePath.begin(), eIt = m_scenePath.end(); it != eIt; it++ )
		{
			name += "/" + it->string();
		}
		renderer->setAttribute( "name", new StringData( name ) );

		// transform

		std::set<float> transformTimes;
		motionTimes( ( m_options.transformBlur && m_attributes.transformBlur ) ? m_attributes.transformBlurSegments : 0, transformTimes );
		{
			ContextPtr timeContext = new Context( *m_context, Context::Borrowed );
			Context::Scope scopedTimeContext( timeContext.get() );

			MotionBlock motionBlock( renderer, transformTimes, transformTimes.size() > 1 );

			for( std::set<float>::const_iterator it = transformTimes.begin(), eIt = transformTimes.end(); it != eIt; it++ )
			{
				timeContext->setFrame( *it );
				renderer->concatTransform( m_scenePlug->transformPlug()->getValue() );
			}
		}

		// attributes

		for( CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; it++ )
		{
			if( const StateRenderable *s = runTimeCast<const StateRenderable>( it->second.get() ) )
			{
				s->render( renderer );
			}
			else if( const ObjectVector *o = runTimeCast<const ObjectVector>( it->second.get() ) )
			{
				for( ObjectVector::MemberContainer::const_iterator it = o->members().begin(), eIt = o->members().end(); it != eIt; it++ )
				{
					const StateRenderable *s = runTimeCast<const StateRenderable>( it->get() );
					if( s )
					{
						s->render( renderer );
					}
				}
			}
			else if( const Data *d = runTimeCast<const Data>( it->second.get() ) )
			{
				renderer->setAttribute( it->first, d );
			}
		}

		// object

		std::set<float> deformationTimes;
		motionTimes( ( m_options.deformationBlur && m_attributes.deformationBlur ) ? m_attributes.deformationBlurSegments : 0, deformationTimes );
		{
			ContextPtr timeContext = new Context( *m_context, Context::Borrowed );
			Context::Scope scopedTimeContext( timeContext.get() );

			unsigned timeIndex = 0;
			for( std::set<float>::const_iterator it = deformationTimes.begin(), eIt = deformationTimes.end(); it != eIt; it++, timeIndex++ )
			{
				timeContext->setFrame( *it );
				ConstObjectPtr object = m_scenePlug->objectPlug()->getValue();
				if( const Primitive *primitive = runTimeCast<const Primitive>( object.get() ) )
				{
					if( deformationTimes.size() > 1 && timeIndex == 0 )
					{
						renderer->motionBegin( deformationTimes );
					}

						primitive->render( renderer );

					if( deformationTimes.size() > 1 && timeIndex == deformationTimes.size() - 1 )
					{
						renderer->motionEnd();
					}
				}
				else if( const VisibleRenderable* renderable = runTimeCast< const VisibleRenderable >( object.get() ) )
				{
					renderable->render( renderer );
					break; // no motion blur for these chappies.
				}

			}
		}

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
		IECore::msg( IECore::Msg::Error, "SceneProcedural::render()", e.what() );
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
		catch( const std::exception& e )
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

void SceneProcedural::updateAttributes( bool full )
{
	Context::Scope scopedContext( m_context.get() );
	
	// \todo: Investigate if it's worth keeping these around and reusing them in SceneProcedural::render().
	
	ConstCompoundObjectPtr attributes;
	if( full )
	{
		attributes = m_scenePlug->fullAttributes( m_scenePath );
	}
	else
	{
		attributes = m_scenePlug->attributesPlug()->getValue();
	}

	if( const BoolData *transformBlurData = attributes->member<BoolData>( "gaffer:transformBlur" ) )
	{
		m_attributes.transformBlur = transformBlurData->readable();
	}

	if( const IntData *transformBlurSegmentsData = attributes->member<IntData>( "gaffer:transformBlurSegments" ) )
	{
		m_attributes.transformBlurSegments = transformBlurSegmentsData->readable();
	}

	if( const BoolData *deformationBlurData = attributes->member<BoolData>( "gaffer:deformationBlur" ) )
	{
		m_attributes.deformationBlur = deformationBlurData->readable();
	}

	if( const IntData *deformationBlurSegmentsData = attributes->member<IntData>( "gaffer:deformationBlurSegments" ) )
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
