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

#ifndef GAFFERSCENE_FILTER_H
#define GAFFERSCENE_FILTER_H

#include "Gaffer/ComputeNode.h"
#include "Gaffer/NumericPlug.h"

#include "GafferScene/TypeIds.h"

namespace GafferScene
{

class Filter : public Gaffer::ComputeNode
{

	public :

		enum Result
		{
			NoMatch = 0,
			DescendantMatch = 1,
			ExactMatch = 2,
			AncestorMatch = 4,
			EveryMatch = DescendantMatch | ExactMatch | AncestorMatch
		};

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::Filter, FilterTypeId, Gaffer::ComputeNode );

		Filter( const std::string &name=defaultName<Filter>() );
		virtual ~Filter();
		
		Gaffer::IntPlug *matchPlug();
		const Gaffer::IntPlug *matchPlug() const;
				
	protected :
		
		/// Implemented to call hashMatch() below when computing the hash for matchPlug().
		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		/// Implemented to call computeMatch() below when computing the value of matchPlug().
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;
		
		/// Must be implemented by derived classes.
		virtual void hashMatch( const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		virtual unsigned computeMatch( const Gaffer::Context *context ) const = 0;

	private :
	
		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Filter )

} // namespace GafferScene

#endif // GAFFERSCENE_FILTER_H
