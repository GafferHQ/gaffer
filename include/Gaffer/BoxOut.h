//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_BOXOUT_H
#define GAFFER_BOXOUT_H

#include "Gaffer/BoxIO.h"

namespace Gaffer
{

class BoxIn;

class GAFFER_API BoxOut : public BoxIO
{

	public :

		BoxOut( const std::string &name=defaultName<BoxOut>() );
		~BoxOut() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::BoxOut, BoxOutTypeId, BoxIO );

		template<typename T=Plug>
		T *passThroughPlug();
		template<typename T=Plug>
		const T *passThroughPlug() const;

	protected :

		bool acceptsInput( const Plug *plug, const Plug *inputPlug ) const override;

	private :

		const BoxIn *sourceBoxIn( const Plug *plug ) const;

};

IE_CORE_DECLAREPTR( BoxOut )

[[deprecated("Use `BoxOut::Iterator` instead")]]
typedef FilteredChildIterator<TypePredicate<BoxOut> > BoxOutIterator;
[[deprecated("Use `BoxOut::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<TypePredicate<BoxOut> > RecursiveBoxOutIterator;

} // namespace Gaffer

#include "Gaffer/BoxOut.inl"

#endif // GAFFER_BOXOUT_H
