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

#pragma once

#include "Gaffer/ValuePlug.h"

#include "IECore/SimpleTypedData.h"

namespace Gaffer
{

template<typename T>
class IECORE_EXPORT TypedPlug : public ValuePlug
{

	public :

		using ValueType = T;

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

		using DataType = IECore::TypedData<T>;
		using DataTypePtr = typename DataType::Ptr;

};

using BoolPlug = TypedPlug<bool>;
using M33fPlug = TypedPlug<Imath::M33f>;
using M44fPlug = TypedPlug<Imath::M44f>;
using AtomicBox2fPlug = TypedPlug<Imath::Box2f>;
using AtomicBox3fPlug = TypedPlug<Imath::Box3f>;
using AtomicBox2iPlug = TypedPlug<Imath::Box2i>;

IE_CORE_DECLAREPTR( BoolPlug );
IE_CORE_DECLAREPTR( M33fPlug );
IE_CORE_DECLAREPTR( M44fPlug );
IE_CORE_DECLAREPTR( AtomicBox2fPlug );
IE_CORE_DECLAREPTR( AtomicBox3fPlug );
IE_CORE_DECLAREPTR( AtomicBox2iPlug );

} // namespace Gaffer
