//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Hypothetical Inc. All rights reserved.
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

#ifndef GAFFER_HIDDENFILEPATHFILTER_H
#define GAFFER_HIDDENFILEPATHFILTER_H

#include "Gaffer/PathFilter.h"
#include "Gaffer/TypeIds.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( HiddenFilePathFilter )

/// HiddenFilePathFilters can filter the results
/// of FileSystemPath::children() to provide a masked view
/// that either includes or excludes hidden files.
class GAFFER_API HiddenFilePathFilter : public PathFilter
{

	public :

		HiddenFilePathFilter( IECore::CompoundDataPtr userData = nullptr );
		~HiddenFilePathFilter() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::HiddenFilePathFilter, HiddenFilePathFilterTypeId, Gaffer::PathFilter );

		void setInverted( bool inverted );
		bool getInverted() const;

	protected :

		void doFilter( std::vector<PathPtr> &paths, const IECore::Canceller *canceller ) const override;

	private :

		bool invert( bool b ) const;
		bool remove( PathPtr path ) const;

		bool m_inverted;

};

IE_CORE_DECLAREPTR( HiddenFilePathFilter )

} // namespace Gaffer

#endif // GAFFER_HIDDENFILEPATHFILTER_H
