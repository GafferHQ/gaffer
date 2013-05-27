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

#include "IECore/Object.h"
#include "IECore/VectorTypedData.h"
#include "IECore/ObjectVector.h"
#include "IECore/Primitive.h"
#include "IECore/CompoundObject.h"

#include "Gaffer/ValuePlug.h"
#include "Gaffer/PlugIterator.h"

namespace Gaffer
{

/// A Plug type which can store values derived from IECore::Object.
template<typename T>
class TypedObjectPlug : public ValuePlug
{

	public :

		typedef T ValueType;
		typedef IECore::IntrusivePtr<T> ValuePtr;
		typedef IECore::IntrusivePtr<const T> ConstValuePtr;

		IECORE_RUNTIMETYPED_DECLARETEMPLATE( TypedObjectPlug<T>, ValuePlug );

		/// A copy of defaultValue is taken - it must not be null.
		TypedObjectPlug(
			const std::string &name,
			Direction direction,
			ConstValuePtr defaultValue,
			unsigned flags = Default
		);
		virtual ~TypedObjectPlug();

		/// Accepts only instances of TypedObjectPlug<T>, or derived classes.
		virtual bool acceptsInput( const Plug *input ) const;
		virtual PlugPtr createCounterpart( const std::string &name, Direction direction ) const;

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
		ConstValuePtr getValue() const;

		virtual void setToDefault();
		virtual void setFrom( const ValuePlug *other );

	private :

		IE_CORE_DECLARERUNTIMETYPEDDESCRIPTION( TypedObjectPlug<T> );		
	
		ConstValuePtr m_defaultValue;

};

typedef TypedObjectPlug<IECore::Object> ObjectPlug;
typedef TypedObjectPlug<IECore::BoolVectorData> BoolVectorDataPlug;
typedef TypedObjectPlug<IECore::IntVectorData> IntVectorDataPlug;
typedef TypedObjectPlug<IECore::FloatVectorData> FloatVectorDataPlug;
typedef TypedObjectPlug<IECore::StringVectorData> StringVectorDataPlug;
typedef TypedObjectPlug<IECore::InternedStringVectorData> InternedStringVectorDataPlug;
typedef TypedObjectPlug<IECore::V3fVectorData> V3fVectorDataPlug;
typedef TypedObjectPlug<IECore::Color3fVectorData> Color3fVectorDataPlug;
typedef TypedObjectPlug<IECore::ObjectVector> ObjectVectorPlug;
typedef TypedObjectPlug<IECore::CompoundObject> CompoundObjectPlug;

IE_CORE_DECLAREPTR( ObjectPlug );
IE_CORE_DECLAREPTR( BoolVectorDataPlug );
IE_CORE_DECLAREPTR( IntVectorDataPlug );
IE_CORE_DECLAREPTR( FloatVectorDataPlug );
IE_CORE_DECLAREPTR( StringVectorDataPlug );
IE_CORE_DECLAREPTR( InternedStringVectorDataPlug );
IE_CORE_DECLAREPTR( V3fVectorDataPlug );
IE_CORE_DECLAREPTR( Color3fVectorDataPlug );
IE_CORE_DECLAREPTR( ObjectVectorPlug );
IE_CORE_DECLAREPTR( CompoundObjectPlug );

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, ObjectPlug> > ObjectPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, ObjectPlug> > InputObjectPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, ObjectPlug> > OutputObjectPlugIterator;

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

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, V3fVectorDataPlug> > V3fVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, V3fVectorDataPlug> > InputV3fVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, V3fVectorDataPlug> > OutputV3fVectorDataPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, Color3fVectorDataPlug> > Color3fVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, Color3fVectorDataPlug> > InputColor3fVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Color3fVectorDataPlug> > OutputColor3fVectorDataPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, ObjectVectorPlug> > ObjectVectorPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, ObjectVectorPlug> > InputObjectVectorPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, ObjectVectorPlug> > OutputObjectVectorPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, CompoundObjectPlug> > CompoundObjectPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, CompoundObjectPlug> > InputCompoundObjectPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, CompoundObjectPlug> > OutputCompoundObjectPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, ObjectPlug> > RecursiveObjectPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, ObjectPlug> > RecursiveInputObjectPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, ObjectPlug> > RecursiveOutputObjectPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, BoolVectorDataPlug> > RecursiveBoolVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, BoolVectorDataPlug> > RecursiveInputBoolVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, BoolVectorDataPlug> > RecursiveOutputBoolVectorDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, IntVectorDataPlug> > RecursiveIntVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, IntVectorDataPlug> > RecursiveInputIntVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, IntVectorDataPlug> > RecursiveOutputIntVectorDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, FloatVectorDataPlug> > RecursiveFloatVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, FloatVectorDataPlug> > RecursiveInputFloatVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, FloatVectorDataPlug> > RecursiveOutputFloatVectorDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, StringVectorDataPlug> > RecursiveStringVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, StringVectorDataPlug> > RecursiveInputStringVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, StringVectorDataPlug> > RecursiveOutputStringVectorDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, InternedStringVectorDataPlug> > RecursiveInternedStringVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, InternedStringVectorDataPlug> > RecursiveInputInternedStringVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, InternedStringVectorDataPlug> > RecursiveOutputInternedStringVectorDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, V3fVectorDataPlug> > RecursiveV3fVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, V3fVectorDataPlug> > RecursiveInputV3fVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, V3fVectorDataPlug> > RecursiveOutputV3fVectorDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, Color3fVectorDataPlug> > RecursiveColor3fVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Color3fVectorDataPlug> > RecursiveInputColor3fVectorDataPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Color3fVectorDataPlug> > RecursiveOutputColor3fVectorDataPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, ObjectVectorPlug> > RecursiveObjectVectorPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, ObjectVectorPlug> > RecursiveInputObjectVectorPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, ObjectVectorPlug> > RecursiveOutputObjectVectorPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, CompoundObjectPlug> > RecursiveCompoundObjectPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, CompoundObjectPlug> > RecursiveInputCompoundObjectPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, CompoundObjectPlug> > RecursiveOutputCompoundObjectPlugIterator;

} // namespace Gaffer

#endif // GAFFER_TYPEDOBJECTPLUG_H
