//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "IECore/MessageHandler.h"

#include "GafferScene/PathMatcherData.h"
#include "IECore/TypedData.inl"

namespace IECore
{

IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( IECore::PathMatcherData, GafferScene::PathMatcherDataTypeId )

template<>
void PathMatcherData::save( SaveContext *context ) const
{
	Data::save( context );
	msg( Msg::Warning, "PathMatcherData::save", "Not implemented" );
}

/// Here we specialise the TypedData::load() method to correctly load the data produced by save().
template<>
void PathMatcherData::load( LoadContextPtr context )
{
	Data::load( context );
	msg( Msg::Warning, "PathMatcherData::load", "Not implemented" );
}

/// Here we specialise the SimpleDataHolder::hash() method to appropriately add our internal data to the hash.
template<>
void SharedDataHolder<GafferScene::PathMatcher>::hash( MurmurHash &h ) const
{
	msg( Msg::Warning, "SharedDataHolder<GafferScene::PathMatcher>::hash", "Not implemented" );
}

template class TypedData<GafferScene::PathMatcher>;

} // namespace IECore
