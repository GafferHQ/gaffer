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

		using ValueType = T;
		using ValuePtr = typename ValueType::Ptr;
		using ConstValuePtr = typename ValueType::ConstPtr;

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

#if !defined( Gaffer_EXPORTS ) && !defined( _MSC_VER )

extern template class TypedObjectPlug<IECore::Object>;
extern template class TypedObjectPlug<IECore::BoolVectorData>;
extern template class TypedObjectPlug<IECore::IntVectorData>;
extern template class TypedObjectPlug<IECore::FloatVectorData>;
extern template class TypedObjectPlug<IECore::StringVectorData>;
extern template class TypedObjectPlug<IECore::InternedStringVectorData>;
extern template class TypedObjectPlug<IECore::V2iVectorData>;
extern template class TypedObjectPlug<IECore::V3iVectorData>;
extern template class TypedObjectPlug<IECore::V2fVectorData>;
extern template class TypedObjectPlug<IECore::V3fVectorData>;
extern template class TypedObjectPlug<IECore::Color3fVectorData>;
extern template class TypedObjectPlug<IECore::M44fVectorData>;
extern template class TypedObjectPlug<IECore::M33fVectorData>;
extern template class TypedObjectPlug<IECore::ObjectVector>;
extern template class TypedObjectPlug<IECore::CompoundObject>;
extern template class TypedObjectPlug<IECore::CompoundData>;
extern template class TypedObjectPlug<IECore::PathMatcherData>;

#endif

using ObjectPlug = TypedObjectPlug<IECore::Object>;
using BoolVectorDataPlug = TypedObjectPlug<IECore::BoolVectorData>;
using IntVectorDataPlug = TypedObjectPlug<IECore::IntVectorData>;
using FloatVectorDataPlug = TypedObjectPlug<IECore::FloatVectorData>;
using StringVectorDataPlug = TypedObjectPlug<IECore::StringVectorData>;
using InternedStringVectorDataPlug = TypedObjectPlug<IECore::InternedStringVectorData>;
using V2iVectorDataPlug = TypedObjectPlug<IECore::V2iVectorData>;
using V3iVectorDataPlug = TypedObjectPlug<IECore::V3iVectorData>;
using V2fVectorDataPlug = TypedObjectPlug<IECore::V2fVectorData>;
using V3fVectorDataPlug = TypedObjectPlug<IECore::V3fVectorData>;
using Color3fVectorDataPlug = TypedObjectPlug<IECore::Color3fVectorData>;
using M44fVectorDataPlug = TypedObjectPlug<IECore::M44fVectorData>;
using M33fVectorDataPlug = TypedObjectPlug<IECore::M33fVectorData>;
using ObjectVectorPlug = TypedObjectPlug<IECore::ObjectVector>;
using CompoundObjectPlug = TypedObjectPlug<IECore::CompoundObject>;
using AtomicCompoundDataPlug = TypedObjectPlug<IECore::CompoundData>;
using PathMatcherDataPlug = TypedObjectPlug<IECore::PathMatcherData>;

IE_CORE_DECLAREPTR( ObjectPlug );
IE_CORE_DECLAREPTR( BoolVectorDataPlug );
IE_CORE_DECLAREPTR( IntVectorDataPlug );
IE_CORE_DECLAREPTR( FloatVectorDataPlug );
IE_CORE_DECLAREPTR( StringVectorDataPlug );
IE_CORE_DECLAREPTR( InternedStringVectorDataPlug );
IE_CORE_DECLAREPTR( V2iVectorDataPlug );
IE_CORE_DECLAREPTR( V3iVectorDataPlug );
IE_CORE_DECLAREPTR( V2fVectorDataPlug );
IE_CORE_DECLAREPTR( V3fVectorDataPlug );
IE_CORE_DECLAREPTR( Color3fVectorDataPlug );
IE_CORE_DECLAREPTR( M44fVectorDataPlug );
IE_CORE_DECLAREPTR( M33fVectorDataPlug );
IE_CORE_DECLAREPTR( ObjectVectorPlug );
IE_CORE_DECLAREPTR( CompoundObjectPlug );
IE_CORE_DECLAREPTR( AtomicCompoundDataPlug );
IE_CORE_DECLAREPTR( PathMatcherDataPlug );

} // namespace Gaffer

#endif // GAFFER_TYPEDOBJECTPLUG_H
