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
#include "IECore/WorldBlock.h"
#include "IECore/Light.h"
#include "IECore/Shader.h"
#include "IECore/AttributeBlock.h"
#include "IECore/Display.h"
#include "IECore/TransformBlock.h"
#include "IECore/CoordinateSystem.h"
#include "IECore/ClippingPlane.h"
#include "IECore/VisibleRenderable.h"
#include "IECore/Primitive.h"
#include "IECore/MotionBlock.h"

#include "Gaffer/Context.h"
#include "Gaffer/Metadata.h"

#include "GafferScene/RendererAlgo.h"
#include "GafferScene/PathMatcherData.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/SceneProcessor.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

void motionTimes( size_t segments, const V2f &shutter, std::set<float> &times )
{
	for( size_t i = 0; i<segments + 1; ++i )
	{
		times.insert( lerp( shutter[0], shutter[1], (float)i / (float)segments ) );
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// RendererAlgo implementation
//////////////////////////////////////////////////////////////////////////

namespace GafferScene
{

namespace RendererAlgo
{

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

void transformSamples( const ScenePlug *scene, size_t segments, const Imath::V2f &shutter, std::vector<Imath::M44f> &samples, std::set<float> &sampleTimes )
{
	// Static case

	if( !segments )
	{
		samples.push_back( scene->transformPlug()->getValue() );
		return;
	}

	// Motion case

	motionTimes( segments, shutter, sampleTimes );

	Context::EditableScope timeContext( Context::current() );

	bool moving = false;
	samples.reserve( sampleTimes.size() );
	for( std::set<float>::const_iterator it = sampleTimes.begin(), eIt = sampleTimes.end(); it != eIt; ++it )
	{
		timeContext.setFrame( *it );
		const M44f m = scene->transformPlug()->getValue();
		if( !moving && !samples.empty() && m != samples.front() )
		{
			moving = true;
		}
		samples.push_back( m );
	}

	if( !moving )
	{
		samples.resize( 1 );
		sampleTimes.clear();
	}
}

void objectSamples( const ScenePlug *scene, size_t segments, const Imath::V2f &shutter, std::vector<IECore::ConstVisibleRenderablePtr> &samples, std::set<float> &sampleTimes )
{

	// Static case

	if( !segments )
	{
		ConstObjectPtr object = scene->objectPlug()->getValue();
		if( const VisibleRenderable *renderable = runTimeCast<const VisibleRenderable>( object.get() ) )
		{
			samples.push_back( renderable );
		}
		return;
	}

	// Motion case

	motionTimes( segments, shutter, sampleTimes );

	Context::EditableScope timeContext( Context::current() );

	bool moving = false;
	MurmurHash lastHash;
	samples.reserve( sampleTimes.size() );
	for( std::set<float>::const_iterator it = sampleTimes.begin(), eIt = sampleTimes.end(); it != eIt; ++it )
	{
		timeContext.setFrame( *it );

		const MurmurHash objectHash = scene->objectPlug()->hash();
		ConstObjectPtr object = scene->objectPlug()->getValue( &objectHash );

		if( const Primitive *primitive = runTimeCast<const Primitive>( object.get() ) )
		{
			// We can support multiple samples for these, so check to see
			// if we actually have something moving.
			if( !moving && !samples.empty() && objectHash != lastHash )
			{
				moving = true;
			}
			samples.push_back( primitive );
			lastHash = objectHash;
		}
		else if( const VisibleRenderable *renderable = runTimeCast< const VisibleRenderable >( object.get() ) )
		{
			// We can't motion blur these chappies, so just take the one
			// sample.
			samples.push_back( renderable );
			break;
		}
		else
		{
			// We don't even know what these chappies are, so
			// don't take any samples at all.
			break;
		}
	}

	if( !moving )
	{
		samples.resize( std::min<size_t>( samples.size(), 1 ) );
		sampleTimes.clear();
	}
}

} // namespace RendererAlgo

} // namespace GafferScene

//////////////////////////////////////////////////////////////////////////
// Adaptor registry
//////////////////////////////////////////////////////////////////////////

namespace
{

typedef boost::container::flat_map<string, GafferScene::RendererAlgo::Adaptor> Adaptors;

Adaptors &adaptors()
{
	static Adaptors a;
	return a;
}

} // namespace

namespace GafferScene
{

namespace RendererAlgo
{

void registerAdaptor( const std::string &name, Adaptor adaptor )
{
	adaptors()[name] = adaptor;
}

void deregisterAdaptor( const std::string &name )
{
	adaptors().erase( name );
}

SceneProcessorPtr createAdaptors()
{
	SceneProcessorPtr result = new SceneProcessor;

	ScenePlug *in = result->inPlug();

	const Adaptors &a = adaptors();
	for( Adaptors::const_iterator it = a.begin(), eIt = a.end(); it != eIt; ++it )
	{
		SceneProcessorPtr adaptor = it->second();
		result->addChild( adaptor );
		adaptor->inPlug()->setInput( in );
		in = adaptor->outPlug();
	}

	result->outPlug()->setInput( in );
	return result;
}

} // namespace RendererAlgo

} // namespace GafferScene
