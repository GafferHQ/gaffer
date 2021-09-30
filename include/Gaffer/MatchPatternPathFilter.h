//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#ifndef GAFFER_MATCHPATTERNPATHFILTER_H
#define GAFFER_MATCHPATTERNPATHFILTER_H

#include "Gaffer/PathFilter.h"

#include "IECore/StringAlgo.h"

namespace Gaffer
{

/// A PathFilter which filters using StringAlgo match().
class GAFFER_API MatchPatternPathFilter : public Gaffer::PathFilter
{

	public :

		/// The filter passes through any path whose name matches
		/// one or more of the patterns (using StringAlgo match()).
		/// If leafOnly is true then directories will always be passed
		/// through.
		MatchPatternPathFilter( const std::vector<IECore::StringAlgo::MatchPattern> &patterns, IECore::InternedString propertyName = "name", bool leafOnly = true, IECore::CompoundDataPtr userData = nullptr );
		~MatchPatternPathFilter() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::MatchPatternPathFilter, MatchPatternPathFilterTypeId, PathFilter );

		void setMatchPatterns( const std::vector<IECore::StringAlgo::MatchPattern> &patterns );
		const std::vector<IECore::StringAlgo::MatchPattern> &getMatchPatterns() const;

		void setPropertyName( IECore::InternedString propertyName );
		IECore::InternedString getPropertyName() const;

		/// \todo Refactor the base class so that derived classes
		/// are just responsible for returning a bool when given a
		/// path, and then move inverting on to the base class.
		void setInverted( bool inverted );
		bool getInverted() const;

	protected :

		void doFilter( std::vector<PathPtr> &paths, const IECore::Canceller *canceller ) const override;

	private :

		bool invert( bool b ) const;
		bool remove( PathPtr path ) const;

		std::vector<IECore::StringAlgo::MatchPattern> m_patterns;
		IECore::InternedString m_propertyName;
		bool m_leafOnly;
		bool m_inverted;

};

IE_CORE_DECLAREPTR( MatchPatternPathFilter )

} // namespace Gaffer

#endif // GAFFER_MATCHPATTERNPATHFILTER_H
