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

#include "boost/filesystem.hpp"
#include "boost/algorithm/string/predicate.hpp"

#include "IECore/PreWorldRenderable.h"
#include "IECore/Camera.h"
#include "IECore/MatrixMotionTransform.h"
#include "IECore/WorldBlock.h"
#include "IECore/Light.h"
#include "IECore/AttributeBlock.h"
#include "IECore/Display.h"
#include "IECore/TransformBlock.h"

#include "Gaffer/Context.h"

#include "GafferScene/RendererAlgo.h"
#include "GafferScene/SceneProcedural.h"
#include "GafferScene/PathMatcherData.h"
#include "GafferScene/SceneAlgo.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;

namespace GafferScene
{

void outputScene( const ScenePlug *scene, IECore::Renderer *renderer )
{
	ConstCompoundObjectPtr globals = scene->globalsPlug()->getValue();
	outputOptions( globals.get(), renderer );
	outputOutputs( globals.get(), renderer );
	outputCamera( scene, globals.get(), renderer );
	{
		WorldBlock world( renderer );

		outputGlobalAttributes( globals.get(), renderer );
		outputCoordinateSystems( scene, globals.get(), renderer );
		outputLights( scene, globals.get(), renderer );

		SceneProceduralPtr proc = new SceneProcedural( scene, Context::current() );
		renderer->procedural( proc );
	}
}

void outputOutputs( const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	CompoundObject::ObjectMap::const_iterator it, eIt;
	for( it = globals->members().begin(), eIt = globals->members().end(); it != eIt; it++ )
	{
		if( !boost::starts_with( it->first.c_str(), "output:" ) )
		{
			continue;
		}
		if( const Display *d = runTimeCast<Display>( it->second.get() ) )
		{
			d->render( renderer );
		}
		else
		{
			throw IECore::Exception( "Global \"" + it->first.string() + "\" is not an IECore::Display" );
		}
	}
}

void outputOptions( const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	CompoundObject::ObjectMap::const_iterator it, eIt;
	for( it = globals->members().begin(), eIt = globals->members().end(); it != eIt; it++ )
	{
		if( !boost::starts_with( it->first.c_str(), "option:" ) )
		{
			continue;
		}
		if( const Data *d = runTimeCast<Data>( it->second.get() ) )
		{
			renderer->setOption( it->first.c_str() + 7, d );
		}
		else
		{
			throw IECore::Exception( "Global \"" + it->first.string() + "\" is not IECore::Data" );
		}
	}
}

void outputCamera( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	// get the camera from the scene

	const StringData *cameraPathData = globals->member<StringData>( "option:render:camera" );
	IECore::CameraPtr camera = 0;
	if( cameraPathData )
	{
		ScenePlug::ScenePath cameraPath;
		ScenePlug::stringToPath( cameraPathData->readable(), cameraPath );
		if( !exists( scene, cameraPath ) )
		{
			throw IECore::Exception( "Camera \"" + cameraPathData->readable() + "\" does not exist" );
		}

		IECore::ConstCameraPtr constCamera = runTimeCast<const IECore::Camera>( scene->object( cameraPath ) );
		if( !constCamera )
		{
			throw IECore::Exception( "Location \"" + cameraPathData->readable() + "\" is not a camera" );
		}

		camera = constCamera->copy();
		const BoolData *cameraBlurData = globals->member<BoolData>( "option:render:cameraBlur" );
		const bool cameraBlur = cameraBlurData ? cameraBlurData->readable() : false;
		camera->setTransform( transform( scene, cameraPath, shutter( globals ), cameraBlur ) );
	}

	if( !camera )
	{
		camera = new IECore::Camera();
	}

	// apply the resolution, aspect ratio and crop window

	V2i resolution( 640, 480 );
	if( const V2iData *resolutionData = globals->member<V2iData>( "option:render:resolution" ) )
	{
		resolution = resolutionData->readable();
	}

	if( const FloatData *resolutionMultiplierData = globals->member<FloatData>( "option:render:resolutionMultiplier" ) )
	{
		resolution.x = int((float)resolution.x * resolutionMultiplierData->readable());
		resolution.y = int((float)resolution.y * resolutionMultiplierData->readable());
	}

	camera->parameters()["resolution"] = new V2iData( resolution );

	const FloatData *pixelAspectRatioData = globals->member<FloatData>( "option:render:pixelAspectRatio" );
	if( pixelAspectRatioData )
	{
		camera->parameters()["pixelAspectRatio"] = pixelAspectRatioData->copy();
	}

	const Box2fData *cropWindowData = globals->member<Box2fData>( "option:render:cropWindow" );
	if( cropWindowData )
	{
		camera->parameters()["cropWindow"] = cropWindowData->copy();
	}

	// calculate an appropriate screen window

	camera->addStandardParameters();

	// apply overscan
	
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

	// and output

	camera->render( renderer );

}

void outputGlobalAttributes( const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	CompoundObject::ObjectMap::const_iterator it, eIt;
	for( it = globals->members().begin(), eIt = globals->members().end(); it != eIt; it++ )
	{
		if( !boost::starts_with( it->first.c_str(), "attribute:" ) )
		{
			continue;
		}
		if( const Data *d = runTimeCast<Data>( it->second.get() ) )
		{
			renderer->setAttribute( it->first.c_str() + 10, d );
		}
		else
		{
			throw IECore::Exception( "Global \"" + it->first.string() + "\" is not IECore::Data" );
		}
	}
}

void outputLights( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	const CompoundData *sets = globals->member<CompoundData>( "gaffer:sets" );
	if( !sets )
	{
		return;
	}

	const PathMatcherData *lightSet = sets->member<PathMatcherData>( "__lights" );
	if( !lightSet )
	{
		return;
	}

	vector<string> paths;
	lightSet->readable().paths( paths );
	for( vector<string>::const_iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
	{
		/// \todo We should be able to get paths out of the PathMatcher in
		/// the first place, rather than have to convert from strings.
		ScenePlug::ScenePath path;
		ScenePlug::stringToPath( *it, path );
		outputLight( scene, path, renderer );
	}
}

bool outputLight( const ScenePlug *scene, const ScenePlug::ScenePath &path, IECore::Renderer *renderer )
{
	IECore::ConstLightPtr constLight = runTimeCast<const IECore::Light>( scene->object( path ) );
	if( !constLight )
	{
		return false;
	}

	ConstCompoundObjectPtr attributes = scene->fullAttributes( path );
	const BoolData *visibilityData = attributes->member<BoolData>( "scene:visible" );
	if( visibilityData && !visibilityData->readable() )
	{
		return false;
	}

	M44f transform = scene->fullTransform( path );

	std::string lightHandle;
	ScenePlug::pathToString( path, lightHandle );

	LightPtr light = constLight->copy();
	light->setHandle( lightHandle );

	{
		AttributeBlock attributeBlock( renderer );

		renderer->setAttribute( "name", new StringData( lightHandle ) );

		CompoundObject::ObjectMap::const_iterator aIt, aeIt;
		for( aIt = attributes->members().begin(), aeIt = attributes->members().end(); aIt != aeIt; aIt++ )
		{
			if( const Data *attribute = runTimeCast<const Data>( aIt->second.get() ) )
			{
				renderer->setAttribute( aIt->first.string(), attribute );
			}
		}

		renderer->concatTransform( transform );
		light->render( renderer );
	}

	renderer->illuminate( lightHandle, true );

	return true;
}

void outputCoordinateSystems( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer )
{
	const CompoundData *sets = globals->member<CompoundData>( "gaffer:sets" );
	if( !sets )
	{
		return;
	}

	const PathMatcherData *coordinateSystemSet = sets->member<PathMatcherData>( "__coordinateSystems" );
	if( !coordinateSystemSet )
	{
		return;
	}

	vector<string> paths;
	coordinateSystemSet->readable().paths( paths );
	for( vector<string>::const_iterator it = paths.begin(), eIt = paths.end(); it != eIt; ++it )
	{
		/// \todo We should be able to get paths out of the PathMatcher in
		/// the first place, rather than have to convert from strings.
		ScenePlug::ScenePath path;
		ScenePlug::stringToPath( *it, path );
		outputCoordinateSystem( scene, path, renderer );
	}
}

bool outputCoordinateSystem( const ScenePlug *scene, const ScenePlug::ScenePath &path, IECore::Renderer *renderer )
{
	IECore::ConstCoordinateSystemPtr constCoordinateSystem = runTimeCast<const IECore::CoordinateSystem>( scene->object( path ) );
	if( !constCoordinateSystem )
	{
		return false;
	}

	ConstCompoundObjectPtr attributes = scene->fullAttributes( path );
	const BoolData *visibilityData = attributes->member<BoolData>( "scene:visible" );
	if( visibilityData && !visibilityData->readable() )
	{
		return false;
	}

	const M44f transform = scene->fullTransform( path );

	std::string coordinateSystemName;
	ScenePlug::pathToString( path, coordinateSystemName );

	CoordinateSystemPtr coordinateSystem = constCoordinateSystem->copy();
	coordinateSystem->setName( coordinateSystemName );

	{
		TransformBlock transformBlock( renderer );
		renderer->concatTransform( transform );
		coordinateSystem->render( renderer );
	}

	return true;
}

void createDisplayDirectories( const IECore::CompoundObject *globals )
{
	CompoundObject::ObjectMap::const_iterator it, eIt;
	for( it = globals->members().begin(), eIt = globals->members().end(); it != eIt; it++ )
	{
		if( const Display *d = runTimeCast<Display>( it->second.get() ) )
		{
			boost::filesystem::path fileName( d->getName() );
			boost::filesystem::path directory = fileName.parent_path();
			if( !directory.empty() )
			{
				boost::filesystem::create_directories( directory );
			}
		}
	}
}

Imath::V2f shutter( const IECore::CompoundObject *globals )
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

IECore::TransformPtr transform( const ScenePlug *scene, const ScenePlug::ScenePath &path, const Imath::V2f &shutter, bool motionBlur )
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

} // namespace GafferScene
