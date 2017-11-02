
//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "tbb/task.h"
#include "tbb/parallel_reduce.h"
#include "tbb/blocked_range.h"

#include "boost/algorithm/string/predicate.hpp"

#include "IECore/Interpolator.h"
#include "IECore/NullObject.h"

#include "Gaffer/Context.h"

#include "GafferScene/Preview/RendererAlgo.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/RendererAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// RenderSets class
//////////////////////////////////////////////////////////////////////////

namespace
{

InternedString g_camerasSetName( "__cameras" );
InternedString g_lightsSetName( "__lights" );
std::string g_renderSetsPrefix( "render:" );
ConstInternedStringVectorDataPtr g_emptySetsAttribute = new InternedStringVectorData;

} // namespace

namespace GafferScene
{

namespace Preview
{

namespace RendererAlgo
{

struct RenderSets::Updater
{

	Updater( const ScenePlug *scene, const Context *context, RenderSets &renderSets, unsigned changed )
		:	changed( changed ), m_scene( scene ), m_context( context ), m_renderSets( renderSets )
	{
	}

	Updater( const Updater &updater, tbb::split )
		:	changed( NothingChanged ), m_scene( updater.m_scene ), m_context( updater.m_context ), m_renderSets( updater.m_renderSets )
	{
	}

	void operator()( const tbb::blocked_range<size_t> &r )
	{
		ScenePlug::SetScope setScope( m_context );

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
			else
			{
				assert( i == m_renderSets.m_sets.size() + 1 );
				s = &m_renderSets.m_lightsSet;
				n = g_lightsSetName;
				potentialChange = LightsSetChanged;
			}

			setScope.setSetName( n );
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
		const Context *m_context;
		RenderSets &m_renderSets;

};

RenderSets::RenderSets()
{
}

RenderSets::RenderSets( const ScenePlug *scene )
{
	m_camerasSet.unprefixedName = g_camerasSetName;
	m_lightsSet.unprefixedName = g_lightsSetName;
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

	Updater updater( scene, Context::current(), *this, changed );
	parallel_reduce( tbb::blocked_range<size_t>( 0, m_sets.size() + 2 ), updater );

	return updater.changed;
}

void RenderSets::clear()
{
	m_sets.clear();
	m_camerasSet = Set();
	m_lightsSet = Set();
}

const PathMatcher &RenderSets::camerasSet() const
{
	return m_camerasSet.set;
}

const PathMatcher &RenderSets::lightsSet() const
{
	return m_lightsSet.set;
}

ConstInternedStringVectorDataPtr RenderSets::setsAttribute( const std::vector<IECore::InternedString> &path ) const
{
	InternedStringVectorDataPtr resultData = nullptr;
	vector<InternedString> *result = nullptr;
	for( Sets::const_iterator it = m_sets.begin(), eIt = m_sets.end(); it != eIt; ++it )
	{
		if( it->second.set.match( path ) & ( Filter::ExactMatch | Filter::AncestorMatch ) )
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

} // namespace Preview

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
static InternedString g_transformBlurAttributeName( "gaffer:transformBlur" );
static InternedString g_transformBlurSegmentsAttributeName( "gaffer:transformBlurSegments" );
static InternedString g_deformationBlurAttributeName( "gaffer:deformationBlur" );
static InternedString g_deformationBlurSegmentsAttributeName( "gaffer:deformationBlurSegments" );

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

	LocationOutput( IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals, const GafferScene::Preview::RendererAlgo::RenderSets &renderSets, const ScenePlug::ScenePath &root )
		:	m_renderer( renderer ), m_attributes( SceneAlgo::globalAttributes( globals ) ), m_renderSets( renderSets ), m_root( root )
	{
		const BoolData *transformBlurData = globals->member<BoolData>( g_transformBlurOptionName );
		m_options.transformBlur = transformBlurData ? transformBlurData->readable() : false;

		const BoolData *deformationBlurData = globals->member<BoolData>( g_deformationBlurOptionName );
		m_options.deformationBlur = deformationBlurData ? deformationBlurData->readable() : false;

		m_options.shutter = SceneAlgo::shutter( globals );

		m_transformSamples.push_back( M44f() );
	}

	bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &path )
	{
		updateAttributes( scene, path );

		if( const IECore::BoolData *d = m_attributes->member<IECore::BoolData>( g_visibleAttributeName ) )
		{
			if( !d->readable() )
			{
				return false;
			}
		}

		updateTransform( scene );

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

		Imath::V2f shutter() const
		{
			return m_options.shutter;
		}

		size_t deformationSegments() const
		{
			return motionSegments( m_options.deformationBlur, g_deformationBlurAttributeName, g_deformationBlurSegmentsAttributeName );
		}

		IECoreScenePreview::Renderer::AttributesInterfacePtr attributes()
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
			if( !m_transformSamples.size() || !objectInterface )
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

		size_t motionSegments( bool motionBlur, const InternedString &attributeName, const InternedString &segmentsAttributeName ) const
		{
			if( !motionBlur )
			{
				return 0;
			}

			if( const BoolData *d = m_attributes->member<BoolData>( attributeName ) )
			{
				if( !d->readable() )
				{
					return 0;
				}
			}

			const IntData *d = m_attributes->member<IntData>( segmentsAttributeName );
			return d ? d->readable() : 1;
		}

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
			const size_t segments = motionSegments( m_options.transformBlur, g_transformBlurAttributeName, g_transformBlurSegmentsAttributeName );
			vector<M44f> samples; set<float> sampleTimes;
			RendererAlgo::transformSamples( scene, segments, m_options.shutter, samples, sampleTimes );

			if( sampleTimes.empty() )
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
				for( set<float>::const_iterator it = sampleTimes.begin(), eIt = sampleTimes.end(); it != eIt; ++it, ++s )
				{
					updatedTransformSamples.push_back( *s * transform( *it ) );
					updatedTransformTimes.push_back( *it );
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
		const GafferScene::Preview::RendererAlgo::RenderSets &m_renderSets;
		const ScenePlug::ScenePath &m_root;

		std::vector<M44f> m_transformSamples;
		std::vector<float> m_transformTimes;

};

struct CameraOutput : public LocationOutput
{

	CameraOutput( IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals, const GafferScene::Preview::RendererAlgo::RenderSets &renderSets, const ScenePlug::ScenePath &root )
		:	LocationOutput( renderer, globals, renderSets, root ), m_globals( globals ), m_cameraSet( renderSets.camerasSet() )
	{
	}

	bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &path )
	{
		if( !LocationOutput::operator()( scene, path ) )
		{
			return false;
		}

		const size_t cameraMatch = m_cameraSet.match( path );
		if( cameraMatch & Filter::ExactMatch )
		{
			IECore::ConstObjectPtr object = scene->objectPlug()->getValue();
			if( const Camera *camera = runTimeCast<const Camera>( object.get() ) )
			{
				IECore::CameraPtr cameraCopy = camera->copy();

				// Explicit namespace can be removed once deprecated applyCameraGlobals
				// is removed from GafferScene::SceneAlgo
				GafferScene::Preview::RendererAlgo::applyCameraGlobals( cameraCopy.get(), m_globals );

				IECoreScenePreview::Renderer::ObjectInterfacePtr objectInterface = renderer()->camera(
					name( path ),
					cameraCopy.get(),
					attributes().get()
				);

				applyTransform( objectInterface.get() );
			}
		}

		return cameraMatch & Filter::DescendantMatch;
	}

	private :

		const IECore::CompoundObject *m_globals;
		const PathMatcher &m_cameraSet;

};

struct LightOutput : public LocationOutput
{

	LightOutput( IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals, const GafferScene::Preview::RendererAlgo::RenderSets &renderSets, const ScenePlug::ScenePath &root )
		:	LocationOutput( renderer, globals, renderSets, root ), m_lightSet( renderSets.lightsSet() )
	{
	}

	bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &path )
	{
		if( !LocationOutput::operator()( scene, path ) )
		{
			return false;
		}

		const size_t lightMatch = m_lightSet.match( path );
		if( lightMatch & Filter::ExactMatch )
		{
			IECore::ConstObjectPtr object = scene->objectPlug()->getValue();

			IECoreScenePreview::Renderer::ObjectInterfacePtr objectInterface = renderer()->light(
				name( path ),
				!runTimeCast<const NullObject>( object.get() ) ? object.get() : nullptr,
				attributes().get()
			);

			applyTransform( objectInterface.get() );
		}

		return lightMatch & Filter::DescendantMatch;
	}

	const PathMatcher &m_lightSet;

};

struct ObjectOutput : public LocationOutput
{

	ObjectOutput( IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals, const GafferScene::Preview::RendererAlgo::RenderSets &renderSets, const ScenePlug::ScenePath &root )
		:	LocationOutput( renderer, globals, renderSets, root ), m_cameraSet( renderSets.camerasSet() ), m_lightSet( renderSets.lightsSet() )
	{
	}

	bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &path )
	{
		if( !LocationOutput::operator()( scene, path ) )
		{
			return false;
		}

		if( ( m_cameraSet.match( path ) & Filter::ExactMatch ) || ( m_lightSet.match( path ) & Filter::ExactMatch ) )
		{
			return true;
		}

		vector<ConstVisibleRenderablePtr> samples; set<float> sampleTimes;
		RendererAlgo::objectSamples( scene, deformationSegments(), shutter(), samples, sampleTimes );
		if( !samples.size() )
		{
			return true;
		}

		IECoreScenePreview::Renderer::ObjectInterfacePtr objectInterface;
		IECoreScenePreview::Renderer::AttributesInterfacePtr attributesInterface = attributes();
		if( !sampleTimes.size() )
		{
			objectInterface = renderer()->object( name( path ), samples[0].get(), attributesInterface.get() );
		}
		else
		{
			/// \todo Can we rejig things so these conversions aren't necessary?
			vector<const Object *> objectsVector; objectsVector.reserve( samples.size() );
			vector<float> timesVector( sampleTimes.begin(), sampleTimes.end() );
			for( vector<ConstVisibleRenderablePtr>::const_iterator it = samples.begin(), eIt = samples.end(); it != eIt; ++it )
			{
				objectsVector.push_back( it->get() );
			}
			objectInterface = renderer()->object( name( path ), objectsVector, timesVector, attributesInterface.get() );
		}

		applyTransform( objectInterface.get() );

		return true;
	}

	const PathMatcher &m_cameraSet;
	const PathMatcher &m_lightSet;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Public methods for outputting globals.
//////////////////////////////////////////////////////////////////////////

namespace GafferScene
{

namespace Preview
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
		if( const Data *data = runTimeCast<Data>( it->second.get() ) )
		{
			bool changedOrAdded = true;
			if( previousGlobals )
			{
				if( const Data *previousData = previousGlobals->member<Data>( it->first ) )
				{
					changedOrAdded = *previousData != *data;
				}
			}
			if( changedOrAdded )
			{
				renderer->option( optionName( it->first ), data );
			}
		}
		else
		{
			throw IECore::Exception( "Global \"" + it->first.string() + "\" is not an IECore::Data" );
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
		if( runTimeCast<Data>( it->second.get() ) )
		{
			if( !globals->member<Data>( it->first ) )
			{
				renderer->option( optionName( it->first ), nullptr );
			}
		}
	}
}

void outputOutputs( const IECore::CompoundObject *globals, IECoreScenePreview::Renderer *renderer )
{
	outputOutputs( globals, /* previousGlobals = */ nullptr, renderer );
}

void outputOutputs( const IECore::CompoundObject *globals, const IECore::CompoundObject *previousGlobals, IECoreScenePreview::Renderer *renderer )
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
		if( const Display *display = runTimeCast<Display>( it->second.get() ) )
		{
			bool changedOrAdded = true;
			if( previousGlobals )
			{
				if( const Display *previousDisplay = previousGlobals->member<Display>( it->first ) )
				{
					changedOrAdded = *previousDisplay != *display;
				}
			}
			if( changedOrAdded )
			{
				renderer->output( it->first.string().substr( prefix.size() ), display );
			}
		}
		else
		{
			throw IECore::Exception( "Global \"" + it->first.string() + "\" is not an IECore::Display" );
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
		if( runTimeCast<Display>( it->second.get() ) )
		{
			if( !globals->member<Display>( it->first ) )
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
		if( !SceneAlgo::exists( scene, cameraPath ) )
		{
			throw IECore::Exception( "Camera \"" + cameraOption->readable() + "\" does not exist" );
		}
		if( !( renderSets.camerasSet().match( cameraPath ) & Filter::ExactMatch ) )
		{
			throw IECore::Exception( "Camera \"" + cameraOption->readable() + "\" is not in the camera set" );
		}
	}

	const ScenePlug::ScenePath root;
	CameraOutput output( renderer, globals, renderSets, root );
	SceneAlgo::parallelProcessLocations( scene, output );

	if( !cameraOption || cameraOption->readable().empty() )
	{
		CameraPtr defaultCamera = SceneAlgo::camera( scene, globals );
		StringDataPtr name = new StringData( "gaffer:defaultCamera" );
		IECoreScenePreview::Renderer::AttributesInterfacePtr defaultAttributes = renderer->attributes( scene->attributesPlug()->defaultValue() ).get();
		renderer->camera(
			name->readable(),
			defaultCamera.get(),
			defaultAttributes.get()
		);
		renderer->option( "camera", name.get() );
	}
}

void outputLights( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, IECoreScenePreview::Renderer *renderer )
{
	const ScenePlug::ScenePath root;
	LightOutput output( renderer, globals, renderSets, root );
	SceneAlgo::parallelProcessLocations( scene, output );
}

void outputObjects( const ScenePlug *scene, const IECore::CompoundObject *globals, const RenderSets &renderSets, IECoreScenePreview::Renderer *renderer, const ScenePlug::ScenePath &root )
{
	ObjectOutput output( renderer, globals, renderSets, root );
	SceneAlgo::parallelProcessLocations( scene, output, root );
}

void applyCameraGlobals( IECore::Camera *camera, const IECore::CompoundObject *globals )
{

	// apply the resolution, aspect ratio and crop window

	V2i resolution( 640, 480 );

	const V2iData *resolutionOverrideData = camera->parametersData()->member<V2iData>( "resolutionOverride" );
	if( resolutionOverrideData )
	{
		// We allow a parameter on the camera to override the resolution from the globals - this
		// is useful when defining secondary cameras for doing texture projections.
		/// \todo Consider how this might fit in as part of a more comprehensive camera setup.
		/// Perhaps we might actually want a specific Camera subclass for such things?
		resolution = resolutionOverrideData->readable();
	}
	else
	{
		if( const V2iData *resolutionData = globals->member<V2iData>( "option:render:resolution" ) )
		{
			resolution = resolutionData->readable();
		}

		if( const FloatData *resolutionMultiplierData = globals->member<FloatData>( "option:render:resolutionMultiplier" ) )
		{
			resolution.x = int((float)resolution.x * resolutionMultiplierData->readable());
			resolution.y = int((float)resolution.y * resolutionMultiplierData->readable());
		}

		const FloatData *pixelAspectRatioData = globals->member<FloatData>( "option:render:pixelAspectRatio" );
		if( pixelAspectRatioData )
		{
			camera->parameters()["pixelAspectRatio"] = pixelAspectRatioData->copy();
		}
	}

	camera->parameters()["resolution"] = new V2iData( resolution );

	// calculate an appropriate screen window

	camera->addStandardParameters();

	// apply overscan


	Box2i renderRegion( V2i( 0 ), resolution - V2i( 1 ) );

	const BoolData *overscanData = globals->member<BoolData>( "option:render:overscan" );
	if( overscanData && overscanData->readable() )
	{
		// get offsets for each corner of image (as a multiplier of the image width)
		V2f minOffset( 0.1 ), maxOffset( 0.1 );
		if( const FloatData *overscanValueData = globals->member<FloatData>( "option:render:overscanLeft" ) )
		{
			minOffset.x = overscanValueData->readable();
		}
		if( const FloatData *overscanValueData = globals->member<FloatData>( "option:render:overscanRight" ) )
		{
			maxOffset.x = overscanValueData->readable();
		}
		if( const FloatData *overscanValueData = globals->member<FloatData>( "option:render:overscanBottom" ) )
		{
			minOffset.y = overscanValueData->readable();
		}
		if( const FloatData *overscanValueData = globals->member<FloatData>( "option:render:overscanTop" ) )
		{
			maxOffset.y = overscanValueData->readable();
		}

		// convert those offsets into pixel values and apply them to the render region
		renderRegion.min -= V2i(
			int(minOffset.x * (float)resolution.x),
			int(minOffset.y * (float)resolution.y)
		);

		renderRegion.max += V2i(
			int(maxOffset.x * (float)resolution.x),
			int(maxOffset.y * (float)resolution.y)
		);
	}


	const Box2fData *cropWindowData = globals->member<Box2fData>( "option:render:cropWindow" );
	if( cropWindowData )
	{
		const Box2f &cropWindow = cropWindowData->readable();
		Box2i cropRegion(
			V2i( (int)( round( resolution.x * cropWindow.min.x ) ),
			     (int)( round( resolution.y * cropWindow.min.y ) ) ),
			V2i( (int)( round( resolution.x * cropWindow.max.x ) ) - 1,
			     (int)( round( resolution.y * cropWindow.max.y ) ) - 1 ) );

		renderRegion.min.x = std::max( renderRegion.min.x, cropRegion.min.x );
		renderRegion.max.x = std::min( renderRegion.max.x, cropRegion.max.x );
		renderRegion.min.y = std::max( renderRegion.min.y, cropRegion.min.y );
		renderRegion.max.y = std::min( renderRegion.max.y, cropRegion.max.y );

	}

	camera->parameters()["renderRegion"] = new Box2iData( renderRegion );

	// apply the shutter

	camera->parameters()["shutter"] = new V2fData( SceneAlgo::shutter( globals ) );

}

} // namespace RendererAlgo

} // namespace Preview

} // namespace GafferScene
