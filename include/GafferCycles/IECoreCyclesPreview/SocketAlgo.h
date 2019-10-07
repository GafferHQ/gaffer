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

#ifndef IECORECYCLES_SOCKETALGO_H
#define IECORECYCLES_SOCKETALGO_H

#include "GafferCycles/IECoreCyclesPreview/Export.h"

#include "IECore/Export.h"

#include "IECore/CompoundData.h"

// Cycles
#include "graph/node.h"
#include "graph/node_type.h"
#include "util/util_transform.h"

namespace IECoreCycles
{

namespace SocketAlgo
{

// Convenience functions to convert types.
IECORECYCLES_API ccl::float2 setVector( const Imath::V2f &vector );
IECORECYCLES_API ccl::float3 setVector( const Imath::V3f &vector );
IECORECYCLES_API ccl::float3 setColor( const Imath::Color3f &color );
IECORECYCLES_API ccl::float3 setColor( const Imath::Color4f &color );
IECORECYCLES_API float setAlpha( const Imath::Color4f &color );
IECORECYCLES_API ccl::float4 setQuaternion( const Imath::Quatf &quat );
IECORECYCLES_API ccl::Transform setTransform( const Imath::M44d &matrix );
IECORECYCLES_API ccl::Transform setTransform( const Imath::M44f &matrix );

IECORECYCLES_API Imath::V2f getVector( const ccl::float2 vector );
IECORECYCLES_API Imath::V3f getVector( const ccl::float3 vector );
IECORECYCLES_API Imath::Color4f getColor( const ccl::float3 color );
IECORECYCLES_API Imath::Color4f getColor( const ccl::float4 color );
IECORECYCLES_API Imath::Quatf getQuaternion( const ccl::float4 quat );
IECORECYCLES_API Imath::M44f getTransform( const ccl::Transform transform );

// Setting sockets onto cycles nodes.
IECORECYCLES_API void setSocket( ccl::Node *node, const ccl::SocketType *socket, const IECore::Data *value );
IECORECYCLES_API void setSocket( ccl::Node *node, const std::string &name, const IECore::Data *value );
IECORECYCLES_API void setSockets( ccl::Node *node, const IECore::CompoundDataMap &values );

// Getting data from cycles nodes via sockets.
IECORECYCLES_API IECore::DataPtr getSocket( const ccl::Node *node, const ccl::SocketType *socket );
IECORECYCLES_API IECore::DataPtr getSocket( const ccl::Node *node, const std::string &name );

} // namespace SocketAlgo

} // namespace IECoreCycles

#endif // IECORECYCLES_SOCKETALGO_H
