//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/PathFilter.h"
#include "Gaffer/TypeIds.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( FileSequencePathFilter )

/// FileSequencePathFilters can filter the results
/// of FileSystemPath::children() to provide a masked view
/// that either includes or excludes FileSequences
class GAFFER_API FileSequencePathFilter : public PathFilter
{

	public :

		/// Defines which child paths should remain after the filter runs.
		enum Keep
		{
			/// Leaf paths which are not valid as files in an IECore::FileSequence
			Files = 0x00000001,
			/// Leaf paths which are valid as files in an IECore::FileSequence
			SequentialFiles = 0x00000002,
			/// Leaf paths which are themselves valid IECore::FileSequences
			Sequences = 0x00000004,
			Concise = Files | Sequences,
			Verbose = Files | SequentialFiles,
			All = Files | SequentialFiles | Sequences,
		};

		explicit FileSequencePathFilter( Keep mode = Concise, IECore::CompoundDataPtr userData = nullptr );
		~FileSequencePathFilter() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::FileSequencePathFilter, FileSequencePathFilterTypeId, Gaffer::PathFilter );

		Keep getMode() const;
		void setMode( Keep mode );

	protected :

		void doFilter( std::vector<PathPtr> &paths, const IECore::Canceller *canceller ) const override;

	private :

		bool remove( PathPtr path ) const;

		Keep m_mode;

};

IE_CORE_DECLAREPTR( FileSequencePathFilter )

} // namespace Gaffer
