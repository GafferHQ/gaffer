//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFER_BOXPLUG_H
#define GAFFER_BOXPLUG_H

#include "OpenEXR/ImathBox.h"

#include "IECore/BoxTraits.h"

#include "Gaffer/CompoundNumericPlug.h"

namespace Gaffer
{

template<typename T>
class BoxPlug : public CompoundPlug
{

	public :

		typedef T ValueType;
		typedef CompoundNumericPlug<typename IECore::BoxTraits<T>::BaseType> ChildType;

		IECORE_RUNTIMETYPED_DECLARETEMPLATE( BoxPlug<T>, CompoundPlug );

		BoxPlug(
			const std::string &name = defaultName<BoxPlug>(),
			Direction direction=In,
			T defaultValue = T(),
			unsigned flags = Default
		);
		virtual ~BoxPlug();

		/// Accepts no children following construction.
		virtual bool acceptsChild( const GraphComponent *potentialChild ) const;
		virtual PlugPtr createCounterpart( const std::string &name, Direction direction ) const;

		ChildType *minPlug();
		const ChildType *minPlug() const;

		ChildType *maxPlug();
		const ChildType *maxPlug() const;

		T defaultValue() const;

		/// Calls setValue for the min and max child plugs, using the min and max of
		/// value.
		/// \undoable
		void setValue( const T &value );
		/// Returns the value, calling getValue() on the min and max child plugs to compute a component
		/// of the result.
		T getValue() const;

	private :

		IE_CORE_DECLARERUNTIMETYPEDDESCRIPTION( BoxPlug<T> );

};

typedef BoxPlug<Imath::Box2i> Box2iPlug;
typedef BoxPlug<Imath::Box3i> Box3iPlug;

typedef BoxPlug<Imath::Box2f> Box2fPlug;
typedef BoxPlug<Imath::Box3f> Box3fPlug;

IE_CORE_DECLAREPTR( Box2iPlug );
IE_CORE_DECLAREPTR( Box3iPlug );

IE_CORE_DECLAREPTR( Box2fPlug );
IE_CORE_DECLAREPTR( Box3fPlug );

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, Box2iPlug> > Box2iPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, Box2iPlug> > InputBox2iPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Box2iPlug> > OutputBox2iPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, Box3iPlug> > Box3iPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, Box3iPlug> > InputBox3iPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Box3iPlug> > OutputBox3iPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, Box2fPlug> > Box2fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, Box2fPlug> > InputBox2fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Box2fPlug> > OutputBox2fPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, Box3fPlug> > Box3fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, Box3fPlug> > InputBox3fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Box3fPlug> > OutputBox3fPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, Box2iPlug>, PlugPredicate<> > RecursiveBox2iPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Box2iPlug>, PlugPredicate<> > RecursiveInputBox2iPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Box2iPlug>, PlugPredicate<> > RecursiveOutputBox2iPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, Box3iPlug>, PlugPredicate<> > RecursiveBox3iPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Box3iPlug>, PlugPredicate<> > RecursiveInputBox3iPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Box3iPlug>, PlugPredicate<> > RecursiveOutputBox3iPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, Box2fPlug>, PlugPredicate<> > RecursiveBox2fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Box2fPlug>, PlugPredicate<> > RecursiveInputBox2fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Box2fPlug>, PlugPredicate<> > RecursiveOutputBox2fPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, Box3fPlug>, PlugPredicate<> > RecursiveBox3fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Box3fPlug>, PlugPredicate<> > RecursiveInputBox3fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Box3fPlug>, PlugPredicate<> > RecursiveOutputBox3fPlugIterator;

} // namespace Gaffer

#endif // GAFFER_BOXPLUG_H
