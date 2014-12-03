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

#include "tbb/spin_mutex.h"
#include "tbb/task.h"

#include "IECore/MatrixMotionTransform.h"
#include "IECore/Camera.h"

#include "Gaffer/Context.h"

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/Filter.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/PathMatcher.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

bool GafferScene::exists( const ScenePlug *scene, const ScenePlug::ScenePath &path )
{
	ContextPtr context = new Context( *Context::current(), Context::Borrowed );
	Context::Scope scopedContext( context.get() );

	ScenePlug::ScenePath p; p.reserve( path.size() );
	for( ScenePlug::ScenePath::const_iterator it = path.begin(), eIt = path.end(); it != eIt; ++it )
	{
		context->set( ScenePlug::scenePathContextName, p );
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

namespace
{

/// \todo If we find similar usage patterns, we could make a parallelTraverse()
/// method in SceneAlgo.h. This would hide the details of traversing using tasks,
/// simply calling a functor in the right context for each location in the scene.
class MatchingPathsTask : public tbb::task
{

	public :

		typedef tbb::spin_mutex PathMatcherMutex;

		MatchingPathsTask(
			const Gaffer::IntPlug *filter,
			const ScenePlug *scene,
			const Gaffer::Context *context,
			PathMatcherMutex &pathMatcherMutex,
			PathMatcher &pathMatcher
		)
			:	m_filter( filter ), m_scene( scene ), m_context( context ), m_pathMatcherMutex( pathMatcherMutex ), m_pathMatcher( pathMatcher )
		{
		}

		virtual ~MatchingPathsTask()
		{
		}

		virtual task *execute()
		{

			ContextPtr context = new Context( *m_context, Context::Borrowed );
			context->set( ScenePlug::scenePathContextName, m_path );
			Context::Scope scopedContext( context.get() );

			const Filter::Result match = (Filter::Result)m_filter->getValue();
			if( match & Filter::ExactMatch )
			{
				PathMatcherMutex::scoped_lock lock( m_pathMatcherMutex );
				m_pathMatcher.addPath( m_path );
			}

			if( match & Filter::DescendantMatch )
			{
				ConstInternedStringVectorDataPtr childNamesData = m_scene->childNamesPlug()->getValue();
				const vector<InternedString> &childNames = childNamesData->readable();

				set_ref_count( 1 + childNames.size() );

				ScenePlug::ScenePath childPath = m_path;
				childPath.push_back( InternedString() ); // space for the child name
				for( vector<InternedString>::const_iterator it = childNames.begin(), eIt = childNames.end(); it != eIt; it++ )
				{
					childPath[m_path.size()] = *it;
					MatchingPathsTask *t = new( allocate_child() ) MatchingPathsTask( *this, childPath );
					spawn( *t );
				}
				wait_for_all();
			}

			return NULL;
		}

	protected :

		MatchingPathsTask( const MatchingPathsTask &other, const ScenePlug::ScenePath &path )
			:	m_filter( other.m_filter ),
				m_scene( other.m_scene ),
				m_context( other.m_context ),
				m_pathMatcherMutex( other.m_pathMatcherMutex ),
				m_pathMatcher( other.m_pathMatcher ),
				m_path( path )
		{
		}

	private :

		const IntPlug *m_filter;
		const ScenePlug *m_scene;
		const Context *m_context;
		PathMatcherMutex &m_pathMatcherMutex;
		PathMatcher &m_pathMatcher;
		ScenePlug::ScenePath m_path;

};

} // namespace

void GafferScene::matchingPaths( const Filter *filter, const ScenePlug *scene, PathMatcher &paths )
{
	matchingPaths( filter->matchPlug(), scene, paths );
}

void GafferScene::matchingPaths( const Gaffer::IntPlug *filterPlug, const ScenePlug *scene, PathMatcher &paths )
{
	ContextPtr context = new Context( *Context::current(), Context::Borrowed );
	Filter::setInputScene( context.get(), scene );
	MatchingPathsTask::PathMatcherMutex mutex;
	MatchingPathsTask *task = new( tbb::task::allocate_root() ) MatchingPathsTask( filterPlug, scene, context.get(), mutex, paths );
	tbb::task::spawn_root_and_wait( *task );
}

Imath::V2f GafferScene::shutter( const IECore::CompoundObject *globals )
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
		const V2fData *shutterData = globals->member<V2fData>( "option:render:shutter" );
		const V2f relativeShutter = shutterData ? shutterData->readable() : V2f( -0.25, 0.25 );
		shutter += relativeShutter;
	}

	return shutter;
}

IECore::TransformPtr GafferScene::transform( const ScenePlug *scene, const ScenePlug::ScenePath &path, const Imath::V2f &shutter, bool motionBlur )
{
	int numSamples = 1;
	if( motionBlur )
	{
		ConstCompoundObjectPtr attributes = scene->fullAttributes( path );
		const IntData *transformBlurSegmentsData = attributes->member<IntData>( "gaffer:transformBlurSegments" );
		numSamples = transformBlurSegmentsData ? transformBlurSegmentsData->readable() + 1 : 2;

		const BoolData *transformBlurData = attributes->member<BoolData>( "gaffer:transformBlur" );
		if( transformBlurData && !transformBlurData->readable() )
		{
			numSamples = 1;
		}
	}

	MatrixMotionTransformPtr result = new MatrixMotionTransform();
	ContextPtr transformContext = new Context( *Context::current(), Context::Borrowed );
	Context::Scope scopedContext( transformContext.get() );
	for( int i = 0; i < numSamples; i++ )
	{
		float frame = lerp( shutter[0], shutter[1], (float)i / std::max( 1, numSamples - 1 ) );
		transformContext->setFrame( frame );
		result->snapshots()[frame] = scene->fullTransform( path );
	}

	return result;
}

//////////////////////////////////////////////////////////////////////////
// Camera algo
//////////////////////////////////////////////////////////////////////////

namespace
{

void applyCameraGlobals( IECore::Camera *camera, const IECore::CompoundObject *globals )
{

	// apply the resolution, aspect ratio and crop window

	V2i resolution( 640, 480 );

	const Box2fData *cropWindowData = NULL;
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

		cropWindowData = globals->member<Box2fData>( "option:render:cropWindow" );
		if( cropWindowData )
		{
			camera->parameters()["cropWindow"] = cropWindowData->copy();
		}
	}

	camera->parameters()["resolution"] = new V2iData( resolution );

	// calculate an appropriate screen window

	camera->addStandardParameters();

	// apply overscan

	const BoolData *overscanData = globals->member<BoolData>( "option:render:overscan" );
	if( overscanData && overscanData->readable() && !resolutionOverrideData )
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

		// convert those offsets into pixel values

		V2i minPixelOffset(
			int(minOffset.x * (float)resolution.x),
			int(minOffset.y * (float)resolution.y)
		);

		V2i maxPixelOffset(
			int(maxOffset.x * (float)resolution.x),
			int(maxOffset.y * (float)resolution.y)
		);

		// recalculate original offsets to account for the rounding when
		// converting to integer pixel space

		minOffset = V2f(
			(float)minPixelOffset.x / (float)resolution.x,
			(float)minPixelOffset.y / (float)resolution.y
		);

		maxOffset = V2f(
			(float)maxPixelOffset.x / (float)resolution.x,
			(float)maxPixelOffset.y / (float)resolution.y
		);

		// adjust camera resolution and screen window appropriately

		V2i &cameraResolution = camera->parametersData()->member<V2iData>( "resolution" )->writable();
		Box2f &cameraScreenWindow = camera->parametersData()->member<Box2fData>( "screenWindow" )->writable();

		cameraResolution += minPixelOffset + maxPixelOffset;

		const Box2f originalScreenWindow = cameraScreenWindow;
		cameraScreenWindow.min -= originalScreenWindow.size() * minOffset;
		cameraScreenWindow.max += originalScreenWindow.size() * maxOffset;

		// adjust crop window too, if it was specified by the user

		if( cropWindowData )
		{
			Box2f &cameraCropWindow = camera->parametersData()->member<Box2fData>( "cropWindow" )->writable();
			// convert into original screen space
			Box2f cropWindowScreen(
				V2f(
					Imath::lerp( originalScreenWindow.min.x, originalScreenWindow.max.x, cameraCropWindow.min.x ),
					Imath::lerp( originalScreenWindow.max.y, originalScreenWindow.min.y, cameraCropWindow.max.y )
				),
				V2f(
					Imath::lerp( originalScreenWindow.min.x, originalScreenWindow.max.x, cameraCropWindow.max.x ),
					Imath::lerp( originalScreenWindow.max.y, originalScreenWindow.min.y, cameraCropWindow.min.y )
				)
			);
			// convert out of new screen space
			cameraCropWindow = Box2f(
				V2f(
					lerpfactor( cropWindowScreen.min.x, cameraScreenWindow.min.x, cameraScreenWindow.max.x ),
					lerpfactor( cropWindowScreen.max.y, cameraScreenWindow.max.y, cameraScreenWindow.min.y )
				),
				V2f(
					lerpfactor( cropWindowScreen.max.x, cameraScreenWindow.min.x, cameraScreenWindow.max.x ),
					lerpfactor( cropWindowScreen.min.y, cameraScreenWindow.max.y, cameraScreenWindow.min.y )
				)
			);
		}

	}

	// apply the shutter

	camera->parameters()["shutter"] = new V2fData( shutter( globals ) );

}

} // namespace

IECore::CameraPtr GafferScene::camera( const ScenePlug *scene, const IECore::CompoundObject *globals )
{
	ConstCompoundObjectPtr computedGlobals;
	if( !globals )
	{
		computedGlobals = scene->globalsPlug()->getValue();
		globals = computedGlobals.get();
	}

	if( const StringData *cameraPathData = globals->member<StringData>( "option:render:camera" ) )
	{
		ScenePlug::ScenePath cameraPath;
		ScenePlug::stringToPath( cameraPathData->readable(), cameraPath );
		return camera( scene, cameraPath, globals );
	}
	else
	{
		CameraPtr defaultCamera = new IECore::Camera();
		applyCameraGlobals( defaultCamera.get(), globals );
		return defaultCamera;
	}
}

IECore::CameraPtr GafferScene::camera( const ScenePlug *scene, const ScenePlug::ScenePath &cameraPath, const IECore::CompoundObject *globals )
{
	ConstCompoundObjectPtr computedGlobals;
	if( !globals )
	{
		computedGlobals = scene->globalsPlug()->getValue();
		globals = computedGlobals.get();
	}

	std::string cameraName;
	ScenePlug::pathToString( cameraPath, cameraName );

	if( !exists( scene, cameraPath ) )
	{
		throw IECore::Exception( "Camera \"" + cameraName + "\" does not exist" );
	}

	IECore::ConstCameraPtr constCamera = runTimeCast<const IECore::Camera>( scene->object( cameraPath ) );
	if( !constCamera )
	{
		std::string path; ScenePlug::pathToString( cameraPath, path );
		throw IECore::Exception( "Location \"" + cameraName + "\" is not a camera" );
	}

	IECore::CameraPtr camera = constCamera->copy();
	camera->setName( cameraName );

	const BoolData *cameraBlurData = globals->member<BoolData>( "option:render:cameraBlur" );
	const bool cameraBlur = cameraBlurData ? cameraBlurData->readable() : false;
	camera->setTransform( transform( scene, cameraPath, shutter( globals ), cameraBlur ) );

	applyCameraGlobals( camera.get(), globals );
	return camera;
}
