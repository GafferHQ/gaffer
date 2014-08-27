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

#include "Gaffer/Node.h"

namespace Gaffer
{

class Reference : public Node
{

	public :

		Reference( const std::string &name=defaultName<Reference>() );
		virtual ~Reference();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::Reference, ReferenceTypeId, Node );

		/// The plugs that stores the name of the file being
		/// referenced. This should be considered read-only, and the
		/// load() method should be used to set it.
		StringPlug *fileNamePlug();
		const StringPlug *fileNamePlug() const;

		/// Loads the specified script, which should have been exported
		/// using Box::exportForReference().
		void load( const std::string &fileName );

	private :

		bool isReferencePlug( const Plug *plug ) const;

		static size_t g_firstPlugIndex;

};

typedef FilteredChildIterator<TypePredicate<Reference> > ReferenceIterator;
typedef FilteredRecursiveChildIterator<TypePredicate<Reference> > RecursiveReferenceIterator;

} // namespace Gaffer

#endif // GAFFER_REFERENCE_H
