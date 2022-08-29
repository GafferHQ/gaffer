//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#ifndef IECORECYCLES_ATTRIBUTEALGO_H
#define IECORECYCLES_ATTRIBUTEALGO_H

#include "GafferCycles/IECoreCyclesPreview/Export.h"

#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/Primitive.h"

// Cycles
IECORE_PUSH_DEFAULT_VISIBILITY
#include "scene/attribute.h"
#include "scene/mesh.h"
IECORE_POP_DEFAULT_VISIBILITY

namespace IECoreCycles
{

namespace AttributeAlgo
{
IECORECYCLES_API ccl::TypeDesc typeDesc( IECore::TypeId dataType );
IECORECYCLES_API ccl::TypeDesc typeFromGeometricDataInterpretation( IECore::GeometricData::Interpretation dataType );

/// Converts a primitive variable to a ccl::Attribute inside of a ccl::AttributeSet
IECORECYCLES_API void convertPrimitiveVariable( const std::string &name, const IECoreScene::PrimitiveVariable &primitiveVariable, ccl::AttributeSet &attributes );
/// Compute tangents.
IECORECYCLES_API void computeTangents( ccl::Mesh *cmesh, const IECoreScene::MeshPrimitive *mesh, bool needsign );

} // namespace AttributeAlgo

} // namespace IECoreCycles

#endif // IECORECYCLES_ATTRIBUTEALGO_H
