//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#pragma once

#include "Gaffer/Export.h"

#include "IECore/PathMatcher.h"
#include "IECore/VectorTypedData.h"

#include <string>

namespace Gaffer::SetExpressionAlgo
{

/// Evaluation
/// ==========

/// Interface for providing sets to `evaluateSetExpression` and `setExpressionHash`.
struct SetProvider
{
	/// Must be implemented to provide the names of all available sets.
	virtual IECore::ConstInternedStringVectorDataPtr setNames() const = 0;
	/// Must be implemented to provide the contents of set `setName`.
	virtual const IECore::PathMatcher paths( const std::string &setName ) const = 0;
	/// Must be implemented to provide the hash of `setName`.
	virtual void hash( const std::string &setName, IECore::MurmurHash &h ) const = 0;
	virtual ~SetProvider() {};
};

GAFFER_API IECore::PathMatcher evaluateSetExpression( const std::string &setExpression, const SetProvider &setProvider );

GAFFER_API void setExpressionHash( const std::string &setExpression, const SetProvider &setProvider, IECore::MurmurHash &h );
GAFFER_API IECore::MurmurHash setExpressionHash( const std::string &setExpression, const SetProvider &setProvider );

/// Editing
/// =======

/// Returns a simplified form of `setExpression`, handling cases including :
/// - Duplications (e.g. "A A" -> "A")
/// - Local cancellation (e.g. "A - A" -> "" or "(A B C) - (B C)" -> "A - (B C)")
/// - Redundant operations (e.g. "A [in,containing,&] A" -> "A")
/// - Repeated difference operators (e.g. "A - B - C - B" -> "A - (B C)")
/// Simplification is intended to improve readability and reduce obvious redundancy,
/// while keeping the evaluated result the same as the input set expression.
/// Note that simplification does not return the canonical form of the expression -
/// expressions that are functionally equivalent but differently structured may
/// simplify to different results.
GAFFER_API std::string simplify( const std::string &setExpression );
/// Returns a set expression that includes `inclusions` in `setExpression`.
/// The new set expression is equivalent to `setExpression | inclusions` with any
/// overlapping operations in `inclusions` first removed from `setExpression` and
/// the result simplified.
GAFFER_API std::string include( const std::string &setExpression, const std::string &inclusions );
/// Returns a set expression that excludes `exclusions` from `setExpression`.
/// The new set expression is equivalent to `setExpression - exclusions` with any
/// overlapping operations in `exclusions` first removed from `setExpression` and
/// the result simplified. Returns "" if `setExpression` is empty or would simplify
/// to an empty expression.
GAFFER_API std::string exclude( const std::string &setExpression, const std::string &exclusions );

} // namespace Gaffer::SetExpressionAlgo
