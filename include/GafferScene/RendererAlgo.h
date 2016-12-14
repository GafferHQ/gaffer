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

#include "IECore/Renderer.h"
#include "IECore/CompoundObject.h"
#include "IECore/Transform.h"
#include "IECore/VisibleRenderable.h"

#include "GafferScene/ScenePlug.h"

namespace GafferScene
{

namespace RendererAlgo
{

/// Outputs an entire scene, using a SceneProcedural for the main body of the world.
/// Individual parts of a scene may be output more specifically using the methods below.
void outputScene( const ScenePlug *scene, IECore::Renderer *renderer );

/// Outputs the output declarations from the globals.
void outputOutputs( const IECore::CompoundObject *globals, IECore::Renderer *renderer );

/// Outputs the renderer options specified by the globals.
void outputOptions( const IECore::CompoundObject *globals, IECore::Renderer *renderer );

/// Outputs all the cameras from the scene, or a default camera if none exist.
void outputCameras( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer );

/// Outputs the primary camera specified by the globals, or a default camera if none is specified.
void outputCamera( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer );

/// Outputs the camera from the specified location.
void outputCamera( const ScenePlug *scene, const ScenePlug::ScenePath &cameraPath, const IECore::CompoundObject *globals, IECore::Renderer *renderer );

/// Outputs all the visible clipping planes from the scene.
void outputClippingPlanes( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer );

/// Outputs a single clipping plane from the scene. Returns true for success, and false if no clipping plane
/// was found or if it was invisible.
bool outputClippingPlane( const ScenePlug *scene, const ScenePlug::ScenePath &path, IECore::Renderer *renderer );

/// Outputs the attributes stored in the globals.
void outputGlobalAttributes( const IECore::CompoundObject *globals, IECore::Renderer *renderer );

/// Outputs all the visible lights from the scene.
void outputLights( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer );

/// Outputs a single light from the scene. Returns true for success, and false if no light was found or if it
/// was invisible.
bool outputLight( const ScenePlug *scene, const ScenePlug::ScenePath &path, IECore::Renderer *renderer );

/// Outputs all the visible coordinate systems from the scene.
void outputCoordinateSystems( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer );

/// Outputs a single coordinate system from the scene. Returns true for success, and false if no coordinate system
/// was found or if it was invisible.
bool outputCoordinateSystem( const ScenePlug *scene, const ScenePlug::ScenePath &path, IECore::Renderer *renderer );

/// Creates the directories necessary to receive the Displays in globals.
void createDisplayDirectories( const IECore::CompoundObject *globals );

/// Outputs the specified attributes, which are expected to have been
/// retrieved from ScenePlug:attributesPlug().
void outputAttributes( const IECore::CompoundObject *attributes, IECore::Renderer *renderer );

/// Samples the local transform from the current location in preparation for output to the renderer.
/// If segments is 0, the transform is sampled at the time from the current context. If it is non-zero then
/// the sampling is performed evenly across the shutter interval, which should have been obtained via
/// SceneAlgo::shutter(). If all samples turn out to be identical, they will be collapsed automatically
/// into a single sample. The sampleTimes container is only filled if there is more than one sample.
void transformSamples( const ScenePlug *scene, size_t segments, const Imath::V2f &shutter, std::vector<Imath::M44f> &samples, std::set<float> &sampleTimes );

/// Outputs the local transform for the current location, using transformSamples() to generate the samples.
void outputTransform( const ScenePlug *scene, IECore::Renderer *renderer, size_t segments = 0, const Imath::V2f &shutter = Imath::V2i( 0 ) );

/// Samples the object from the current location in preparation for output to the renderer. Sampling parameters
/// are as for the transformSamples() method. Multiple samples will only be generated for Primitives, since other
/// object types cannot be interpolated anyway.
void objectSamples( const ScenePlug *scene, size_t segments, const Imath::V2f &shutter, std::vector<IECore::ConstVisibleRenderablePtr> &samples, std::set<float> &sampleTimes );

/// Outputs the object for the current location, using objectSamples() to generate the samples.
void outputObject( const ScenePlug *scene, IECore::Renderer *renderer, size_t segments = 0, const Imath::V2f &shutter = Imath::V2i( 0 ) );

} // namespace RendererAlgo

/// \todo Remove this temporary backwards compatibility.
using namespace RendererAlgo;

} // namespace GafferScene

#endif // GAFFERSCENE_RENDERERALGO_H
