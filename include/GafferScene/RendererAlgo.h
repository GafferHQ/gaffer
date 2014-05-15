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

#include "GafferScene/ScenePlug.h"

namespace GafferScene
{

/// Outputs an entire scene, using a SceneProcedural for the main body of the world.
/// Individual parts of a scene may be output more specifically using the methods below.
void outputScene( const ScenePlug *scene, IECore::Renderer *renderer );

/// Outputs the renderer options specified by the globals.
void outputOptions( const IECore::CompoundObject *globals, IECore::Renderer *renderer );

/// Outputs the camera specified by the globals.
void outputCamera( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer );

/// Outputs the lights from the scene.
void outputLights( const ScenePlug *scene, const IECore::CompoundObject *globals, IECore::Renderer *renderer );

/// Creates the directories necessary to receive the Displays in globals.
void createDisplayDirectories( const IECore::CompoundObject *globals );

/// Calculates the shutter specified by the globals.
Imath::V2f shutter( const IECore::CompoundObject *globals );

/// Calculates the full transform for the specified location in the scene, sampling motion according to the attributes at that
/// location if motionBlur is true.
IECore::TransformPtr transform( const ScenePlug *scene, const ScenePlug::ScenePath &path, const Imath::V2f &shutter, bool motionBlur );

} // namespace GafferScene

#endif // GAFFERSCENE_RENDERERALGO_H
