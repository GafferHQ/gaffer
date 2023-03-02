//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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
#include "Gaffer/Signals.h"
#include "Gaffer/TypeIds.h"

#include "IECore/CompoundData.h"
#include "IECore/RunTimeTyped.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Path )
IE_CORE_FORWARDDECLARE( PathFilter )

/// PathFilters are classes which can filter the results
/// of Path::children() methods to provide a masked view of
/// the hierarchy the Path navigates. Filters are applied
/// to a path using the Path::setFilter() method.
class GAFFER_API PathFilter : public IECore::RunTimeTyped
{

	public :

		PathFilter( IECore::CompoundDataPtr userData = nullptr );
		~PathFilter() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::PathFilter, PathFilterTypeId, IECore::RunTimeTyped );

		IECore::CompoundData *userData();

		void setEnabled( bool enabled );
		bool getEnabled() const;

		void filter( std::vector<PathPtr> &paths, const IECore::Canceller *canceller = nullptr ) const;

		using ChangedSignal = Signals::Signal<void ( PathFilter * )>;
		ChangedSignal &changedSignal();

	protected :

		/// Must be implemented by derived classes to filter the passed
		/// paths in place.
		virtual void doFilter( std::vector<PathPtr> &paths, const IECore::Canceller *canceller ) const = 0;

	private :

		IECore::CompoundDataPtr m_userData;
		bool m_enabled;

		ChangedSignal m_changedSignal;

};

IE_CORE_DECLAREPTR( PathFilter )

} // namespace Gaffer
