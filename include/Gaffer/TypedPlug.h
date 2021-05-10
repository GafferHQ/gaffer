//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_TYPEDPLUG_H
#define GAFFER_TYPEDPLUG_H

#include "Gaffer/ValuePlug.h"

#include "IECore/SimpleTypedData.h"

namespace Gaffer
{

template<typename T>
class IECORE_EXPORT TypedPlug : public ValuePlug
{

	public :

		typedef T ValueType;

		GAFFER_PLUG_DECLARE_TEMPLATE_TYPE( TypedPlug<T>, ValuePlug );

		TypedPlug(
			const std::string &name = defaultName<TypedPlug>(),
			Direction direction=In,
			const T &defaultValue = T(),
			unsigned flags = Default
		);
		~TypedPlug() override;

		/// Accepts only instances of TypedPlug<T> or derived classes.
		/// In addition, BoolPlug accepts inputs from NumericPlug.
		bool acceptsInput( const Plug *input ) const override;
		PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		const T &defaultValue() const;

		/// \undoable
		void setValue( const T &value );
		/// Returns the value. See comments in TypedObjectPlug::getValue()
		/// for details of the optional precomputedHash argument - and use
		/// with care!
		T getValue( const IECore::MurmurHash *precomputedHash = nullptr ) const;

		void setFrom( const ValuePlug *other ) override;

		/// Implemented to just return ValuePlug::hash(),
		/// but may be specialised in particular instantiations.
		IECore::MurmurHash hash() const override;
		/// Ensures the method above doesn't mask
		/// ValuePlug::hash( h )
		using ValuePlug::hash;

	private :

		typedef IECore::TypedData<T> DataType;
		typedef typename DataType::Ptr DataTypePtr;

};

typedef TypedPlug<bool> BoolPlug;
typedef TypedPlug<Imath::M33f> M33fPlug;
typedef TypedPlug<Imath::M44f> M44fPlug;
typedef TypedPlug<Imath::Box2f> AtomicBox2fPlug;
typedef TypedPlug<Imath::Box3f> AtomicBox3fPlug;
typedef TypedPlug<Imath::Box2i> AtomicBox2iPlug;

IE_CORE_DECLAREPTR( BoolPlug );
IE_CORE_DECLAREPTR( M33fPlug );
IE_CORE_DECLAREPTR( M44fPlug );
IE_CORE_DECLAREPTR( AtomicBox2fPlug );
IE_CORE_DECLAREPTR( AtomicBox3fPlug );
IE_CORE_DECLAREPTR( AtomicBox2iPlug );

[[deprecated("Use `BoolPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, BoolPlug> > BoolPlugIterator;
[[deprecated("Use `BoolPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, BoolPlug> > InputBoolPlugIterator;
[[deprecated("Use `BoolPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, BoolPlug> > OutputBoolPlugIterator;
[[deprecated("Use `M33fPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, M33fPlug> > M33fPlugIterator;
[[deprecated("Use `M33fPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, M33fPlug> > InputM33fPlugIterator;
[[deprecated("Use `M33fPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, M33fPlug> > OutputM33fPlugIterator;
[[deprecated("Use `M44fPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, M44fPlug> > M44fPlugIterator;
[[deprecated("Use `M44fPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, M44fPlug> > InputM44fPlugIterator;
[[deprecated("Use `M44fPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, M44fPlug> > OutputM44fPlugIterator;
[[deprecated("Use `AtomicBox2fPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, AtomicBox2fPlug> > AtomicBox2fPlugIterator;
[[deprecated("Use `AtomicBox2fPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, AtomicBox2fPlug> > InputAtomicBox2fPlugIterator;
[[deprecated("Use `AtomicBox2fPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, AtomicBox2fPlug> > OutputAtomicBox2fPlugIterator;
[[deprecated("Use `AtomicBox3fPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, AtomicBox3fPlug> > AtomicBox3fPlugIterator;
[[deprecated("Use `AtomicBox3fPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, AtomicBox3fPlug> > InputAtomicBox3fPlugIterator;
[[deprecated("Use `AtomicBox3fPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, AtomicBox3fPlug> > OutputAtomicBox3fPlugIterator;
[[deprecated("Use `AtomicBox2iPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, AtomicBox2iPlug> > AtomicBox2iPlugIterator;
[[deprecated("Use `AtomicBox2iPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, AtomicBox2iPlug> > InputAtomicBox2iPlugIterator;
[[deprecated("Use `AtomicBox2iPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, AtomicBox2iPlug> > OutputAtomicBox2iPlugIterator;
[[deprecated("Use `BoolPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, BoolPlug>, PlugPredicate<> > RecursiveBoolPlugIterator;
[[deprecated("Use `BoolPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, BoolPlug>, PlugPredicate<> > RecursiveInputBoolPlugIterator;
[[deprecated("Use `BoolPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, BoolPlug>, PlugPredicate<> > RecursiveOutputBoolPlugIterator;
[[deprecated("Use `M33fPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, M33fPlug>, PlugPredicate<> > RecursiveM33fPlugIterator;
[[deprecated("Use `M33fPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, M33fPlug>, PlugPredicate<> > RecursiveInputM33fPlugIterator;
[[deprecated("Use `M33fPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, M33fPlug>, PlugPredicate<> > RecursiveOutputM33fPlugIterator;
[[deprecated("Use `M44fPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, M44fPlug>, PlugPredicate<> > RecursiveM44fPlugIterator;
[[deprecated("Use `M44fPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, M44fPlug>, PlugPredicate<> > RecursiveInputM44fPlugIterator;
[[deprecated("Use `M44fPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, M44fPlug>, PlugPredicate<> > RecursiveOutputM44fPlugIterator;
[[deprecated("Use `AtomicBox2fPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, AtomicBox2fPlug>, PlugPredicate<> > RecursiveAtomicBox2fPlugIterator;
[[deprecated("Use `AtomicBox2fPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, AtomicBox2fPlug>, PlugPredicate<> > RecursiveInputAtomicBox2fPlugIterator;
[[deprecated("Use `AtomicBox2fPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, AtomicBox2fPlug>, PlugPredicate<> > RecursiveOutputAtomicBox2fPlugIterator;
[[deprecated("Use `AtomicBox3fPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, AtomicBox3fPlug>, PlugPredicate<> > RecursiveAtomicBox3fPlugIterator;
[[deprecated("Use `AtomicBox3fPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, AtomicBox3fPlug>, PlugPredicate<> > RecursiveInputAtomicBox3fPlugIterator;
[[deprecated("Use `AtomicBox3fPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, AtomicBox3fPlug>, PlugPredicate<> > RecursiveOutputAtomicBox3fPlugIterator;
[[deprecated("Use `AtomicBox2iPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, AtomicBox2iPlug>, PlugPredicate<> > RecursiveAtomicBox2iPlugIterator;
[[deprecated("Use `AtomicBox2iPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, AtomicBox2iPlug>, PlugPredicate<> > RecursiveInputAtomicBox2iPlugIterator;
[[deprecated("Use `AtomicBox2iPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, AtomicBox2iPlug>, PlugPredicate<> > RecursiveOutputAtomicBox2iPlugIterator;

} // namespace Gaffer

#endif // GAFFER_TYPEDPLUG_H
