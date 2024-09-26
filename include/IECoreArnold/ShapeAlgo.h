//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#pragma once

#include "IECoreArnold/Export.h"

#include "IECoreScene/Primitive.h"

#include "ai_nodes.h"

namespace IECoreArnold
{

namespace ShapeAlgo
{

IECOREARNOLD_API void convertP( const IECoreScene::Primitive *primitive, AtNode *shape, const AtString name, const std::string &messageContext = "ShapeAlgo::convertP" );
IECOREARNOLD_API void convertP( const std::vector<const IECoreScene::Primitive *> &samples, AtNode *shape, const AtString name, const std::string &messageContext = "ShapeAlgo::convertP" );

IECOREARNOLD_API void convertRadius( const IECoreScene::Primitive *primitive, AtNode *shape, const std::string &messageContext = "ShapeAlgo::convertRadius" );
IECOREARNOLD_API void convertRadius( const std::vector<const IECoreScene::Primitive *> &samples, AtNode *shape, const std::string &messageContext = "ShapeAlgo::convertRadius" );

IECOREARNOLD_API void convertPrimitiveVariable( const IECoreScene::Primitive *primitive, const IECoreScene::PrimitiveVariable &primitiveVariable, AtNode *shape, const AtString name, const std::string &messageContext = "ShapeAlgo::convertPrimitiveVariable" );
/// Converts primitive variables from primitive into user parameters on shape, ignoring any variables
/// whose names are present in the ignore array.
IECOREARNOLD_API void convertPrimitiveVariables( const IECoreScene::Primitive *primitive, AtNode *shape, const char **namesToIgnore=nullptr, const std::string &messageContext = "ShapeAlgo::convertPrimitiveVariables" );

} // namespace ShapeAlgo

} // namespace IECoreArnold
