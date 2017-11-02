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

#ifndef GAFFERSCENE_RENDERERALGO_H
#define GAFFERSCENE_RENDERERALGO_H

#include <functional>

#include "IECore/CompoundObject.h"
#include "IECore/VisibleRenderable.h"

#include "GafferScene/ScenePlug.h"

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( SceneProcessor )

namespace RendererAlgo
{

/// Creates the directories necessary to receive the Displays in globals.
void createDisplayDirectories( const IECore::CompoundObject *globals );

/// Samples the local transform from the current location in preparation for output to the renderer.
/// If segments is 0, the transform is sampled at the time from the current context. If it is non-zero then
/// the sampling is performed evenly across the shutter interval, which should have been obtained via
/// SceneAlgo::shutter(). If all samples turn out to be identical, they will be collapsed automatically
/// into a single sample. The sampleTimes container is only filled if there is more than one sample.
void transformSamples( const ScenePlug *scene, size_t segments, const Imath::V2f &shutter, std::vector<Imath::M44f> &samples, std::set<float> &sampleTimes );

/// Samples the object from the current location in preparation for output to the renderer. Sampling parameters
/// are as for the transformSamples() method. Multiple samples will only be generated for Primitives, since other
/// object types cannot be interpolated anyway.
void objectSamples( const ScenePlug *scene, size_t segments, const Imath::V2f &shutter, std::vector<IECore::ConstVisibleRenderablePtr> &samples, std::set<float> &sampleTimes );

/// Function to return a SceneProcessor used to adapt the
/// scene for rendering.
typedef std::function<SceneProcessorPtr ()> Adaptor;
/// Registers an adaptor.
void registerAdaptor( const std::string &name, Adaptor adaptor );
/// Removes a previously registered adaptor.
void deregisterAdaptor( const std::string &name );
/// Returns a SceneProcessor that will apply all the currently
/// registered adaptors.
SceneProcessorPtr createAdaptors();

} // namespace RendererAlgo

} // namespace GafferScene

#endif // GAFFERSCENE_RENDERERALGO_H
