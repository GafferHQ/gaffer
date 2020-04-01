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
#include "IECore/SimpleTypedData.h"

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
extern template class TypedObjectPlug<IECore::InternedStringData>;
extern template class TypedObjectPlug<IECore::BoolVectorData>;
extern template class TypedObjectPlug<IECore::IntVectorData>;
extern template class TypedObjectPlug<IECore::FloatVectorData>;
extern template class TypedObjectPlug<IECore::StringVectorData>;
extern template class TypedObjectPlug<IECore::InternedStringVectorData>;
extern template class TypedObjectPlug<IECore::V2iVectorData>;
extern template class TypedObjectPlug<IECore::V3fVectorData>;
extern template class TypedObjectPlug<IECore::Color3fVectorData>;
extern template class TypedObjectPlug<IECore::M44fVectorData>;
extern template class TypedObjectPlug<IECore::ObjectVector>;
extern template class TypedObjectPlug<IECore::CompoundObject>;
extern template class TypedObjectPlug<IECore::CompoundData>;
extern template class TypedObjectPlug<IECore::PathMatcherData>;

#endif

typedef TypedObjectPlug<IECore::Object> ObjectPlug;
typedef TypedObjectPlug<IECore::InternedStringData> InternedStringDataPlug;
typedef TypedObjectPlug<IECore::BoolVectorData> BoolVectorDataPlug;
typedef TypedObjectPlug<IECore::IntVectorData> IntVectorDataPlug;
typedef TypedObjectPlug<IECore::FloatVectorData> FloatVectorDataPlug;
typedef TypedObjectPlug<IECore::StringVectorData> StringVectorDataPlug;
typedef TypedObjectPlug<IECore::InternedStringVectorData> InternedStringVectorDataPlug;
typedef TypedObjectPlug<IECore::V2iVectorData> V2iVectorDataPlug;
typedef TypedObjectPlug<IECore::V3fVectorData> V3fVectorDataPlug;
typedef TypedObjectPlug<IECore::Color3fVectorData> Color3fVectorDataPlug;
typedef TypedObjectPlug<IECore::M44fVectorData> M44fVectorDataPlug;
typedef TypedObjectPlug<IECore::ObjectVector> ObjectVectorPlug;
typedef TypedObjectPlug<IECore::CompoundObject> CompoundObjectPlug;
typedef TypedObjectPlug<IECore::CompoundData> AtomicCompoundDataPlug;
typedef TypedObjectPlug<IECore::PathMatcherData> PathMatcherDataPlug;

IE_CORE_DECLAREPTR( ObjectPlug );
IE_CORE_DECLAREPTR( InternedStringDataPlug );
IE_CORE_DECLAREPTR( BoolVectorDataPlug );
IE_CORE_DECLAREPTR( IntVectorDataPlug );
IE_CORE_DECLAREPTR( FloatVectorDataPlug );
IE_CORE_DECLAREPTR( StringVectorDataPlug );
IE_CORE_DECLAREPTR( InternedStringVectorDataPlug );
IE_CORE_DECLAREPTR( V2iVectorDataPlug );
IE_CORE_DECLAREPTR( V3fVectorDataPlug );
IE_CORE_DECLAREPTR( Color3fVectorDataPlug );
IE_CORE_DECLAREPTR( M44fVectorDataPlug );
IE_CORE_DECLAREPTR( ObjectVectorPlug );
IE_CORE_DECLAREPTR( CompoundObjectPlug );
IE_CORE_DECLAREPTR( AtomicCompoundDataPlug );
IE_CORE_DECLAREPTR( PathMatcherDataPlug );

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, ObjectPlug> > ObjectPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, ObjectPlug> > InputObjectPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, ObjectPlug> > OutputObjectPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, InternedStringDataPlug> > InternedStringDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, InternedStringDataPlug> > InputInternedStringDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, InternedStringDataPlug> > OutputInternedStringDataPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, BoolVectorDataPlug> > BoolVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, BoolVectorDataPlug> > InputBoolVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, BoolVectorDataPlug> > OutputBoolVectorDataPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, IntVectorDataPlug> > IntVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, IntVectorDataPlug> > InputIntVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, IntVectorDataPlug> > OutputIntVectorDataPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, FloatVectorDataPlug> > FloatVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, FloatVectorDataPlug> > InputFloatVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, FloatVectorDataPlug> > OutputFloatVectorDataPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, StringVectorDataPlug> > StringVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, StringVectorDataPlug> > InputStringVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, StringVectorDataPlug> > OutputStringVectorDataPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, InternedStringVectorDataPlug> > InternedStringVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, InternedStringVectorDataPlug> > InputInternedStringVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, InternedStringVectorDataPlug> > OutputInternedStringVectorDataPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, V2iVectorDataPlug> > V2iVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, V2iVectorDataPlug> > InputV2iVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, V2iVectorDataPlug> > OutputV2iVectorDataPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, V3fVectorDataPlug> > V3fVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, V3fVectorDataPlug> > InputV3fVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, V3fVectorDataPlug> > OutputV3fVectorDataPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, Color3fVectorDataPlug> > Color3fVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, Color3fVectorDataPlug> > InputColor3fVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Color3fVectorDataPlug> > OutputColor3fVectorDataPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, M44fVectorDataPlug> > M44fVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, M44fVectorDataPlug> > InputM44fVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, M44fVectorDataPlug> > OutputM44fVectorDataPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, ObjectVectorPlug> > ObjectVectorPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, ObjectVectorPlug> > InputObjectVectorPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, ObjectVectorPlug> > OutputObjectVectorPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, CompoundObjectPlug> > CompoundObjectPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, CompoundObjectPlug> > InputCompoundObjectPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, CompoundObjectPlug> > OutputCompoundObjectPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, AtomicCompoundDataPlug> > AtomicCompoundDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, AtomicCompoundDataPlug> > InputAtomicCompoundDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, AtomicCompoundDataPlug> > OutputAtomicCompoundDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, ObjectPlug>, PlugPredicate<> > RecursiveObjectPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, ObjectPlug>, PlugPredicate<> > RecursiveInputObjectPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, ObjectPlug>, PlugPredicate<> > RecursiveOutputObjectPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, InternedStringDataPlug>, PlugPredicate<> > RecursiveInternedStringDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, InternedStringDataPlug>, PlugPredicate<> > RecursiveInputInternedStringDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, InternedStringDataPlug>, PlugPredicate<> > RecursiveOutputInternedStringDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, BoolVectorDataPlug>, PlugPredicate<> > RecursiveBoolVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, BoolVectorDataPlug>, PlugPredicate<> > RecursiveInputBoolVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, BoolVectorDataPlug>, PlugPredicate<> > RecursiveOutputBoolVectorDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, IntVectorDataPlug>, PlugPredicate<> > RecursiveIntVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, IntVectorDataPlug>, PlugPredicate<> > RecursiveInputIntVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, IntVectorDataPlug>, PlugPredicate<> > RecursiveOutputIntVectorDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, FloatVectorDataPlug>, PlugPredicate<> > RecursiveFloatVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, FloatVectorDataPlug>, PlugPredicate<> > RecursiveInputFloatVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, FloatVectorDataPlug>, PlugPredicate<> > RecursiveOutputFloatVectorDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, StringVectorDataPlug>, PlugPredicate<> > RecursiveStringVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, StringVectorDataPlug>, PlugPredicate<> > RecursiveInputStringVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, StringVectorDataPlug>, PlugPredicate<> > RecursiveOutputStringVectorDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, InternedStringVectorDataPlug>, PlugPredicate<> > RecursiveInternedStringVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, InternedStringVectorDataPlug>, PlugPredicate<> > RecursiveInputInternedStringVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, InternedStringVectorDataPlug>, PlugPredicate<> > RecursiveOutputInternedStringVectorDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, V2iVectorDataPlug>, PlugPredicate<> > RecursiveV2iVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, V2iVectorDataPlug>, PlugPredicate<> > RecursiveInputV2iVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, V2iVectorDataPlug>, PlugPredicate<> > RecursiveOutputV2iVectorDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, V3fVectorDataPlug>, PlugPredicate<> > RecursiveV3fVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, V3fVectorDataPlug>, PlugPredicate<> > RecursiveInputV3fVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, V3fVectorDataPlug>, PlugPredicate<> > RecursiveOutputV3fVectorDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, Color3fVectorDataPlug>, PlugPredicate<> > RecursiveColor3fVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Color3fVectorDataPlug>, PlugPredicate<> > RecursiveInputColor3fVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Color3fVectorDataPlug>, PlugPredicate<> > RecursiveOutputColor3fVectorDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, M44fVectorDataPlug>, PlugPredicate<> > RecursiveM44fVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, M44fVectorDataPlug>, PlugPredicate<> > RecursiveInputM44fVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, M44fVectorDataPlug>, PlugPredicate<> > RecursiveOutputM44fVectorDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, ObjectVectorPlug>, PlugPredicate<> > RecursiveObjectVectorPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, ObjectVectorPlug>, PlugPredicate<> > RecursiveInputObjectVectorPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, ObjectVectorPlug>, PlugPredicate<> > RecursiveOutputObjectVectorPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, CompoundObjectPlug>, PlugPredicate<> > RecursiveCompoundObjectPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, CompoundObjectPlug>, PlugPredicate<> > RecursiveInputCompoundObjectPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, CompoundObjectPlug>, PlugPredicate<> > RecursiveOutputCompoundObjectPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, AtomicCompoundDataPlug>, PlugPredicate<> > RecursiveAtomicCompoundDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, AtomicCompoundDataPlug>, PlugPredicate<> > RecursiveInputAtomicCompoundDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, AtomicCompoundDataPlug>, PlugPredicate<> > RecursiveOutputAtomicCompoundDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, PathMatcherDataPlug>, PlugPredicate<> > RecursivePathMatcherDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, PathMatcherDataPlug>, PlugPredicate<> > RecursiveInputPathMatcherDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, PathMatcherDataPlug>, PlugPredicate<> > RecursiveOutputPathMatcherDataPlugIterator;

} // namespace Gaffer

#endif // GAFFER_TYPEDOBJECTPLUG_H
