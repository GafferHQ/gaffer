//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_TYPEDOBJECTPLUG_H
#define GAFFER_TYPEDOBJECTPLUG_H

// Include must come first to avoid symbol visibility problems with Clang.
// It would appear that if any inline code involving `std::vector` appears
// before the definitions of VectorTypedData, Clang will hide the symbols
// for `TypedObjectPlug<*VectorData>`.
#include "IECore/VectorTypedData.h"

#include "Gaffer/ValuePlug.h"

#include "IECore/CompoundData.h"
#include "IECore/CompoundObject.h"
#include "IECore/Object.h"
#include "IECore/ObjectVector.h"
#include "IECore/PathMatcherData.h"

namespace Gaffer
{

/// A Plug type which can store values derived from IECore::Object.
template<typename T>
class IECORE_EXPORT TypedObjectPlug : public ValuePlug
{

	public :

		typedef T ValueType;
		typedef typename ValueType::Ptr ValuePtr;
		typedef typename ValueType::ConstPtr ConstValuePtr;

		GAFFER_PLUG_DECLARE_TEMPLATE_TYPE( TypedObjectPlug<T>, ValuePlug );

		/// A copy of defaultValue is taken - it must not be null.
		TypedObjectPlug(
			const std::string &name,
			Direction direction,
			ConstValuePtr defaultValue,
			unsigned flags = Default
		);
		~TypedObjectPlug() override;

		/// Accepts only instances of TypedObjectPlug<T>, or derived classes.
		bool acceptsInput( const Plug *input ) const override;
		PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		const ValueType *defaultValue() const;

		/// Sets the value, which must be non-null. The value is referenced directly
		/// and may be shared internally with other Plugs and the cache - under no
		/// circumstances should you /ever/ modify value after calling setValue( value ).
		/// Note that the python bindings perform an automatic copy before calling
		/// setValue() (unless instructed otherwise), to make it harder
		/// for less experienced coders to get this wrong.
		void setValue( ConstValuePtr value );
		/// Returns the value. Note that the returned value is not a copy
		/// and may be shared with other Plugs and the cache - it is therefore
		/// imperative that it not be modified in any way. The python bindings
		/// automatically return a copy from getValue() (unless instructed otherwise)
		/// to make it harder for less experienced coders to get this wrong.
		///
		/// If available, an optional precomputed hash may be passed to avoid the cost
		/// of computing it again. This hash must have been computed in the current context
		/// with the node graph in the current state. Passing an incorrect hash has dire
		/// consequences - use with care.
		///
		/// Precomputed hashes are intended to support the following use pattern :
		///
		/// MurmurHash currentHash = plug->hash();
		/// if( currentHash != storedHash )
		/// {
		/// 	ConstObjectPtr currentObject = plug->getValue( &currentHash );
		/// 	storedObject = convertObjectInSomeWay( currentObject );
		/// 	storedHash = currentHash;
		/// }
		///
		/// This pattern is particularly effective because it not only
		/// avoids unnecessary conversions, but it also avoids churn in
		/// the ValuePlug cache.
		ConstValuePtr getValue( const IECore::MurmurHash *precomputedHash = nullptr ) const;

		void setFrom( const ValuePlug *other ) override;

};

#ifndef Gaffer_EXPORTS

extern template class TypedObjectPlug<IECore::Object>;
extern template class TypedObjectPlug<IECore::BoolVectorData>;
extern template class TypedObjectPlug<IECore::IntVectorData>;
extern template class TypedObjectPlug<IECore::FloatVectorData>;
extern template class TypedObjectPlug<IECore::StringVectorData>;
extern template class TypedObjectPlug<IECore::InternedStringVectorData>;
extern template class TypedObjectPlug<IECore::V2iVectorData>;
extern template class TypedObjectPlug<IECore::V3fVectorData>;
extern template class TypedObjectPlug<IECore::Color3fVectorData>;
extern template class TypedObjectPlug<IECore::M44fVectorData>;
extern template class TypedObjectPlug<IECore::M33fVectorData>;
extern template class TypedObjectPlug<IECore::ObjectVector>;
extern template class TypedObjectPlug<IECore::CompoundObject>;
extern template class TypedObjectPlug<IECore::CompoundData>;
extern template class TypedObjectPlug<IECore::PathMatcherData>;

#endif

typedef TypedObjectPlug<IECore::Object> ObjectPlug;
typedef TypedObjectPlug<IECore::BoolVectorData> BoolVectorDataPlug;
typedef TypedObjectPlug<IECore::IntVectorData> IntVectorDataPlug;
typedef TypedObjectPlug<IECore::FloatVectorData> FloatVectorDataPlug;
typedef TypedObjectPlug<IECore::StringVectorData> StringVectorDataPlug;
typedef TypedObjectPlug<IECore::InternedStringVectorData> InternedStringVectorDataPlug;
typedef TypedObjectPlug<IECore::V2iVectorData> V2iVectorDataPlug;
typedef TypedObjectPlug<IECore::V3fVectorData> V3fVectorDataPlug;
typedef TypedObjectPlug<IECore::Color3fVectorData> Color3fVectorDataPlug;
typedef TypedObjectPlug<IECore::M44fVectorData> M44fVectorDataPlug;
typedef TypedObjectPlug<IECore::M33fVectorData> M33fVectorDataPlug;
typedef TypedObjectPlug<IECore::ObjectVector> ObjectVectorPlug;
typedef TypedObjectPlug<IECore::CompoundObject> CompoundObjectPlug;
typedef TypedObjectPlug<IECore::CompoundData> AtomicCompoundDataPlug;
typedef TypedObjectPlug<IECore::PathMatcherData> PathMatcherDataPlug;

IE_CORE_DECLAREPTR( ObjectPlug );
IE_CORE_DECLAREPTR( BoolVectorDataPlug );
IE_CORE_DECLAREPTR( IntVectorDataPlug );
IE_CORE_DECLAREPTR( FloatVectorDataPlug );
IE_CORE_DECLAREPTR( StringVectorDataPlug );
IE_CORE_DECLAREPTR( InternedStringVectorDataPlug );
IE_CORE_DECLAREPTR( V2iVectorDataPlug );
IE_CORE_DECLAREPTR( V3fVectorDataPlug );
IE_CORE_DECLAREPTR( Color3fVectorDataPlug );
IE_CORE_DECLAREPTR( M44fVectorDataPlug );
IE_CORE_DECLAREPTR( M33fVectorDataPlug );
IE_CORE_DECLAREPTR( ObjectVectorPlug );
IE_CORE_DECLAREPTR( CompoundObjectPlug );
IE_CORE_DECLAREPTR( AtomicCompoundDataPlug );
IE_CORE_DECLAREPTR( PathMatcherDataPlug );

[[deprecated("Use `ObjectPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, ObjectPlug> > ObjectPlugIterator;
[[deprecated("Use `ObjectPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, ObjectPlug> > InputObjectPlugIterator;
[[deprecated("Use `ObjectPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, ObjectPlug> > OutputObjectPlugIterator;
[[deprecated("Use `BoolVectorDataPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, BoolVectorDataPlug> > BoolVectorDataPlugIterator;
[[deprecated("Use `BoolVectorDataPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, BoolVectorDataPlug> > InputBoolVectorDataPlugIterator;
[[deprecated("Use `BoolVectorDataPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, BoolVectorDataPlug> > OutputBoolVectorDataPlugIterator;
[[deprecated("Use `IntVectorDataPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, IntVectorDataPlug> > IntVectorDataPlugIterator;
[[deprecated("Use `IntVectorDataPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, IntVectorDataPlug> > InputIntVectorDataPlugIterator;
[[deprecated("Use `IntVectorDataPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, IntVectorDataPlug> > OutputIntVectorDataPlugIterator;
[[deprecated("Use `FloatVectorDataPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, FloatVectorDataPlug> > FloatVectorDataPlugIterator;
[[deprecated("Use `FloatVectorDataPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, FloatVectorDataPlug> > InputFloatVectorDataPlugIterator;
[[deprecated("Use `FloatVectorDataPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, FloatVectorDataPlug> > OutputFloatVectorDataPlugIterator;
[[deprecated("Use `StringVectorDataPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, StringVectorDataPlug> > StringVectorDataPlugIterator;
[[deprecated("Use `StringVectorDataPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, StringVectorDataPlug> > InputStringVectorDataPlugIterator;
[[deprecated("Use `StringVectorDataPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, StringVectorDataPlug> > OutputStringVectorDataPlugIterator;
[[deprecated("Use `InternedStringVectorDataPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, InternedStringVectorDataPlug> > InternedStringVectorDataPlugIterator;
[[deprecated("Use `InternedStringVectorDataPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, InternedStringVectorDataPlug> > InputInternedStringVectorDataPlugIterator;
[[deprecated("Use `InternedStringVectorDataPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, InternedStringVectorDataPlug> > OutputInternedStringVectorDataPlugIterator;
[[deprecated("Use `V2iVectorDataPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, V2iVectorDataPlug> > V2iVectorDataPlugIterator;
[[deprecated("Use `V2iVectorDataPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, V2iVectorDataPlug> > InputV2iVectorDataPlugIterator;
[[deprecated("Use `V2iVectorDataPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, V2iVectorDataPlug> > OutputV2iVectorDataPlugIterator;
[[deprecated("Use `V3fVectorDataPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, V3fVectorDataPlug> > V3fVectorDataPlugIterator;
[[deprecated("Use `V3fVectorDataPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, V3fVectorDataPlug> > InputV3fVectorDataPlugIterator;
[[deprecated("Use `V3fVectorDataPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, V3fVectorDataPlug> > OutputV3fVectorDataPlugIterator;
[[deprecated("Use `Color3fVectorDataPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, Color3fVectorDataPlug> > Color3fVectorDataPlugIterator;
[[deprecated("Use `Color3fVectorDataPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, Color3fVectorDataPlug> > InputColor3fVectorDataPlugIterator;
[[deprecated("Use `Color3fVectorDataPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Color3fVectorDataPlug> > OutputColor3fVectorDataPlugIterator;
[[deprecated("Use `M44fVectorDataPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, M44fVectorDataPlug> > M44fVectorDataPlugIterator;
[[deprecated("Use `M44fVectorDataPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, M44fVectorDataPlug> > InputM44fVectorDataPlugIterator;
[[deprecated("Use `M44fVectorDataPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, M44fVectorDataPlug> > OutputM44fVectorDataPlugIterator;
[[deprecated("Use `M33fVectorDataPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, M33fVectorDataPlug> > M33fVectorDataPlugIterator;
[[deprecated("Use `M33fVectorDataPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, M33fVectorDataPlug> > InputM33fVectorDataPlugIterator;
[[deprecated("Use `M33fVectorDataPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, M33fVectorDataPlug> > OutputM33fVectorDataPlugIterator;
[[deprecated("Use `ObjectVectorPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, ObjectVectorPlug> > ObjectVectorPlugIterator;
[[deprecated("Use `ObjectVectorPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, ObjectVectorPlug> > InputObjectVectorPlugIterator;
[[deprecated("Use `ObjectVectorPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, ObjectVectorPlug> > OutputObjectVectorPlugIterator;
[[deprecated("Use `CompoundObjectPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, CompoundObjectPlug> > CompoundObjectPlugIterator;
[[deprecated("Use `CompoundObjectPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, CompoundObjectPlug> > InputCompoundObjectPlugIterator;
[[deprecated("Use `CompoundObjectPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, CompoundObjectPlug> > OutputCompoundObjectPlugIterator;
[[deprecated("Use `AtomicCompoundDataPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, AtomicCompoundDataPlug> > AtomicCompoundDataPlugIterator;
[[deprecated("Use `AtomicCompoundDataPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, AtomicCompoundDataPlug> > InputAtomicCompoundDataPlugIterator;
[[deprecated("Use `AtomicCompoundDataPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, AtomicCompoundDataPlug> > OutputAtomicCompoundDataPlugIterator;
[[deprecated("Use `ObjectPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, ObjectPlug>, PlugPredicate<> > RecursiveObjectPlugIterator;
[[deprecated("Use `ObjectPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, ObjectPlug>, PlugPredicate<> > RecursiveInputObjectPlugIterator;
[[deprecated("Use `ObjectPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, ObjectPlug>, PlugPredicate<> > RecursiveOutputObjectPlugIterator;
[[deprecated("Use `BoolVectorDataPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, BoolVectorDataPlug>, PlugPredicate<> > RecursiveBoolVectorDataPlugIterator;
[[deprecated("Use `BoolVectorDataPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, BoolVectorDataPlug>, PlugPredicate<> > RecursiveInputBoolVectorDataPlugIterator;
[[deprecated("Use `BoolVectorDataPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, BoolVectorDataPlug>, PlugPredicate<> > RecursiveOutputBoolVectorDataPlugIterator;
[[deprecated("Use `IntVectorDataPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, IntVectorDataPlug>, PlugPredicate<> > RecursiveIntVectorDataPlugIterator;
[[deprecated("Use `IntVectorDataPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, IntVectorDataPlug>, PlugPredicate<> > RecursiveInputIntVectorDataPlugIterator;
[[deprecated("Use `IntVectorDataPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, IntVectorDataPlug>, PlugPredicate<> > RecursiveOutputIntVectorDataPlugIterator;
[[deprecated("Use `FloatVectorDataPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, FloatVectorDataPlug>, PlugPredicate<> > RecursiveFloatVectorDataPlugIterator;
[[deprecated("Use `FloatVectorDataPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, FloatVectorDataPlug>, PlugPredicate<> > RecursiveInputFloatVectorDataPlugIterator;
[[deprecated("Use `FloatVectorDataPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, FloatVectorDataPlug>, PlugPredicate<> > RecursiveOutputFloatVectorDataPlugIterator;
[[deprecated("Use `StringVectorDataPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, StringVectorDataPlug>, PlugPredicate<> > RecursiveStringVectorDataPlugIterator;
[[deprecated("Use `StringVectorDataPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, StringVectorDataPlug>, PlugPredicate<> > RecursiveInputStringVectorDataPlugIterator;
[[deprecated("Use `StringVectorDataPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, StringVectorDataPlug>, PlugPredicate<> > RecursiveOutputStringVectorDataPlugIterator;
[[deprecated("Use `InternedStringVectorDataPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, InternedStringVectorDataPlug>, PlugPredicate<> > RecursiveInternedStringVectorDataPlugIterator;
[[deprecated("Use `InternedStringVectorDataPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, InternedStringVectorDataPlug>, PlugPredicate<> > RecursiveInputInternedStringVectorDataPlugIterator;
[[deprecated("Use `InternedStringVectorDataPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, InternedStringVectorDataPlug>, PlugPredicate<> > RecursiveOutputInternedStringVectorDataPlugIterator;
[[deprecated("Use `V2iVectorDataPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, V2iVectorDataPlug>, PlugPredicate<> > RecursiveV2iVectorDataPlugIterator;
[[deprecated("Use `V2iVectorDataPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, V2iVectorDataPlug>, PlugPredicate<> > RecursiveInputV2iVectorDataPlugIterator;
[[deprecated("Use `V2iVectorDataPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, V2iVectorDataPlug>, PlugPredicate<> > RecursiveOutputV2iVectorDataPlugIterator;
[[deprecated("Use `V3fVectorDataPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, V3fVectorDataPlug>, PlugPredicate<> > RecursiveV3fVectorDataPlugIterator;
[[deprecated("Use `V3fVectorDataPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, V3fVectorDataPlug>, PlugPredicate<> > RecursiveInputV3fVectorDataPlugIterator;
[[deprecated("Use `V3fVectorDataPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, V3fVectorDataPlug>, PlugPredicate<> > RecursiveOutputV3fVectorDataPlugIterator;
[[deprecated("Use `Color3fVectorDataPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, Color3fVectorDataPlug>, PlugPredicate<> > RecursiveColor3fVectorDataPlugIterator;
[[deprecated("Use `Color3fVectorDataPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Color3fVectorDataPlug>, PlugPredicate<> > RecursiveInputColor3fVectorDataPlugIterator;
[[deprecated("Use `Color3fVectorDataPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Color3fVectorDataPlug>, PlugPredicate<> > RecursiveOutputColor3fVectorDataPlugIterator;
[[deprecated("Use `M44fVectorDataPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, M44fVectorDataPlug>, PlugPredicate<> > RecursiveM44fVectorDataPlugIterator;
[[deprecated("Use `M44fVectorDataPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, M44fVectorDataPlug>, PlugPredicate<> > RecursiveInputM44fVectorDataPlugIterator;
[[deprecated("Use `M44fVectorDataPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, M44fVectorDataPlug>, PlugPredicate<> > RecursiveOutputM44fVectorDataPlugIterator;
[[deprecated("Use `M33fVectorDataPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, M33fVectorDataPlug>, PlugPredicate<> > RecursiveM33fVectorDataPlugIterator;
[[deprecated("Use `M33fVectorDataPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, M33fVectorDataPlug>, PlugPredicate<> > RecursiveInputM33fVectorDataPlugIterator;
[[deprecated("Use `M33fVectorDataPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, M33fVectorDataPlug>, PlugPredicate<> > RecursiveOutputM33fVectorDataPlugIterator;
[[deprecated("Use `ObjectVectorPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, ObjectVectorPlug>, PlugPredicate<> > RecursiveObjectVectorPlugIterator;
[[deprecated("Use `ObjectVectorPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, ObjectVectorPlug>, PlugPredicate<> > RecursiveInputObjectVectorPlugIterator;
[[deprecated("Use `ObjectVectorPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, ObjectVectorPlug>, PlugPredicate<> > RecursiveOutputObjectVectorPlugIterator;
[[deprecated("Use `CompoundObjectPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, CompoundObjectPlug>, PlugPredicate<> > RecursiveCompoundObjectPlugIterator;
[[deprecated("Use `CompoundObjectPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, CompoundObjectPlug>, PlugPredicate<> > RecursiveInputCompoundObjectPlugIterator;
[[deprecated("Use `CompoundObjectPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, CompoundObjectPlug>, PlugPredicate<> > RecursiveOutputCompoundObjectPlugIterator;
[[deprecated("Use `AtomicCompoundDataPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, AtomicCompoundDataPlug>, PlugPredicate<> > RecursiveAtomicCompoundDataPlugIterator;
[[deprecated("Use `AtomicCompoundDataPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, AtomicCompoundDataPlug>, PlugPredicate<> > RecursiveInputAtomicCompoundDataPlugIterator;
[[deprecated("Use `AtomicCompoundDataPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, AtomicCompoundDataPlug>, PlugPredicate<> > RecursiveOutputAtomicCompoundDataPlugIterator;
[[deprecated("Use `PathMatcherDataPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, PathMatcherDataPlug>, PlugPredicate<> > RecursivePathMatcherDataPlugIterator;
[[deprecated("Use `PathMatcherDataPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, PathMatcherDataPlug>, PlugPredicate<> > RecursiveInputPathMatcherDataPlugIterator;
[[deprecated("Use `PathMatcherDataPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, PathMatcherDataPlug>, PlugPredicate<> > RecursiveOutputPathMatcherDataPlugIterator;

} // namespace Gaffer

#endif // GAFFER_TYPEDOBJECTPLUG_H
