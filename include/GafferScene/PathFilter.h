//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFERSCENE_PATHFILTER_H
#define GAFFERSCENE_PATHFILTER_H

#include "Gaffer/TypedObjectPlug.h"

#include "GafferScene/Filter.h"
#include "GafferScene/PathMatcher.h"

namespace GafferScene
{

/// \todo Investigate whether or not caching is actually beneficial for this node
class PathFilter : public Filter
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::PathFilter, PathFilterTypeId, Filter );

		PathFilter( const std::string &name=defaultName<PathFilter>() );
		virtual ~PathFilter();
		
		Gaffer::StringVectorDataPlug *pathsPlug();
		const Gaffer::StringVectorDataPlug *pathsPlug() const;
				
		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :

		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;

		virtual void hashMatch( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual unsigned computeMatch( const Gaffer::Context *context ) const;

	private :

		Gaffer::ObjectPlug *pathMatcherPlug();
		const Gaffer::ObjectPlug *pathMatcherPlug() const;
	
		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( PathFilter )

} // namespace GafferScene

#endif // GAFFERSCENE_PATHFILTER_H
