//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "IECore/PreWorldRenderable.h"
#include "IECore/Camera.h"
#include "IECore/MatrixMotionTransform.h"
#include "IECore/WorldBlock.h"
#include "IECore/Light.h"
#include "IECore/AttributeBlock.h"

#include "Gaffer/Context.h"

#include "GafferScene/Render.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/SceneProcedural.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Render );

size_t Render::g_firstPlugIndex = 0;

Render::Render( const std::string &name )
	:	Node( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "in" ) );
}

Render::~Render()
{
}

ScenePlug *Render::inPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *Render::inPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

void Render::outputScene( const ScenePlug *scene, IECore::Renderer *renderer ) const
{
	ConstCompoundObjectPtr globals = scene->globalsPlug()->getValue();
	outputOptions( globals, renderer );
	outputCamera( scene, globals, renderer );
	{
		WorldBlock world( renderer );
		
		outputLights( scene, globals, renderer ); 

		SceneProceduralPtr proc = new SceneProcedural( scene, Context::current() );
		renderer->procedural( proc );
	}
}

void Render::outputOptions( const IECore::CompoundObject *globals, IECore::Renderer *renderer ) const
{
	CompoundObject::ObjectMap::const_iterator it, eIt;
	for( it = globals->members().begin(), eIt = globals->members().end(); it != eIt; it++ )
	{
		if( const PreWorldRenderable *r = runTimeCast<PreWorldRenderable>( it->second.get() ) )
		{
			r->render( renderer );
		}
		else if( const Data *d = runTimeCast<Data>( it->second.get() ) )
		{
			renderer->setOption( it->first, d );
		}
	}
}

void Render::outputCamera( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer ) const
{
	// get the camera from the scene
	
	const StringData *cameraPathData = globals->member<StringData>( "render:camera" );
	IECore::CameraPtr camera = 0;
	if( cameraPathData )
	{
		ScenePlug::ScenePath cameraPath;
		ScenePlug::stringToPath( cameraPathData->readable(), cameraPath );
		
		IECore::ConstCameraPtr constCamera = runTimeCast<const IECore::Camera>( scene->object( cameraPath ) );
		if( constCamera )
		{
			camera = constCamera->copy();
			const BoolData *cameraBlurData = globals->member<BoolData>( "render:cameraBlur" );
			const bool cameraBlur = cameraBlurData ? cameraBlurData->readable() : false;
			camera->setTransform( transform( scene, cameraPath, shutter( globals ), cameraBlur ) );
		}
	}
	
	if( !camera )
	{
		camera = new IECore::Camera();
	}
	
	// apply the resolution
	
	const V2iData *resolutionData = globals->member<V2iData>( "render:resolution" );
	if( resolutionData )
	{
		camera->parameters()["resolution"] = resolutionData->copy();
	}
	
	camera->addStandardParameters();
	
	// apply the shutter
	
	camera->parameters()["shutter"] = new V2fData( shutter( globals ) );
	
	// and output
	
	camera->render( renderer );
	
}

void Render::outputLights( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer ) const
{
	const CompoundData *forwardDeclarations = globals->member<CompoundData>( "gaffer:forwardDeclarations" );
	if( !forwardDeclarations )
	{
		return;
	}

	CompoundDataMap::const_iterator it, eIt;
	for( it = forwardDeclarations->readable().begin(), eIt = forwardDeclarations->readable().end(); it != eIt; it++ )
	{
		const CompoundData *declaration = runTimeCast<const CompoundData>( it->second.get() );
		if( !declaration )
		{
			continue;
		}
		
		const IECore::TypeId type = (IECore::TypeId)declaration->member<IntData>( "type", true )->readable();
		if( type != IECore::LightTypeId )
		{
			continue;
		}
		
		ScenePlug::ScenePath path;
		ScenePlug::stringToPath( it->first.string(), path );
		
		IECore::ConstLightPtr constLight = runTimeCast<const IECore::Light>( scene->object( path ) );
		if( !constLight )
		{
			continue;
		}
		
		ConstCompoundObjectPtr attributes = scene->fullAttributes( path );
		const BoolData *visibilityData = attributes->member<BoolData>( "gaffer:visibility" );
		if( visibilityData && !visibilityData->readable() )
		{
			continue;
		}
		
		M44f transform = scene->fullTransform( path );
		
		LightPtr light = constLight->copy();
		light->setHandle( it->first.string() );
		
		{
			AttributeBlock attributeBlock( renderer );
		
			renderer->setAttribute( "name", new StringData( it->first ) );
		
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
		
		renderer->illuminate( light->getHandle(), true );
	}
}

Imath::V2f Render::shutter( const IECore::CompoundObject *globals ) const
{
	const BoolData *cameraBlurData = globals->member<BoolData>( "render:cameraBlur" );
	const bool cameraBlur = cameraBlurData ? cameraBlurData->readable() : false;
	
	const BoolData *transformBlurData = globals->member<BoolData>( "render:transformBlur" );
	const bool transformBlur = transformBlurData ? transformBlurData->readable() : false;
	
	const BoolData *deformationBlurData = globals->member<BoolData>( "render:deformationBlur" );
	const bool deformationBlur = deformationBlurData ? deformationBlurData->readable() : false;
	
	V2f shutter( Context::current()->getFrame() );
	if( cameraBlur || transformBlur || deformationBlur )
	{
		const V2fData *shutterData = globals->member<V2fData>( "render:shutter" );
		const V2f relativeShutter = shutterData ? shutterData->readable() : V2f( -0.25, 0.25 );
		shutter += relativeShutter;
	}
	
	return shutter;
}

IECore::TransformPtr Render::transform( const ScenePlug *scene, const ScenePlug::ScenePath &path, const Imath::V2f &shutter, bool motionBlur ) const
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
	ContextPtr transformContext = new Context( *Context::current() );
	Context::Scope scopedContext( transformContext );
	for( int i = 0; i < numSamples; i++ )
	{
		float frame = lerp( shutter[0], shutter[1], (float)i / std::max( 1, numSamples - 1 ) );
		transformContext->setFrame( frame );
		result->snapshots()[frame] = scene->fullTransform( path );
	}

	return result;
}
