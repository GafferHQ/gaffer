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

#include "Gaffer/CompoundPlug.h"
#include "Gaffer/Behaviours/InputGenerator.h"

namespace Gaffer
{

/// The ArrayPlug maintains a sequence of identically-typed child
/// plugs, automatically adding new plugs when all existing plugs
/// have connections.
/// \todo Consider using this everywhere in preference to
/// InputGenerator, and removing the InputGenerator class.
class ArrayPlug : public CompoundPlug
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
			PlugPtr element = NULL,
			size_t minSize = 1,
			size_t maxSize = Imath::limits<size_t>::max(),
			unsigned flags = Default
		);

		virtual ~ArrayPlug();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::ArrayPlug, ArrayPlugTypeId, CompoundPlug );

		virtual bool acceptsChild( const GraphComponent *potentialChild ) const;
		virtual PlugPtr createCounterpart( const std::string &name, Direction direction ) const;

		size_t minSize() const;
		size_t maxSize() const;

	private :

		void childAdded();
		void parentChanged();

		size_t m_minSize;
		size_t m_maxSize;

		typedef Behaviours::InputGenerator<Plug> InputGenerator;
		typedef boost::shared_ptr<InputGenerator> InputGeneratorPtr;
		InputGeneratorPtr m_inputGenerator;

};

IE_CORE_DECLAREPTR( ArrayPlug );

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, ArrayPlug> > ArrayPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, ArrayPlug> > InputArrayPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, ArrayPlug> > OutputArrayPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, ArrayPlug>, PlugPredicate<> > RecursiveArrayPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, ArrayPlug>, PlugPredicate<> > RecursiveInputArrayPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, ArrayPlug>, PlugPredicate<> > RecursiveOutputArrayPlugIterator;

} // namespace Gaffer

#endif // GAFFER_ARRAYPLUG_H
