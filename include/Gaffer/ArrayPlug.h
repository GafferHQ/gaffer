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

#ifndef GAFFER_ARRAYPLUG_H
#define GAFFER_ARRAYPLUG_H

#include "Gaffer/Plug.h"

namespace Gaffer
{

/// The ArrayPlug maintains a sequence of identically-typed child
/// plugs, automatically adding new plugs when all existing plugs
/// have connections.
class GAFFER_API ArrayPlug : public Plug
{

	public :

		/// The element plug is used as the first array element,
		/// and all new array elements are created by calling
		/// element->createCounterpart(). Currently the element
		/// names are derived from the name of the first element,
		/// but this may change in the future. It is strongly
		/// recommended that ArrayPlug children are only accessed
		/// through numeric indexing and never via names.
		ArrayPlug(
			const std::string &name = defaultName<ArrayPlug>(),
			Direction direction = In,
			PlugPtr element = nullptr,
			size_t minSize = 1,
			size_t maxSize = std::numeric_limits<size_t>::max(),
			unsigned flags = Default,
			bool resizeWhenInputsChange = true
		);

		~ArrayPlug() override;

		GAFFER_PLUG_DECLARE_TYPE( Gaffer::ArrayPlug, ArrayPlugTypeId, Plug );

		bool acceptsChild( const GraphComponent *potentialChild ) const override;
		bool acceptsInput( const Plug *input ) const override;
		void setInput( PlugPtr input ) override;
		PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		size_t minSize() const;
		size_t maxSize() const;
		void resize( size_t size );
		bool resizeWhenInputsChange() const;
		/// Returns an unconnected element at the end of the array, adding one
		/// if necessary. Returns null if `maxSize()` prevents the creation of
		/// a new element.
		Gaffer::Plug *next();

	protected :

		void parentChanged( GraphComponent *oldParent ) override;

	private :

		void inputChanged( Gaffer::Plug *plug );

		size_t m_minSize;
		size_t m_maxSize;
		bool m_resizeWhenInputsChange;

		Signals::ScopedConnection m_inputChangedConnection;

};

IE_CORE_DECLAREPTR( ArrayPlug );

} // namespace Gaffer

#endif // GAFFER_ARRAYPLUG_H
