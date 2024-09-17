//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "IECore/Data.h"
#include "IECore/PathMatcherData.h"
#include "IECore/VectorTypedData.h"

#include "boost/multi_index/hashed_index.hpp"
#include "boost/multi_index/member.hpp"
#include "boost/multi_index_container.hpp"

#include <vector>
#include <unordered_set>

namespace GafferScene
{

namespace Private
{

/// Utility class to merge `childNames` from multiple
/// input scenes, renaming children to preserve uniqueness.
class ChildNamesMap : public IECore::Data
{

	public :

		ChildNamesMap( const std::vector<IECore::ConstInternedStringVectorDataPtr> &inputChildNames );

		struct Input
		{
			IECore::InternedString name;
			size_t index;
			bool operator == ( const Input &rhs ) const { return name == rhs.name && index == rhs.index; }
		};

		/// Returns the merged child names.
		const IECore::InternedStringVectorData *outputChildNames() const;
		/// Returns the input which is mapped to `outputName`.
		const Input &input( IECore::InternedString outputName ) const;
		/// Combines multiple input sets, accounting for the name remapping.
		IECore::PathMatcher set( const std::vector<IECore::ConstPathMatcherDataPtr> &inputSets ) const;

		static IECore::InternedString uniqueName( IECore::InternedString name, const std::unordered_set<IECore::InternedString> &existingNames );

	private :

		const IECore::InternedStringVectorDataPtr m_childNames;

		struct Child
		{
			const Input input;
			const IECore::InternedString output;
		};

		using Map = boost::multi_index::multi_index_container<
			Child,
			boost::multi_index::indexed_by<
				boost::multi_index::hashed_unique<boost::multi_index::member<Child, const IECore::InternedString, &Child::output>>,
				boost::multi_index::hashed_unique<boost::multi_index::member<Child, const Input, &Child::input>>
			>
		>;

		Map m_map;

};

IE_CORE_DECLAREPTR( ChildNamesMap )

} // namespace Private

} // namespace GafferScene
