//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_COMPOUNDPATHFILTER_H
#define GAFFER_COMPOUNDPATHFILTER_H

#include "Gaffer/Export.h"
#include "Gaffer/PathFilter.h"

namespace Gaffer
{

/// The CompoundPathFilter class simply combines a number of other
/// PathFilters, applying them in sequence.
class GAFFER_API CompoundPathFilter : public Gaffer::PathFilter
{

	public :

		typedef std::vector<PathFilterPtr> Filters;

		CompoundPathFilter( IECore::CompoundDataPtr userData = nullptr );
		~CompoundPathFilter() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::CompoundPathFilter, CompoundPathFilterTypeId, PathFilter );

		void addFilter( PathFilterPtr filter );
		void removeFilter( PathFilter *filter );

		void setFilters( const Filters &filters );
		void getFilters( Filters &filters ) const;

	protected :

		void doFilter( std::vector<PathPtr> &paths ) const override;

	private :

		// Doesn't emit changed signal.
		void addFilterInternal( PathFilterPtr filter );
		void filterChanged();

		struct Filter
		{
			PathFilterPtr filter;
			boost::signals::scoped_connection filterChangedConnection;
		};

		// Using a list rather than a vector, because
		// scoped_connections can't be copy constructed.
		std::list<Filter> m_filters;

};

IE_CORE_DECLAREPTR( CompoundPathFilter )

} // namespace Gaffer

#endif // GAFFER_COMPOUNDPATHFILTER_H
