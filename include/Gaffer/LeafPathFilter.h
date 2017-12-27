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

#ifndef GAFFER_LEAFPATHFILTER_H
#define GAFFER_LEAFPATHFILTER_H

#include "Gaffer/Export.h"
#include "Gaffer/PathFilter.h"

namespace Gaffer
{

/// A PathFilter which removes leaf paths.
class GAFFER_API LeafPathFilter : public Gaffer::PathFilter
{

	public :

		/// The filter passes through any path whose name matches
		/// one or more of the patterns (using StringAlgo match()).
		/// If leafOnly is true then directories will always be passed
		/// through.
		LeafPathFilter( IECore::CompoundDataPtr userData = nullptr );
		~LeafPathFilter() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::LeafPathFilter, LeafPathFilterTypeId, PathFilter );

	protected :

		void doFilter( std::vector<PathPtr> &paths ) const override;

	private :

		bool remove( PathPtr path ) const;

};

IE_CORE_DECLAREPTR( LeafPathFilter )

} // namespace Gaffer

#endif // GAFFER_LEAFPATHFILTER_H
