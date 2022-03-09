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

#include "GafferScene/Private/RendererAlgo.h"

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/SceneProcessor.h"
#include "GafferScene/SetAlgo.h"

#include "Gaffer/Context.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Version.h"

#include "IECoreScene/Camera.h"
#include "IECoreScene/ClippingPlane.h"
#include "IECoreScene/CoordinateSystem.h"
#include "IECoreScene/Output.h"
#include "IECoreScene/PreWorldRenderable.h"
#include "IECoreScene/Primitive.h"
#include "IECoreScene/Shader.h"
#include "IECoreScene/Transform.h"
#include "IECoreScene/VisibleRenderable.h"

#include "IECore/Data.h"
#include "IECore/Interpolator.h"
#include "IECore/NullObject.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/filesystem.hpp"

#include "tbb/blocked_range.h"
#include "tbb/parallel_reduce.h"
#include "tbb/parallel_for.h"
#include "tbb/task.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// RendererAlgo implementation
//////////////////////////////////////////////////////////////////////////

namespace
{

static InternedString g_transformBlurAttributeName( "gaffer:transformBlur" );
static InternedString g_transformBlurSegmentsAttributeName( "gaffer:transformBlurSegments" );
static InternedString g_deformationBlurAttributeName( "gaffer:deformationBlur" );
static InternedString g_deformationBlurSegmentsAttributeName( "gaffer:deformationBlurSegments" );

} // namespace

namespace GafferScene
{

namespace Private
{

namespace RendererAlgo
{

void createOutputDirectories( const IECore::CompoundObject *globals )
{
	CompoundObject::ObjectMap::const_iterator it, eIt;
	for( it = globals->members().begin(), eIt = globals->members().end(); it != eIt; it++ )
	{
		if( const Output *o = runTimeCast<Output>( it->second.get() ) )
		{
			boost::filesystem::path fileName( o->getName() );
			boost::filesystem::path directory = fileName.parent_path();
			if( !directory.empty() )
			{
				boost::filesystem::create_directories( directory );
			}
		}
	}
}

bool motionTimes( bool motionBlur, const V2f &shutter, const CompoundObject *attributes, const InternedString &attributeName, const InternedString &segmentsAttributeName, std::vector<float> &times )
{
	unsigned int segments = 0;
	if( motionBlur )
	{
		const BoolData *enabled = attributes->member<BoolData>( attributeName );
		if( !enabled || enabled->readable() ) // Default enabled if not found
		{
			const IntData *d = attributes->member<IntData>( segmentsAttributeName );
			segments = d ? std::max( 0, d->readable() ) : 1;
		}
	}

	bool changed = false;
	if( segments == 0 )
	{
		changed = times.size() != 0;
		times.clear();
		return changed;
	}

	if( times.size() != segments + 1 )
	{
		changed = true;
		times.resize( segments + 1 );
	}
	for( size_t i = 0; i < segments + 1; ++i )
	{
		float t = lerp( shutter[0], shutter[1], (float)i / (float)segments );
		if( times[i] != t )
		{
			changed = true;
			times[i] = t;
		}
	}
	return changed;
}

bool transformMotionTimes( bool motionBlur, const V2f &shutter, const CompoundObject *attributes, std::vector<float> &times )
{
	return motionTimes( motionBlur, shutter, attributes, g_transformBlurAttributeName, g_transformBlurSegmentsAttributeName, times );
}

bool deformationMotionTimes( bool motionBlur, const V2f &shutter, const CompoundObject *attributes, std::vector<float> &times )
{
	return motionTimes( motionBlur, shutter, attributes, g_deformationBlurAttributeName, g_deformationBlurSegmentsAttributeName, times );
}

bool transformSamples( const M44fPlug *transformPlug, const std::vector<float> &sampleTimes, std::vector<Imath::M44f> &samples, IECore::MurmurHash *hash )
{
	std::vector< IECore::MurmurHash > sampleHashes;
	if( !sampleTimes.size() )
	{
		sampleHashes.push_back( transformPlug->hash() );
	}
	else
	{
		Context::EditableScope timeContext( Context::current() );

		bool moving = false;
		sampleHashes.reserve( sampleTimes.size() );
		for( const float sampleTime : sampleTimes )
		{
			timeContext.setFrame( sampleTime );
			IECore::MurmurHash h = transformPlug->hash();
			if( !moving && !sampleHashes.empty() && h != sampleHashes.front() )
			{
				moving = true;
			}
			sampleHashes.push_back( h );
		}

		if( !moving )
		{
			sampleHashes.resize( 1 );
		}
	}

	if( hash )
	{
		IECore::MurmurHash combinedHash;
		if( sampleHashes.size() == 1 )
		{
			combinedHash = sampleHashes[0];
		}
		else
		{
			for( const IECore::MurmurHash &h : sampleHashes )
			{
				combinedHash.append( h );
			}
		}

		if( combinedHash == *hash )
		{
			return false;
		}
		else
		{
			*hash = combinedHash;
		}
	}

	samples.clear();
	if( !sampleTimes.size() )
	{
		// No shutter to sample over
		samples.push_back( transformPlug->getValue( &sampleHashes[0]) );
		return true;
	}

	Context::EditableScope timeContext( Context::current() );
	if( sampleHashes.size() == 1 )
	{
		// We have a shutter, but all the samples hash the same, so just evaluate one
		timeContext.setFrame( sampleTimes[0] );
		samples.push_back( transformPlug->getValue( &sampleHashes[0]) );
		return true;
	}

	// Motion case
	bool moving = false;
	samples.reserve( sampleTimes.size() );
	for( size_t i = 0; i < sampleTimes.size(); i++ )
	{
		timeContext.setFrame( sampleTimes[i] );
		M44f m;
		m = transformPlug->getValue( &sampleHashes[i] );
		if( !moving && !samples.empty() && m != samples.front() )
		{
			moving = true;
		}
		samples.push_back( m );
	}

	if( !moving )
	{
		samples.resize( 1 );
	}
	return true;
}

bool objectSamples( const ObjectPlug *objectPlug, const std::vector<float> &sampleTimes, std::vector<IECore::ConstObjectPtr> &samples, IECore::MurmurHash *hash )
{
	std::vector< IECore::MurmurHash > sampleHashes;
	if( !sampleTimes.size() )
	{
		sampleHashes.push_back( objectPlug->hash() );
	}
	else
	{
		const Context *frameContext = Context::current();
		Context::EditableScope timeContext( frameContext );

		bool moving = false;
		sampleHashes.reserve( sampleTimes.size() );
		for( const float sampleTime : sampleTimes )
		{
			timeContext.setFrame( sampleTime );

			const MurmurHash objectHash = objectPlug->hash();
			if( !moving && !sampleHashes.empty() && objectHash != sampleHashes.front() )
			{
				moving = true;
			}
			sampleHashes.push_back( objectHash );
		}

		if( !moving )
		{
			sampleHashes.resize( 1 );
		}
	}

	if( hash )
	{
		IECore::MurmurHash combinedHash;
		if( sampleHashes.size() == 1 )
		{
			combinedHash = sampleHashes[0];
		}
		else
		{
			for( const IECore::MurmurHash &h : sampleHashes )
			{
				combinedHash.append( h );
			}
		}

		if( combinedHash == *hash )
		{
			return false;
		}
		else
		{
			*hash = combinedHash;
		}
	}

	// Static case
	samples.clear();
	if( sampleHashes.size() == 1 )
	{
		ConstObjectPtr object;
		if( !sampleTimes.size() )
		{
			// No shutter, just hash on frame
			object = objectPlug->getValue( &sampleHashes[0]);
		}
		else
		{
			// We have a shutter, but all the samples hash the same, so just evaluate one
			Context::EditableScope timeContext( Context::current() );
			timeContext.setFrame( sampleTimes[0] );
			object = objectPlug->getValue( &sampleHashes[0]);
		}

		if(
			runTimeCast<const VisibleRenderable>( object.get() ) ||
			runTimeCast<const Camera>( object.get() ) ||
			runTimeCast<const CoordinateSystem>( object.get() )
		)
		{
			samples.push_back( object.get() );
		}

		return true;
	}

	// Motion case

	const Context *frameContext = Context::current();
	Context::EditableScope timeContext( frameContext );

	samples.reserve( sampleTimes.size() );
	for( size_t i = 0; i < sampleTimes.size(); i++ )
	{
		timeContext.setFrame( sampleTimes[i] );

		ConstObjectPtr object = objectPlug->getValue( &sampleHashes[i] );

		if(
			runTimeCast<const Primitive>( object.get() ) ||
			runTimeCast<const Camera>( object.get() )
		)
		{
			samples.push_back( object.get() );
		}
		else if(
			runTimeCast<const VisibleRenderable>( object.get() ) ||
			runTimeCast<const CoordinateSystem>( object.get() )
		)
		{
			// We can't motion blur these chappies, so just take the one
			// sample. This must be at the frame time rather than shutter
			// open time so that non-interpolable objects appear in the right
			// position relative to non-blurred objects.
			Context::Scope frameScope( frameContext );
			std::vector<float> tempTimes = {};

			// This is a pretty weird case - we would have taken an earlier branch if the hashes
			// had all matched, so it looks like this object is actual animated, despite not supporting
			// animation.
			// The most correct thing to do here is reset the hash, since we may not have included the
			// on frame in the samples we hashed, and in theory, the on frame value could vary indepndently
			// of shutter open and close.  This means that an animated non-animateable object will never have
			// a matching hash, and will be updated every pass.  May be a performance hazard, but probably
			// preferable to incorrect behaviour?  Just means people need to be careful to make sure their
			// heavy crowd procedurals don't have a hash that changes during the shutter?
			// ( I guess in theory we could check if the on frame time is in sampleTimes, but I don't want to
			// add any more special cases to this weird corner ).
			//
			if( hash )
			{
				*hash = IECore::MurmurHash();
			}

			return objectSamples( objectPlug, tempTimes, samples );
		}
		else
		{
			// We don't even know what these chappies are, so
			// don't take any samples at all.
			break;
		}
	}
	return true;
}

} // namespace RendererAlgo

} // namespace Private

} // namespace GafferScene

//////////////////////////////////////////////////////////////////////////
// RenderSets class
//////////////////////////////////////////////////////////////////////////

namespace
{

InternedString g_camerasSetName( "__cameras" );
InternedString g_lightsSetName( "__lights" );
InternedString g_lightFiltersSetName( "__lightFilters" );
std::string g_renderSetsPrefix( "render:" );
ConstInternedStringVectorDataPtr g_emptySetsAttribute = new InternedStringVectorData;

} // namespace

namespace GafferScene
{

namespace Private
{

namespace RendererAlgo
{

struct RenderSets::Updater
{

	Updater( const ScenePlug *scene, const ThreadState &threadState, RenderSets &renderSets, unsigned changed )
		:	changed( changed ), m_scene( scene ), m_threadState( threadState ), m_renderSets( renderSets )
	{
	}

	Updater( const Updater &updater, tbb::split )
		:	changed( NothingChanged ), m_scene( updater.m_scene ), m_threadState( updater.m_threadState ), m_renderSets( updater.m_renderSets )
	{
	}

	void operator()( const tbb::blocked_range<size_t> &r )
	{
		ScenePlug::SetScope setScope( m_threadState );

		for( size_t i=r.begin(); i!=r.end(); ++i )
		{
			Set *s = nullptr;
			InternedString n;
			unsigned potentialChange = NothingChanged;
			if( i < m_renderSets.m_sets.size() )
			{
				Sets::iterator it = m_renderSets.m_sets.begin() + i;
				s = &(it->second);
				n = it->first;
				potentialChange = RenderSetsChanged;
			}
			else if( i == m_renderSets.m_sets.size() )
			{
				s = &m_renderSets.m_camerasSet;
				n = g_camerasSetName;
				potentialChange = CamerasSetChanged;
			}
			else if( i == m_renderSets.m_sets.size() + 1 )
			{
				s = &m_renderSets.m_lightFiltersSet;
				n = g_lightFiltersSetName;
				potentialChange = LightFiltersSetChanged;
			}
			else
			{
				assert( i == m_renderSets.m_sets.size() + 2 );
				s = &m_renderSets.m_lightsSet;
				n = g_lightsSetName;
				potentialChange = LightsSetChanged;
			}

			setScope.setSetName( &n );
			const IECore::MurmurHash &hash = m_scene->setPlug()->hash();
			if( s->hash != hash )
			{
				s->set = m_scene->setPlug()->getValue( &hash )->readable();
				s->hash = hash;
				changed |= potentialChange;
			}
		}
	}

	void join( Updater &rhs )
	{
		changed |= rhs.changed;
	}

	unsigned changed;

	private :

		const ScenePlug *m_scene;
		const ThreadState &m_threadState;
		RenderSets &m_renderSets;

};

RenderSets::RenderSets()
{
}

RenderSets::RenderSets( const ScenePlug *scene )
{
	m_camerasSet.unprefixedName = g_camerasSetName;
	m_lightsSet.unprefixedName = g_lightsSetName;
	m_lightFiltersSet.unprefixedName = g_lightFiltersSetName;
	update( scene );
}

unsigned RenderSets::update( const ScenePlug *scene )
{
	unsigned changed = NothingChanged;

	// Figure out the names of the sets we want, and make
	// sure we have an entry for each of them in m_renderSets.

	ConstInternedStringVectorDataPtr setNamesData = scene->setNamesPlug()->getValue();
	const vector<InternedString> &setNames = setNamesData->readable();

	for( vector<InternedString>::const_iterator it = setNames.begin(), eIt = setNames.end(); it != eIt; ++it )
	{
		if( boost::starts_with( it->string(), g_renderSetsPrefix ) )
		{
			m_sets[*it].unprefixedName = it->string().substr( g_renderSetsPrefix.size() );
		}
	}

	// Remove anything from m_renderSets that no longer exists
	// in the scene.

	for( Sets::const_iterator it = m_sets.begin(); it != m_sets.end(); )
	{
		if( std::find( setNames.begin(), setNames.end(), it->first ) == setNames.end() )
		{
			it = m_sets.erase( it );
			changed |= RenderSetsChanged;
		}
		else
		{
			++it;
		}
	}

	// Update all the sets we want in parallel.

	Updater updater( scene, ThreadState::current(), *this, changed );
	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );
	parallel_reduce(
		tbb::blocked_range<size_t>( 0, m_sets.size() + 3 ),
		updater,
		tbb::auto_partitioner(),
		// Prevents outer tasks silently cancelling our tasks
		taskGroupContext
	);

	return updater.changed;
}

void RenderSets::clear()
{
	m_sets.clear();
	m_camerasSet = Set();
	m_lightsSet = Set();
	m_lightFiltersSet = Set();
}

const PathMatcher &RenderSets::camerasSet() const
{
	return m_camerasSet.set;
}

const PathMatcher &RenderSets::lightsSet() const
{
	return m_lightsSet.set;
}

const PathMatcher &RenderSets::lightFiltersSet() const
{
	return m_lightFiltersSet.set;
}

ConstInternedStringVectorDataPtr RenderSets::setsAttribute( const std::vector<IECore::InternedString> &path ) const
{
	InternedStringVectorDataPtr resultData = nullptr;
	vector<InternedString> *result = nullptr;
	for( Sets::const_iterator it = m_sets.begin(), eIt = m_sets.end(); it != eIt; ++it )
	{
		if( it->second.set.match( path ) & ( IECore::PathMatcher::ExactMatch | IECore::PathMatcher::AncestorMatch ) )
		{
			if( !result )
			{
				resultData = new InternedStringVectorData;
				result = &resultData->writable();
			}
			result->push_back( it->second.unprefixedName );
		}
	}
	return resultData ? resultData : g_emptySetsAttribute;
}

} // namespace RendererAlgo

} // namespace Private

} // namespace GafferScene

//////////////////////////////////////////////////////////////////////////
// LightLinks class
///////////////////////////////////////////////////////////////////////////

namespace
{

IECore::InternedString g_linkedLightsAttributeName( "linkedLights" );
IECore::InternedString g_filteredLightsAttributeName( "filteredLights" );
IECore::InternedString g_defaultLightsSetName( "defaultLights" );
IECore::InternedString g_shadowGroupAttributeName( "ai:visibility:shadow_group" );
IECore::InternedString g_lights( "lights" );
IECore::InternedString g_lightFilters( "lightFilters" );

} // namespace

namespace GafferScene
{

namespace Private
{

namespace RendererAlgo
{

LightLinks::LightLinks()
	:	m_lightLinksDirty( true ), m_lightFilterLinksDirty( true )
{
}

void LightLinks::addLight( const std::string &path, const IECoreScenePreview::Renderer::ObjectInterfacePtr &light )
{
	assert( light );
	LightMap::accessor a;
	m_lights.insert( a, path );
	assert( !a->second ); // We expect `removeLight()` to be called before `addLight()` is called again
	a->second = light;
	m_lightLinksDirty = true;
	m_lightFilterLinksDirty = true;
	clearLightLinks();
}

void LightLinks::removeLight( const std::string &path )
{
	m_lights.erase( path );
	m_lightLinksDirty = true;
	m_lightFilterLinksDirty = true;
	clearLightLinks();
}

void LightLinks::addLightFilter( const IECoreScenePreview::Renderer::ObjectInterfacePtr &lightFilter, const IECore::CompoundObject *attributes )
{
	FilterMap::accessor a;
	const bool inserted = m_filters.insert( a, lightFilter );
	assert( inserted ); (void)inserted;

	a->second = this->filteredLightsExpression( attributes );
	addFilterLink( lightFilter, a->second );

	m_lightFilterLinksDirty = true;
}

void LightLinks::updateLightFilter( const IECoreScenePreview::Renderer::ObjectInterfacePtr &lightFilter, const IECore::CompoundObject *attributes )
{
	FilterMap::accessor a;
	const bool found = m_filters.find( a, lightFilter );
	assert( found ); (void)found;

	const string e = this->filteredLightsExpression( attributes );
	if( e == a->second )
	{
		return;
	}

	removeFilterLink( lightFilter, a->second );
	a->second = e;
	addFilterLink( lightFilter, a->second );

	m_lightFilterLinksDirty = true;
}

void LightLinks::removeLightFilter( const IECoreScenePreview::Renderer::ObjectInterfacePtr &lightFilter )
{
	FilterMap::accessor a;
	const bool found = m_filters.find( a, lightFilter );
	assert( found ); (void)found;

	removeFilterLink( a->first, a->second );
	m_filters.erase( a );

	m_lightFilterLinksDirty = true;
}

void LightLinks::addFilterLink( const IECoreScenePreview::Renderer::ObjectInterfacePtr &lightFilter, const std::string &filteredLightsExpression )
{
	if( filteredLightsExpression == "" )
	{
		return;
	}

	FilterLinkMap::accessor a;
	const bool inserted = m_filterLinks.insert( a, filteredLightsExpression );
	if( inserted )
	{
		a->second.filteredLightsDirty = true;
		a->second.lightFilters = std::make_shared<IECoreScenePreview::Renderer::ObjectSet>();
	}
	a->second.lightFilters->insert( lightFilter );
}

void LightLinks::removeFilterLink( const IECoreScenePreview::Renderer::ObjectInterfacePtr &lightFilter, const std::string &filteredLightsExpression )
{
	if( filteredLightsExpression == "" )
	{
		return;
	}

	FilterLinkMap::accessor a;
	bool found = m_filterLinks.find( a, filteredLightsExpression );
	assert( found ); (void)found;
	const bool erased = a->second.lightFilters->erase( lightFilter );
	assert( erased ); (void)erased;

	if( a->second.lightFilters->empty() )
	{
		m_filterLinks.erase( a );
	}
}

void LightLinks::setsDirtied()
{
	for( auto &f : m_filterLinks )
	{
		f.second.filteredLightsDirty = true;
	}
	clearLightLinks();
	m_lightLinksDirty = true;
	m_lightFilterLinksDirty = true;
}

bool LightLinks::lightLinksDirty() const
{
	return m_lightLinksDirty;
}

bool LightLinks::lightFilterLinksDirty() const
{
	return m_lightFilterLinksDirty;
}

void LightLinks::clean()
{
	m_lightLinksDirty = false;
	m_lightFilterLinksDirty = false;
}

void LightLinks::clearLightLinks()
{
	// We may be called concurrently from `addLight()/removeLight()`, and
	// `clear()` is not threadsafe - hence the mutex.
	tbb::spin_mutex::scoped_lock l( m_lightLinksClearMutex );
	m_lightLinks.clear();
}

std::string LightLinks::filteredLightsExpression( const IECore::CompoundObject *attributes ) const
{
	const StringData *d = attributes->member<StringData>( g_filteredLightsAttributeName );
	return d ? d->readable() : "";
}

void LightLinks::outputLightLinks( const ScenePlug *scene, const IECore::CompoundObject *attributes, IECoreScenePreview::Renderer::ObjectInterface *object, IECore::MurmurHash *hash ) const
{
	const StringData *linkedLightsExpressionData = attributes->member<StringData>( g_linkedLightsAttributeName );
	/// This is Arnold-specific. We could consider making it a standard,
	/// or if we find we need to support other renderer-specific attributes, we
	/// could add a mechanism for registering them.
	const StringData *linkedShadowsExpressionData = attributes->member<StringData>( g_shadowGroupAttributeName );
	const std::string linkedLightsExpression = linkedLightsExpressionData ? linkedLightsExpressionData->readable() : "defaultLights";
	const std::string linkedShadowsExpression = linkedShadowsExpressionData ? linkedShadowsExpressionData->readable() : "__lights";

	if( hash )
	{
		IECore::MurmurHash h;
		h.append( linkedLightsExpression );
		h.append( linkedShadowsExpression );
		if( !m_lightLinksDirty && *hash == h )
		{
			// We're only being called because the attributes have changed as a whole, but the
			// specific attributes we care about haven't changed. No need to relink anything.
			/// \todo Investigate other optimisations. Perhaps `setExpressionHash()` is fast enough
			/// that we could use it to avoid editing links when sets have been dirtied but the
			/// specific sets we care about haven't changed?
			return;
		}
		*hash = h;
	}

	IECoreScenePreview::Renderer::ConstObjectSetPtr objectSet = linkedLights( linkedLightsExpression, scene );
	object->link( g_lights, objectSet );
	objectSet = linkedLights( linkedShadowsExpression, scene );
	object->link( g_shadowGroupAttributeName, objectSet );
}

IECoreScenePreview::Renderer::ConstObjectSetPtr LightLinks::linkedLights( const std::string &linkedLightsExpression, const ScenePlug *scene ) const
{
	LightLinkMap::accessor a;
	if( !m_lightLinks.insert( a, linkedLightsExpression ) )
	{
		// Already did the work
		return a->second;
	}

	PathMatcher paths = SetAlgo::evaluateSetExpression( linkedLightsExpression, scene );

	auto objectSet = std::make_shared<IECoreScenePreview::Renderer::ObjectSet>();
	for( PathMatcher::Iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
	{
		std::string pathString;
		ScenePlug::pathToString( *it, pathString );
		LightMap::const_accessor a;
		if( m_lights.find( a, pathString ) )
		{
			objectSet->insert( a->second );
		}
	}
	if( objectSet->size() == m_lights.size() )
	{
		// All lights are linked, in which case we can avoid
		// explicitly listing all the links as an optimisation.
		objectSet = nullptr;
	}

	a->second = objectSet;
	return a->second;
}

void LightLinks::outputLightFilterLinks( const ScenePlug *scene )
{

	// Update the `filteredLights` fields in our FilterLinks.

	tbb::task_group_context taskGroupContext( tbb::task_group_context::isolated );
	const ThreadState &threadState = ThreadState::current();

	tbb::parallel_for(
		m_filterLinks.range(),
		[scene, &threadState]( FilterLinkMap::range_type &range )
		{
			ThreadState::Scope threadStateScope( threadState );
			for( auto &f : range )
			{
				if( f.second.filteredLightsDirty )
				{
					f.second.filteredLights = SetAlgo::evaluateSetExpression( f.first, scene );
					f.second.filteredLightsDirty = false;
				}
			}
		},
		tbb::auto_partitioner(),
		taskGroupContext
	);

	// Loop over all our lights, outputting filter links as
	// necessary.

	tbb::parallel_for(
		m_lights.range(),
		[this]( const LightMap::range_type &range )
		{
			// No need to scope `threadState` here, as `outputLightFilterLinks()`
			// doesn't trigger Gaffer processes.
			for( const auto &l : range )
			{
				outputLightFilterLinks( l.first, l.second.get() );
			}
		},
		tbb::auto_partitioner(),
		taskGroupContext
	);
}

void LightLinks::outputLightFilterLinks( const std::string &lightName, IECoreScenePreview::Renderer::ObjectInterface *light ) const
{
	// Find the filter links that apply to this light

	vector<const FilterLink *> filterLinks;
	for( const auto &filterLink : m_filterLinks )
	{
		if( filterLink.second.filteredLights.match( lightName ) & PathMatcher::ExactMatch )
		{
			filterLinks.push_back( &filterLink.second );
		}
	}

	// Combine the filters from all the links, and output them.

	IECoreScenePreview::Renderer::ObjectSetPtr linkedFilters;
	if( filterLinks.size() == 0 )
	{
		static IECoreScenePreview::Renderer::ObjectSetPtr emptySet = make_shared<IECoreScenePreview::Renderer::ObjectSet>();
		linkedFilters = emptySet;
	}
	else if( filterLinks.size() == 1 )
	{
		// Optimisation for common case - no need to combine.
		linkedFilters = filterLinks.front()->lightFilters;
	}
	else
	{
		linkedFilters = std::make_shared<IECoreScenePreview::Renderer::ObjectSet>();
		for( const auto &filterLink : filterLinks )
		{
			linkedFilters->insert( filterLink->lightFilters->begin(), filterLink->lightFilters->end() );
		}
	}

	light->link( g_lightFilters, linkedFilters );
}

} // namespace RendererAlgo

} // namespace Private

} // namespace GafferScene

//////////////////////////////////////////////////////////////////////////
// Internal utilities
///////////////////////////////////////////////////////////////////////////

namespace
{

const std::string g_optionPrefix( "option:" );

const IECore::InternedString g_frameOptionName( "frame" );
const IECore::InternedString g_cameraOptionLegacyName( "option:render:camera" );
const InternedString g_transformBlurOptionName( "option:render:transformBlur" );
const InternedString g_deformationBlurOptionName( "option:render:deformationBlur" );
const InternedString g_shutterOptionName( "option:render:shutter" );

static InternedString g_setsAttributeName( "sets" );
static InternedString g_visibleAttributeName( "scene:visible" );

IECore::InternedString optionName( const IECore::InternedString &globalsName )
{
	if( globalsName == g_cameraOptionLegacyName )
	{
		/// \todo Just rename the options themselves in StandardOptions and remove this?
		return globalsName.string().substr( g_optionPrefix.size() + 7 );
	}

	return globalsName.string().substr( g_optionPrefix.size() );
}

// Base class for functors which output objects/lights etc.
struct LocationOutput
{

	LocationOutput( IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals, const GafferScene::Private::RendererAlgo::RenderSets &renderSets, const ScenePlug::ScenePath &root, const ScenePlug *scene )
		:	m_renderer( renderer ), m_attributes( SceneAlgo::globalAttributes( globals ) ), m_renderSets( renderSets ), m_root( root )
	{
		const BoolData *transformBlurData = globals->member<BoolData>( g_transformBlurOptionName );
		m_options.transformBlur = transformBlurData ? transformBlurData->readable() : false;

		const BoolData *deformationBlurData = globals->member<BoolData>( g_deformationBlurOptionName );
		m_options.deformationBlur = deformationBlurData ? deformationBlurData->readable() : false;

		m_options.shutter = SceneAlgo::shutter( globals, scene );

		m_transformSamples.push_back( M44f() );
	}

	bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &path )
	{
		if( path.size() > m_root.size() )
		{
			updateAttributes( scene, path );
		}

		if( const IECore::BoolData *d = m_attributes->member<IECore::BoolData>( g_visibleAttributeName ) )
		{
			if( !d->readable() )
			{
				return false;
			}
		}

		if( path.size() > m_root.size() )
		{
			updateTransform( scene );
		}

		return true;
	}

	protected :

		std::string name( const ScenePlug::ScenePath &path ) const
		{
			if( m_root.size() == path.size() )
			{
				return "/";
			}
			else
			{
				string result;
				for( ScenePlug::ScenePath::const_iterator it = path.begin() + m_root.size(), eIt = path.end(); it != eIt; ++it )
				{
					result += "/" + it->string();
				}
				return result;
			}
		}

		IECoreScenePreview::Renderer *renderer()
		{
			return m_renderer;
		}

		void deformationMotionTimes( std::vector<float> &times )
		{
			GafferScene::Private::RendererAlgo::deformationMotionTimes( m_options.deformationBlur, m_options.shutter, m_attributes.get(), times );
		}

		const IECore::CompoundObject *attributes() const
		{
			return m_attributes.get();
		}

		IECoreScenePreview::Renderer::AttributesInterfacePtr attributesInterface()
		{
			/// \todo Should we keep a cache of AttributesInterfaces so we can share
			/// them between multiple objects, or should we rely on the renderers to
			/// do something similar? Since renderers might cache some attributes
			/// (e.g. "ai:surface") separately from others, they can do a better job,
			/// but perhaps there might be some value in caching here at the higher
			/// level too?
			return m_renderer->attributes( m_attributes.get() );
		}

		void applyTransform( IECoreScenePreview::Renderer::ObjectInterface *objectInterface )
		{
			if( !m_transformSamples.size() )
			{
				return;
			}
			else if( !m_transformTimes.size() )
			{
				objectInterface->transform( m_transformSamples[0] );
			}
			else
			{
				objectInterface->transform( m_transformSamples, m_transformTimes );
			}
		}

	private :

		void updateAttributes( const ScenePlug *scene, const ScenePlug::ScenePath &path )
		{
			IECore::ConstCompoundObjectPtr attributes = scene->attributesPlug()->getValue();
			IECore::ConstInternedStringVectorDataPtr setsAttribute = m_renderSets.setsAttribute( path );

			if( attributes->members().empty() && !setsAttribute )
			{
				return;
			}

			IECore::CompoundObjectPtr updatedAttributes = new IECore::CompoundObject;
			updatedAttributes->members() = m_attributes->members();

			for( CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; ++it )
			{
				updatedAttributes->members()[it->first] = it->second;
			}

			if( setsAttribute )
			{
				updatedAttributes->members()[g_setsAttributeName] = boost::const_pointer_cast<InternedStringVectorData>( setsAttribute );
			}

			m_attributes = updatedAttributes;
		}

		void updateTransform( const ScenePlug *scene )
		{
			vector<float> sampleTimes;
			GafferScene::Private::RendererAlgo::transformMotionTimes( m_options.transformBlur, m_options.shutter, m_attributes.get(), sampleTimes );
			vector<M44f> samples;
			GafferScene::Private::RendererAlgo::transformSamples( scene->transformPlug(), sampleTimes, samples );

			if( samples.size() == 1 )
			{
				for( vector<M44f>::iterator it = m_transformSamples.begin(), eIt = m_transformSamples.end(); it != eIt; ++it )
				{
					*it = samples.front() * *it;
				}
			}
			else
			{
				vector<M44f> updatedTransformSamples;
				updatedTransformSamples.reserve( samples.size() );

				vector<float> updatedTransformTimes;
				updatedTransformTimes.reserve( samples.size() );

				vector<M44f>::const_iterator s = samples.begin();
				for( const float sampleTime : sampleTimes )
				{
					updatedTransformSamples.push_back( *s++ * transform( sampleTime ) );
					updatedTransformTimes.push_back( sampleTime );
				}

				m_transformSamples = updatedTransformSamples;
				m_transformTimes = updatedTransformTimes;
			}
		}

		M44f transform( float time )
		{
			if( m_transformSamples.empty() )
			{
				return M44f();
			}
			if( m_transformSamples.size() == 1 )
			{
				return m_transformSamples[0];
			}

			vector<float>::const_iterator t1 = lower_bound( m_transformTimes.begin(), m_transformTimes.end(), time );
			if( t1 == m_transformTimes.begin() || *t1 == time )
			{
				return m_transformSamples[t1 - m_transformTimes.begin()];
			}
			else
			{
				vector<float>::const_iterator t0 = t1 - 1;
				const float l = lerpfactor( time, *t0, *t1 );
				const M44f &s0 = m_transformSamples[t0 - m_transformTimes.begin()];
				const M44f &s1 = m_transformSamples[t1 - m_transformTimes.begin()];
				M44f result;
				LinearInterpolator<M44f>()( s0, s1, l, result );
				return result;
			}
		}

		IECoreScenePreview::Renderer *m_renderer;

		struct Options
		{
			bool transformBlur;
			bool deformationBlur;
			Imath::V2f shutter;
		};

		Options m_options;
		IECore::ConstCompoundObjectPtr m_attributes;
		const GafferScene::Private::RendererAlgo::RenderSets &m_renderSets;
		const ScenePlug::ScenePath &m_root;

		std::vector<M44f> m_transformSamples;
		std::vector<float> m_transformTimes;

};

struct CameraOutput : public LocationOutput
{

	CameraOutput( IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals, const GafferScene::Private::RendererAlgo::RenderSets &renderSets, const ScenePlug::ScenePath &root, const ScenePlug *scene )
		:	LocationOutput( renderer, globals, renderSets, root, scene ), m_globals( globals ), m_cameraSet( renderSets.camerasSet() )
	{
	}

	bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &path )
	{
		if( !LocationOutput::operator()( scene, path ) )
		{
			return false;
		}

		const size_t cameraMatch = m_cameraSet.match( path );
		if( cameraMatch & IECore::PathMatcher::ExactMatch )
		{
			// Sample cameras and apply globals
			vector<float> sampleTimes;
			deformationMotionTimes( sampleTimes );

			vector<ConstObjectPtr> samples;
			GafferScene::Private::RendererAlgo::objectSamples( scene->objectPlug(), sampleTimes, samples );

			vector<ConstCameraPtr> cameraSamples; cameraSamples.reserve( samples.size() );
			for( const auto &sample : samples )
			{
				if( auto cameraSample = runTimeCast<const Camera>( sample.get() ) )
				{
					IECoreScene::CameraPtr cameraSampleCopy = cameraSample->copy();
					GafferScene::SceneAlgo::applyCameraGlobals( cameraSampleCopy.get(), m_globals, scene );
					cameraSamples.push_back( cameraSampleCopy );
				}
			}

			// Create ObjectInterface

			if( !samples.size() || cameraSamples.size() != samples.size() )
			{
				IECore::msg(
					IECore::Msg::Warning,
					"RendererAlgo::CameraOutput",
					boost::format( "Camera missing for location \"%1%\" at frame %2%" )
						% name( path )
						% Context::current()->getFrame()
				);
			}
			else
			{
				IECoreScenePreview::Renderer::ObjectInterfacePtr objectInterface;
				if( cameraSamples.size() == 1 )
				{
					objectInterface = renderer()->camera(
						name( path ),
						cameraSamples[0].get(),
						attributesInterface().get()
					);
				}
				else
				{
					vector<const Camera *> rawCameraSamples; rawCameraSamples.reserve( cameraSamples.size() );
					for( auto &c : cameraSamples )
					{
						rawCameraSamples.push_back( c.get() );
					}
					objectInterface = renderer()->camera(
						name( path ),
						rawCameraSamples,
						sampleTimes,
						attributesInterface().get()
					);
				}

				if( objectInterface )
				{
					applyTransform( objectInterface.get() );
				}
			}
		}

		return cameraMatch & IECore::PathMatcher::DescendantMatch;
	}

	private :

		const IECore::CompoundObject *m_globals;
		const PathMatcher &m_cameraSet;

};

struct LightOutput : public LocationOutput
{

	LightOutput( IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals, const GafferScene::Private::RendererAlgo::RenderSets &renderSets, GafferScene::Private::RendererAlgo::LightLinks *lightLinks, const ScenePlug::ScenePath &root, const ScenePlug *scene )
		:	LocationOutput( renderer, globals, renderSets, root, scene ), m_lightSet( renderSets.lightsSet() ), m_lightLinks( lightLinks )
	{
	}

	bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &path )
	{
		if( !LocationOutput::operator()( scene, path ) )
		{
			return false;
		}

		const size_t lightMatch = m_lightSet.match( path );
		if( lightMatch & IECore::PathMatcher::ExactMatch )
		{
			IECore::ConstObjectPtr object = scene->objectPlug()->getValue();

			const std::string name = this->name( path );
			IECoreScenePreview::Renderer::ObjectInterfacePtr objectInterface = renderer()->light(
				name,
				!runTimeCast<const NullObject>( object.get() ) ? object.get() : nullptr,
				attributesInterface().get()
			);

			if( objectInterface )
			{
				applyTransform( objectInterface.get() );
				if( m_lightLinks )
				{
					m_lightLinks->addLight( name, objectInterface );
				}
			}

		}

		return lightMatch & IECore::PathMatcher::DescendantMatch;
	}

	const PathMatcher &m_lightSet;
	GafferScene::Private::RendererAlgo::LightLinks *m_lightLinks;

};

struct LightFiltersOutput : public LocationOutput
{

	LightFiltersOutput( IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals, const GafferScene::Private::RendererAlgo::RenderSets &renderSets, GafferScene::Private::RendererAlgo::LightLinks *lightLinks, const ScenePlug::ScenePath &root, const ScenePlug *scene )
		:	LocationOutput( renderer, globals, renderSets, root, scene ), m_lightFiltersSet( renderSets.lightFiltersSet() ), m_lightLinks( lightLinks )
	{
	}

	bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &path )
	{
		if( !LocationOutput::operator()( scene, path ) )
		{
			return false;
		}

		const size_t lightFilterMatch = m_lightFiltersSet.match( path );
		if( lightFilterMatch & IECore::PathMatcher::ExactMatch )
		{
			IECore::ConstObjectPtr object = scene->objectPlug()->getValue();

			IECoreScenePreview::Renderer::ObjectInterfacePtr objectInterface = renderer()->lightFilter(
				name( path ),
				!runTimeCast<const NullObject>( object.get() ) ? object.get() : nullptr,
				attributesInterface().get()
			);

			if( objectInterface )
			{
				applyTransform( objectInterface.get() );
				if( m_lightLinks )
				{
					m_lightLinks->addLightFilter( objectInterface, attributes() );
				}
			}
		}

		return lightFilterMatch & IECore::PathMatcher::DescendantMatch;
	}

	private :

		const PathMatcher &m_lightFiltersSet;
		GafferScene::Private::RendererAlgo::LightLinks *m_lightLinks;

};

struct ObjectOutput : public LocationOutput
{

	ObjectOutput( IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals, const GafferScene::Private::RendererAlgo::RenderSets &renderSets, const GafferScene::Private::RendererAlgo::LightLinks *lightLinks, const ScenePlug::ScenePath &root, const ScenePlug *scene )
		:	LocationOutput( renderer, globals, renderSets, root, scene ), m_cameraSet( renderSets.camerasSet() ), m_lightSet( renderSets.lightsSet() ), m_lightFiltersSet( renderSets.lightFiltersSet() ), m_lightLinks( lightLinks )
	{
	}

	bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &path )
	{
		if( !LocationOutput::operator()( scene, path ) )
		{
			return false;
		}

		if( ( m_cameraSet.match( path ) & IECore::PathMatcher::ExactMatch ) || ( m_lightFiltersSet.match( path ) & IECore::PathMatcher::ExactMatch ) || ( m_lightSet.match( path ) & IECore::PathMatcher::ExactMatch ) )
		{
			return true;
		}

		vector<float> sampleTimes;
		deformationMotionTimes( sampleTimes );

		vector<ConstObjectPtr> samples;
		GafferScene::Private::RendererAlgo::objectSamples( scene->objectPlug(), sampleTimes, samples );
		if( !samples.size() )
		{
			return true;
		}

		IECoreScenePreview::Renderer::ObjectInterfacePtr objectInterface;
		IECoreScenePreview::Renderer::AttributesInterfacePtr attributesInterface = this->attributesInterface();
		if( !sampleTimes.size() )
		{
			objectInterface = renderer()->object( name( path ), samples[0].get(), attributesInterface.get() );
		}
		else
		{
			/// \todo Can we rejig things so this conversion isn't necessary?
			vector<const Object *> objectsVector; objectsVector.reserve( samples.size() );
			for( const auto &sample : samples )
			{
				objectsVector.push_back( sample.get() );
			}
			objectInterface = renderer()->object( name( path ), objectsVector, sampleTimes, attributesInterface.get() );
		}

		if( objectInterface )
		{
			applyTransform( objectInterface.get() );
			if( m_lightLinks )
			{
				m_lightLinks->outputLightLinks( scene, attributes(), objectInterface.get() );
			}
		}

		return true;
	}

	const PathMatcher &m_cameraSet;
	const PathMatcher &m_lightSet;
	const PathMatcher &m_lightFiltersSet;
	const GafferScene::Private::RendererAlgo::LightLinks *m_lightLinks;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Public methods for outputting globals.
//////////////////////////////////////////////////////////////////////////

namespace
{

ConstOutputPtr addGafferOutputHeaders( const Output *output, const ScenePlug *scene )
{
	CompoundDataPtr param = output->parametersData()->copy();

	const Node *node = scene->node();
	const ScriptNode *script = node->scriptNode();

	param->writable()["header:gaffer:version"] = new StringData( Gaffer::versionString() );

	// Include the path to the render node to allow tools to back-track from the image
	param->writable()["header:gaffer:sourceScene"] = new StringData( scene->relativeName( script ) );

	// Include the current context
	const Context *context = Context::current();
	std::vector<IECore::InternedString> names;
	context->names( names );
	for( const auto &name : names )
	{
		DataPtr data = context->getAsData( name );

		// The requires a round-trip through the renderer's native type system, as such, it requires
		// bi-directional conversion in Cortex. Unsupported types result in a slew of warning messages
		// in render output. As many facilities employ un-supported types in their contexts as standard,
		// we whitelist known supported types, and bump the output for unsupported types to Debug messages
		// to avoid noise in the log.
		switch( data->typeId() )
		{
			case IECore::BoolDataTypeId :
			case IECore::IntDataTypeId :
			case IECore::FloatDataTypeId :
			case IECore::StringDataTypeId :
			case IECore::V3fDataTypeId :
			case IECore::Color3fDataTypeId :
			case IECore::Color4fDataTypeId :
				param->writable()["header:gaffer:context:" + name.string()] = data;
				break;
			default :
				IECore::msg(
					IECore::Msg::Debug,
					"GafferScene::RendererAlgo",
					boost::format(  "Unsupported data type for Context variable \"%s\" (%s), unable to add this variable to output image header" ) % name % data->typeName()
				);
		};
	}

	return new Output( output->getName(), output->getType(), output->getData(), param );
}

} // namespace

namespace GafferScene
{

namespace Private
{

namespace RendererAlgo
{

void outputOptions( const IECore::CompoundObject *globals, IECoreScenePreview::Renderer *renderer )
{
	outputOptions( globals, /* previousGlobals = */ nullptr, renderer );
}

void outputOptions( const IECore::CompoundObject *globals, const IECore::CompoundObject *previousGlobals, IECoreScenePreview::Renderer *renderer )
{
	// Output the current frame.

	renderer->option( g_frameOptionName, new IntData( (int)round( Context::current()->getFrame() ) ) );

	// Output anything that has changed or was added since last time.

	CompoundObject::ObjectMap::const_iterator it, eIt;
	for( it = globals->members().begin(), eIt = globals->members().end(); it != eIt; ++it )
	{
		if( !boost::starts_with( it->first.string(), g_optionPrefix ) )
		{
			continue;
		}
		if( const Object *object = it->second.get() )
		{
			bool changedOrAdded = true;
			if( previousGlobals )
			{
				if( const Object *previousObject = previousGlobals->member<Object>( it->first ) )
				{
					changedOrAdded = *previousObject != *object;
				}
			}
			if( changedOrAdded )
			{
				renderer->option( optionName( it->first ), object );
			}
		}
		else
		{
			throw IECore::Exception( "Global \"" + it->first.string() + "\" is null" );
		}
	}

	// Remove anything that has been removed since last time.

	if( !previousGlobals )
	{
		return;
	}

	for( it = previousGlobals->members().begin(), eIt = previousGlobals->members().end(); it != eIt; ++it )
	{
		if( !boost::starts_with( it->first.string(), g_optionPrefix ) )
		{
			continue;
		}
		if( it->second.get() )
		{
			if( !globals->member<Object>( it->first ) )
			{
				renderer->option( optionName( it->first ), nullptr );
			}
		}
	}
}

void outputOutputs( const ScenePlug *scene, const IECore::CompoundObject *globals, IECoreScenePreview::Renderer *renderer )
{
	outputOutputs( scene, globals, /* previousGlobals = */ nullptr, renderer );
}

void outputOutputs( const ScenePlug *scene, const IECore::CompoundObject *globals, const IECore::CompoundObject *previousGlobals, IECoreScenePreview::Renderer *renderer )
{
	static const std::string prefix( "output:" );

	// Output anything that has changed or was added since last time.

	CompoundObject::ObjectMap::const_iterator it, eIt;
	for( it = globals->members().begin(), eIt = globals->members().end(); it != eIt; ++it )
	{
		if( !boost::starts_with( it->first.string(), prefix ) )
		{
			continue;
		}
		if( const Output *output = runTimeCast<Output>( it->second.get() ) )
		{
			bool changedOrAdded = true;
			if( previousGlobals )
			{
				if( const Output *previousOutput = previousGlobals->member<Output>( it->first ) )
				{
					changedOrAdded = *previousOutput != *output;
				}
			}
			if( changedOrAdded )
			{
				ConstOutputPtr updatedOutput = addGafferOutputHeaders( output, scene );
				renderer->output( it->first.string().substr( prefix.size() ), updatedOutput.get() );
			}
		}
		else
		{
			throw IECore::Exception( "Global \"" + it->first.string() + "\" is not an IECoreScene::Output" );
		}
	}

	// Remove anything that has been removed since last time.

	if( !previousGlobals )
	{
		return;
	}

	for( it = previousGlobals->members().begin(), eIt = previousGlobals->members().end(); it != eIt; ++it )
	{
		if( !boost::starts_with( it->first.string(), prefix ) )
		{
			continue;
		}
		if( runTimeCast<Output>( it->second.get() ) )
		{
			if( !globals->member<Output>( it->first ) )
			{
				renderer->output( it->first.string().substr( prefix.size() ), nullptr );
			}
		}
	}
}

void outputCameras( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, IECoreScenePreview::Renderer *renderer )
{
	const StringData *cameraOption = globals->member<StringData>( g_cameraOptionLegacyName );
	if( cameraOption && !cameraOption->readable().empty() )
	{
		ScenePlug::ScenePath cameraPath; ScenePlug::stringToPath( cameraOption->readable(), cameraPath );
		if( !scene->exists( cameraPath ) )
		{
			throw IECore::Exception( "Camera \"" + cameraOption->readable() + "\" does not exist" );
		}
		if( !( renderSets.camerasSet().match( cameraPath ) & IECore::PathMatcher::ExactMatch ) )
		{
			throw IECore::Exception( "Camera \"" + cameraOption->readable() + "\" is not in the camera set" );
		}
	}

	const ScenePlug::ScenePath root;
	CameraOutput output( renderer, globals, renderSets, root, scene );
	SceneAlgo::parallelProcessLocations( scene, output );

	if( !cameraOption || cameraOption->readable().empty() )
	{
		CameraPtr defaultCamera = new IECoreScene::Camera;
		SceneAlgo::applyCameraGlobals( defaultCamera.get(), globals, scene );
		IECoreScenePreview::Renderer::AttributesInterfacePtr defaultAttributes = renderer->attributes( scene->attributesPlug()->defaultValue() );
		ConstStringDataPtr name = new StringData( "gaffer:defaultCamera" );
		renderer->camera( name->readable(), defaultCamera.get(), defaultAttributes.get() );
		renderer->option( "camera", name.get() );
	}
}

void outputLightFilters( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, LightLinks *lightLinks, IECoreScenePreview::Renderer *renderer )
{
	const ScenePlug::ScenePath root;
	LightFiltersOutput output( renderer, globals, renderSets, lightLinks, root, scene );
	SceneAlgo::parallelProcessLocations( scene, output );
}

void outputLights( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, LightLinks *lightLinks, IECoreScenePreview::Renderer *renderer )
{
	const ScenePlug::ScenePath root;
	LightOutput output( renderer, globals, renderSets, lightLinks, root, scene );
	SceneAlgo::parallelProcessLocations( scene, output );
}

void outputObjects( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, const LightLinks *lightLinks, IECoreScenePreview::Renderer *renderer, const ScenePlug::ScenePath &root )
{
	ObjectOutput output( renderer, globals, renderSets, lightLinks, root, scene );
	SceneAlgo::parallelProcessLocations( scene, output, root );
}

} // namespace RendererAlgo

} // namespace Private

} // namespace GafferScene
