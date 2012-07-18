//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

		/// A copy of defaultValue is taken.
		TypedObjectPlug(
			const std::string &name = staticTypeName(),
			Direction direction=In,
			ConstValuePtr defaultValue = ValuePtr(),
			unsigned flags = Default
		);
		virtual ~TypedObjectPlug();

		/// Accepts only instances of TypedObjectPlug<T>, or derived classes.
		virtual bool acceptsInput( const Plug *input ) const;

		ConstValuePtr defaultValue() const;

		/// \undoable
		/// \todo This is taking a copy - does that cause terrible performance?
		void setValue( ConstValuePtr value );
		/// Returns the value.
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
typedef TypedObjectPlug<IECore::V3fVectorData> V3fVectorDataPlug;
typedef TypedObjectPlug<IECore::ObjectVector> ObjectVectorPlug;
typedef TypedObjectPlug<IECore::Primitive> PrimitivePlug;

IE_CORE_DECLAREPTR( ObjectPlug );
IE_CORE_DECLAREPTR( BoolVectorDataPlug );
IE_CORE_DECLAREPTR( IntVectorDataPlug );
IE_CORE_DECLAREPTR( FloatVectorDataPlug );
IE_CORE_DECLAREPTR( StringVectorDataPlug );
IE_CORE_DECLAREPTR( V3fVectorDataPlug );
IE_CORE_DECLAREPTR( ObjectVectorPlug );
IE_CORE_DECLAREPTR( PrimitivePlug );

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

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, V3fVectorDataPlug> > V3fVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, V3fVectorDataPlug> > InputV3fVectorDataPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, V3fVectorDataPlug> > OutputV3fVectorDataPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, ObjectVectorPlug> > ObjectVectorPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, ObjectVectorPlug> > InputObjectVectorPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, ObjectVectorPlug> > OutputObjectVectorPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, PrimitivePlug> > PrimitivePlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, PrimitivePlug> > InputPrimitivePlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, PrimitivePlug> > OutputPrimitivePlugIterator;

} // namespace Gaffer

#endif // GAFFER_TYPEDOBJECTPLUG_H
