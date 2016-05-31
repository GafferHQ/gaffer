
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
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Potential replacement for SceneAlgo::parallelTraverse().
// The original is pretty limited in that the processing at each
// location is done in isolation, with no access to parent or child
// results. This version copy constructs the functor for each location
// from its parent, allowing state to be maintained through the traversal.
//////////////////////////////////////////////////////////////////////////

namespace
{

template<typename Functor>
class LocationTask : public tbb::task
{

	public :

		LocationTask(
			const GafferScene::ScenePlug *scene,
			const Gaffer::Context *context,
			const ScenePlug::ScenePath &path,
			Functor &f
		)
			:	m_scene( scene ), m_context( context ), m_path( path ), m_f( f )
		{
		}

		virtual ~LocationTask()
		{
		}

		virtual task *execute()
		{
			Gaffer::ContextPtr context = new Gaffer::Context( *m_context, Gaffer::Context::Borrowed );
			context->set( ScenePlug::scenePathContextName, m_path );
			Gaffer::Context::Scope scopedContext( context.get() );

			if( !m_f( m_scene, m_path ) )
			{
				return NULL;
			}

			IECore::ConstInternedStringVectorDataPtr childNamesData = m_scene->childNamesPlug()->getValue();
			const std::vector<IECore::InternedString> &childNames = childNamesData->readable();
			if( childNames.empty() )
			{
				return NULL;
			}

			std::vector<Functor> childFunctors( childNames.size(), m_f );

			set_ref_count( 1 + childNames.size() );

			ScenePlug::ScenePath childPath = m_path;
			childPath.push_back( IECore::InternedString() ); // space for the child name
			for( size_t i = 0, e = childNames.size(); i < e; ++i )
			{
				childPath.back() = childNames[i];
				LocationTask *t = new( allocate_child() ) LocationTask( m_scene, m_context, childPath, childFunctors[i] );
				spawn( *t );
			}
			wait_for_all();

			return NULL;
		}

	private :

		const GafferScene::ScenePlug *m_scene;
		const Gaffer::Context *m_context;
		const GafferScene::ScenePlug::ScenePath m_path;
		Functor &m_f;

};

/// Invokes the Functor at every location in the scene,
/// visiting parent locations before their children, but
/// otherwise processing locations in parallel as much
/// as possible.
///
/// Functor should be of the following form.
///
/// ```
/// struct Functor
/// {
///
///	    /// Called to construct a new functor to be used at
///     /// each child location. This allows state to be
///     /// accumulated as the scene is traversed, with each
///     /// parent passing its state to its children.
///     Functor( const Functor &parent );
///
///     /// Called to process a specific location. May return
///     /// false to prune the traversal, or true to continue
///     /// to the children.
///     bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &path );
///
/// };
/// ```
template <class Functor>
void parallelProcessLocations( const GafferScene::ScenePlug *scene, Functor &f )
{
	Gaffer::ContextPtr c = new Gaffer::Context( *Gaffer::Context::current(), Gaffer::Context::Borrowed );
	GafferScene::Filter::setInputScene( c.get(), scene );
	LocationTask<Functor> *task = new( tbb::task::allocate_root() ) LocationTask<Functor>( scene, c.get(), ScenePlug::ScenePath(), f );
	tbb::task::spawn_root_and_wait( *task );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Internal utilities
///////////////////////////////////////////////////////////////////////////

namespace
{

const std::string g_optionPrefix( "option:" );

const IECore::InternedString g_cameraOptionLegacyName( "option:render:camera" );
const InternedString g_transformBlurOptionName( "option:render:transformBlur" );
const InternedString g_deformationBlurOptionName( "option:render:deformationBlur" );
const InternedString g_shutterOptionName( "option:render:shutter" );

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

	LocationOutput( IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals )
		:	m_renderer( renderer ), m_attributes( globalAttributes( globals ) )
	{
		const BoolData *transformBlurData = globals->member<BoolData>( g_transformBlurOptionName );
		m_options.transformBlur = transformBlurData ? transformBlurData->readable() : false;

		const BoolData *deformationBlurData = globals->member<BoolData>( g_deformationBlurOptionName );
		m_options.deformationBlur = deformationBlurData ? deformationBlurData->readable() : false;

		m_options.shutter = GafferScene::shutter( globals );

		m_transformSamples.push_back( M44f() );
	}

	bool operator()( const ScenePlug *scene, const ScenePlug::ScenePath &path )
	{
		updateAttributes( scene );

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

		void applyAttributes( IECoreScenePreview::Renderer::ObjectInterface *objectInterface )
		{
			/// \todo Should we keep a cache of AttributesInterfaces so we can share
			/// them between multiple objects, or should we rely on the renderers to
			/// do something similar? Since renderers might cache some attributes
			/// (e.g. "ai:surface") separately from others, they can do a better job,
			/// but perhaps there might be some value in caching here at the higher
			/// level too?
			IECoreScenePreview::Renderer::AttributesInterfacePtr rendererAttributes = m_renderer->attributes( m_attributes.get() );
			objectInterface->attributes( rendererAttributes.get() );
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

		void updateAttributes( const ScenePlug *scene )
		{
			IECore::ConstCompoundObjectPtr attributes = scene->attributesPlug()->getValue();
			if( attributes->members().empty() )
			{
				return;
			}

			IECore::CompoundObjectPtr updatedAttributes = new IECore::CompoundObject;
			updatedAttributes->members() = m_attributes->members();

			for( CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; ++it )
			{
				updatedAttributes->members()[it->first] = it->second;
			}

			m_attributes = updatedAttributes;
		}

		void updateTransform( const ScenePlug *scene )
		{
			const size_t segments = motionSegments( m_options.transformBlur, g_transformBlurAttributeName, g_transformBlurSegmentsAttributeName );
			vector<M44f> samples; set<float> sampleTimes;
			transformSamples( scene, segments, m_options.shutter, samples, sampleTimes );

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

		std::vector<M44f> m_transformSamples;
		std::vector<float> m_transformTimes;

};

struct CameraOutput : public LocationOutput
{

	CameraOutput( IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals, const PathMatcher &cameraSet )
		:	LocationOutput( renderer, globals ), m_globals( globals ), m_cameraSet( cameraSet )
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
				applyCameraGlobals( cameraCopy.get(), m_globals );

				std::string name;
				ScenePlug::pathToString( path, name );

				IECoreScenePreview::Renderer::ObjectInterfacePtr objectInterface = renderer()->camera( name, cameraCopy.get() );

				applyAttributes( objectInterface.get() );
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

	LightOutput( IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals, const PathMatcher &lightSet )
		:	LocationOutput( renderer, globals ), m_lightSet( lightSet )
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

			std::string name;
			ScenePlug::pathToString( path, name );
			IECoreScenePreview::Renderer::ObjectInterfacePtr objectInterface = renderer()->light(
				name,
				!runTimeCast<const NullObject>( object.get() ) ? object.get() : NULL
			);

			applyAttributes( objectInterface.get() );
			applyTransform( objectInterface.get() );
		}

		return lightMatch & Filter::DescendantMatch;
	}

	const PathMatcher &m_lightSet;

};

struct ObjectOutput : public LocationOutput
{

	ObjectOutput( IECoreScenePreview::Renderer *renderer, const IECore::CompoundObject *globals, const PathMatcher &cameraSet, const PathMatcher &lightSet )
		:	LocationOutput( renderer, globals ), m_cameraSet( cameraSet ), m_lightSet( lightSet )
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
		objectSamples( scene, deformationSegments(), shutter(), samples, sampleTimes );
		if( !samples.size() )
		{
			return true;
		}

		std::string name;
		ScenePlug::pathToString( path, name );
		IECoreScenePreview::Renderer::ObjectInterfacePtr objectInterface;
		if( !sampleTimes.size() )
		{
			objectInterface = renderer()->object( name, samples[0].get() );
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
			objectInterface = renderer()->object( name, objectsVector, timesVector );
		}

		applyAttributes( objectInterface.get() );
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

void outputOptions( const IECore::CompoundObject *globals, IECoreScenePreview::Renderer *renderer )
{
	outputOptions( globals, /* previousGlobals = */ NULL, renderer );
}

void outputOptions( const IECore::CompoundObject *globals, const IECore::CompoundObject *previousGlobals, IECoreScenePreview::Renderer *renderer )
{
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
				renderer->option( optionName( it->first ), NULL );
			}
		}
	}
}

void outputOutputs( const IECore::CompoundObject *globals, IECoreScenePreview::Renderer *renderer )
{
	outputOutputs( globals, /* previousGlobals = */ NULL, renderer );
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
				renderer->output( it->first.string().substr( prefix.size() ), NULL );
			}
		}
	}
}

void outputCameras( const ScenePlug *scene, const IECore::CompoundObject *globals, IECoreScenePreview::Renderer *renderer )
{
	ConstPathMatcherDataPtr cameraSet = scene->set( "__cameras" );

	const StringData *cameraOption = globals->member<StringData>( g_cameraOptionLegacyName );
	if( cameraOption && !cameraOption->readable().empty() )
	{
		ScenePlug::ScenePath cameraPath; ScenePlug::stringToPath( cameraOption->readable(), cameraPath );
		if( !exists( scene, cameraPath ) )
		{
			throw IECore::Exception( "Camera \"" + cameraOption->readable() + "\" does not exist" );
		}
		if( !(cameraSet->readable().match( cameraPath ) & Filter::ExactMatch) )
		{
			throw IECore::Exception( "Camera \"" + cameraOption->readable() + "\" is not in the camera set" );
		}
	}

	CameraOutput output( renderer, globals, cameraSet->readable() );
	parallelProcessLocations( scene, output );

	if( !cameraOption || cameraOption->readable().empty() )
	{
		CameraPtr defaultCamera = camera( scene, globals );
		StringDataPtr name = new StringData( "gaffer:defaultCamera" );
		renderer->camera( name->readable(), defaultCamera.get() );
		renderer->option( "camera", name.get() );
	}
}

void outputLights( const ScenePlug *scene, const IECore::CompoundObject *globals, IECoreScenePreview::Renderer *renderer )
{
	ConstPathMatcherDataPtr lightSet = scene->set( "__lights" );
	LightOutput output( renderer, globals, lightSet->readable() );
	parallelProcessLocations( scene, output );
}

void outputObjects( const ScenePlug *scene, const IECore::CompoundObject *globals, IECoreScenePreview::Renderer *renderer )
{
	ConstPathMatcherDataPtr cameraSet = scene->set( "__cameras" );
	ConstPathMatcherDataPtr lightSet = scene->set( "__lights" );
	ObjectOutput output( renderer, globals, cameraSet->readable(), lightSet->readable() );
	parallelProcessLocations( scene, output );
}

} // namespace Preview

} // namespace GafferScene
