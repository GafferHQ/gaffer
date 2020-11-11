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

#include "Gaffer/CompoundNumericPlug.h"

#include "IECore/BoxTraits.h"
#include "IECore/Export.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/ImathBox.h"
IECORE_POP_DEFAULT_VISIBILITY

namespace Gaffer
{

template<typename T>
class GAFFER_API BoxPlug : public ValuePlug
{

	public :

		typedef T ValueType;
		typedef typename IECore::BoxTraits<T>::BaseType PointType;
		typedef CompoundNumericPlug<PointType> ChildType;

		GAFFER_PLUG_DECLARE_TEMPLATE_TYPE( BoxPlug<T>, ValuePlug );

		BoxPlug(
			const std::string &name = defaultName<BoxPlug>(),
			Direction direction=In,
			T defaultValue = T(),
			unsigned flags = Default
		);

		BoxPlug(
			const std::string &name,
			Direction direction,
			T defaultValue,
			const PointType &minValue,
			const PointType &maxValue,
			unsigned flags = Default
		);

		~BoxPlug() override;

		/// Accepts no children following construction.
		bool acceptsChild( const GraphComponent *potentialChild ) const override;
		PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		ChildType *minPlug();
		const ChildType *minPlug() const;

		ChildType *maxPlug();
		const ChildType *maxPlug() const;

		T defaultValue() const;

		bool hasMinValue() const;
		bool hasMaxValue() const;

		PointType minValue() const;
		PointType maxValue() const;

		/// Calls setValue for the min and max child plugs, using the min and max of
		/// value.
		/// \undoable
		void setValue( const T &value );
		/// Returns the value, calling getValue() on the min and max child plugs to compute a component
		/// of the result.
		T getValue() const;

};

typedef BoxPlug<Imath::Box2i> Box2iPlug;
typedef BoxPlug<Imath::Box3i> Box3iPlug;

typedef BoxPlug<Imath::Box2f> Box2fPlug;
typedef BoxPlug<Imath::Box3f> Box3fPlug;

IE_CORE_DECLAREPTR( Box2iPlug );
IE_CORE_DECLAREPTR( Box3iPlug );

IE_CORE_DECLAREPTR( Box2fPlug );
IE_CORE_DECLAREPTR( Box3fPlug );

[[deprecated("Use `Box2iPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, Box2iPlug> > Box2iPlugIterator;
[[deprecated("Use `Box2iPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, Box2iPlug> > InputBox2iPlugIterator;
[[deprecated("Use `Box2iPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Box2iPlug> > OutputBox2iPlugIterator;
[[deprecated("Use `Box3iPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, Box3iPlug> > Box3iPlugIterator;
[[deprecated("Use `Box3iPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, Box3iPlug> > InputBox3iPlugIterator;
[[deprecated("Use `Box3iPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Box3iPlug> > OutputBox3iPlugIterator;
[[deprecated("Use `Box2fPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, Box2fPlug> > Box2fPlugIterator;
[[deprecated("Use `Box2fPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, Box2fPlug> > InputBox2fPlugIterator;
[[deprecated("Use `Box2fPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Box2fPlug> > OutputBox2fPlugIterator;
[[deprecated("Use `Box3fPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, Box3fPlug> > Box3fPlugIterator;
[[deprecated("Use `Box3fPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, Box3fPlug> > InputBox3fPlugIterator;
[[deprecated("Use `Box3fPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Box3fPlug> > OutputBox3fPlugIterator;
[[deprecated("Use `Box2iPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, Box2iPlug>, PlugPredicate<> > RecursiveBox2iPlugIterator;
[[deprecated("Use `Box2iPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Box2iPlug>, PlugPredicate<> > RecursiveInputBox2iPlugIterator;
[[deprecated("Use `Box2iPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Box2iPlug>, PlugPredicate<> > RecursiveOutputBox2iPlugIterator;
[[deprecated("Use `Box3iPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, Box3iPlug>, PlugPredicate<> > RecursiveBox3iPlugIterator;
[[deprecated("Use `Box3iPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Box3iPlug>, PlugPredicate<> > RecursiveInputBox3iPlugIterator;
[[deprecated("Use `Box3iPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Box3iPlug>, PlugPredicate<> > RecursiveOutputBox3iPlugIterator;
[[deprecated("Use `Box2fPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, Box2fPlug>, PlugPredicate<> > RecursiveBox2fPlugIterator;
[[deprecated("Use `Box2fPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Box2fPlug>, PlugPredicate<> > RecursiveInputBox2fPlugIterator;
[[deprecated("Use `Box2fPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Box2fPlug>, PlugPredicate<> > RecursiveOutputBox2fPlugIterator;
[[deprecated("Use `Box3fPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, Box3fPlug>, PlugPredicate<> > RecursiveBox3fPlugIterator;
[[deprecated("Use `Box3fPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Box3fPlug>, PlugPredicate<> > RecursiveInputBox3fPlugIterator;
[[deprecated("Use `Box3fPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Box3fPlug>, PlugPredicate<> > RecursiveOutputBox3fPlugIterator;

} // namespace Gaffer

#endif // GAFFER_BOXPLUG_H
