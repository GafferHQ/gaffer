//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_REFERENCE_H
#define GAFFER_REFERENCE_H

#include "Gaffer/Export.h"
#include "Gaffer/SubGraph.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

class GAFFER_API Reference : public SubGraph
{

	public :

		Reference( const std::string &name=defaultName<Reference>() );
		~Reference() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::Reference, ReferenceTypeId, SubGraph );

		/// Loads the specified script, which should have been exported
		/// using Box::exportForReference().
		/// \undoable.
		void load( const std::string &fileName );
		/// Returns the name of the script currently being referenced.
		const std::string &fileName() const;

		typedef boost::signal<void ( Reference * )> ReferenceLoadedSignal;
		/// Emitted when a reference is loaded (or unloaded following an undo).
		ReferenceLoadedSignal &referenceLoadedSignal();

	private :

		void loadInternal( const std::string &fileName );
		bool isReferencePlug( const Plug *plug ) const;

		void convertPersistentMetadata( Plug *plug ) const;

		std::string m_fileName;
		ReferenceLoadedSignal m_referenceLoadedSignal;

};

IE_CORE_DECLAREPTR( Reference )

typedef FilteredChildIterator<TypePredicate<Reference> > ReferenceIterator;
typedef FilteredRecursiveChildIterator<TypePredicate<Reference> > RecursiveReferenceIterator;

} // namespace Gaffer

#endif // GAFFER_REFERENCE_H
