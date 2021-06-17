//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_DOT_H
#define GAFFER_DOT_H

#include "Gaffer/DependencyNode.h"
#include "Gaffer/NumericPlug.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

/// The Dot node has no computational purpose - it is merely a pass-through,
/// used as an organisational tool in the graph.
class GAFFER_API Dot : public DependencyNode
{

	public :

		Dot( const std::string &name=defaultName<Dot>() );
		~Dot() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::Dot, DotTypeId, DependencyNode );

		/// Because plugs are strongly typed in Gaffer, a
		/// Dot cannot be set up in advance to work with
		/// any type. This method should be called after
		/// construction to set the Dot up for a plug of
		/// a particular type. The passed plug is used as
		/// a template, but will not be referenced by the
		/// Dot itself - typically you will pass a plug
		/// which you will connect to the Dot after calling
		/// setup().
		/// \undoable
		void setup( const Plug *plug );

		template<typename T=Plug>
		T *inPlug();
		template<typename T=Plug>
		const T *inPlug() const;

		template<typename T=Plug>
		T *outPlug();
		template<typename T=Plug>
		const T *outPlug() const;

		enum LabelType
		{
			None = 0,
			NodeName = 1,
			UpstreamNodeName = 2,
			Custom = 3
		};

		IntPlug *labelTypePlug();
		const IntPlug *labelTypePlug() const;

		StringPlug *labelPlug();
		const StringPlug *labelPlug() const;

		void affects( const Plug *input, AffectedPlugsContainer &outputs ) const override;
		Plug *correspondingInput( const Plug *output ) override;
		const Plug *correspondingInput( const Plug *output ) const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Dot )

} // namespace Gaffer

#include "Gaffer/Dot.inl"

#endif // GAFFER_DOT_H
