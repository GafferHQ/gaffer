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

#include "boost/python.hpp"

#include "RendererAlgoBinding.h"

#include "GafferScene/RendererAlgo.h"
#include "GafferScene/SceneProcessor.h"

#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace GafferScene;

namespace
{

list objectSamplesWrapper( const Gaffer::ObjectPlug &objectPlug, const std::vector<float> &sampleTimes, bool copy )
{
	std::vector<IECore::ConstObjectPtr> samples;
	{
		IECorePython::ScopedGILRelease gilRelease;
		RendererAlgo::objectSamples( &objectPlug, sampleTimes, samples );
	}

	list pythonSamples;
	for( auto &s : samples )
	{
		if( copy )
		{
			pythonSamples.append( s->copy() );
		}
		else
		{
			pythonSamples.append( boost::const_pointer_cast<IECore::Object>( s ) );
		}
	}

	return pythonSamples;
}

void outputCamerasWrapper( const ScenePlug &scene, const IECore::CompoundObject &globals, const RendererAlgo::RenderSets &renderSets, IECoreScenePreview::Renderer &renderer )
{
	IECorePython::ScopedGILRelease gilRelease;
	RendererAlgo::outputCameras( &scene, &globals, renderSets, &renderer );
}

} // namespace

namespace GafferSceneModule
{

void bindRendererAlgo()
{

	object module( borrowed( PyImport_AddModule( "GafferScene.RendererAlgo" ) ) );
	scope().attr( "RendererAlgo" ) = module;
	scope moduleScope( module );

	def( "objectSamples", &objectSamplesWrapper, ( arg( "objectPlug" ), arg( "sampleTimes" ), arg( "_copy" ) = true ) );

	class_<RendererAlgo::RenderSets, boost::noncopyable>( "RenderSets" )
		.def( init<const ScenePlug *>() )
	;

	def( "outputCameras", &outputCamerasWrapper );

}

} // namespace GafferSceneModule
