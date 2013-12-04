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

#ifndef GAFFER_TYPEDPLUG_H
#define GAFFER_TYPEDPLUG_H

#include "OpenEXR/ImathMatrix.h"

#include "IECore/SimpleTypedData.h"

#include "Gaffer/ValuePlug.h"

namespace Gaffer
{

template<typename T>
class TypedPlug : public ValuePlug
{

	public :

		typedef T ValueType;

		IECORE_RUNTIMETYPED_DECLARETEMPLATE( TypedPlug<T>, ValuePlug );

		TypedPlug(
			const std::string &name = defaultName<TypedPlug>(),
			Direction direction=In,
			const T &defaultValue = T(),
			unsigned flags = Default
		);
		virtual ~TypedPlug();

		/// Accepts only instances of TypedPlug<T> or derived classes.
		virtual bool acceptsInput( const Plug *input ) const;
		virtual PlugPtr createCounterpart( const std::string &name, Direction direction ) const;

		const T &defaultValue() const;

		/// \undoable
		void setValue( const T &value );
		/// Returns the value.
		T getValue() const;

		virtual void setToDefault();
		virtual void setFrom( const ValuePlug *other );

		/// Implemented to perform automatic substitutions
		/// for string plugs.
		virtual IECore::MurmurHash hash() const;
		/// Just calls ValuePlug::hash( h ) - only
		/// exists to workaround the problem of the
		/// function above masking this function on
		/// the base class.
		void hash( IECore::MurmurHash &h ) const;
		
	private :

		IE_CORE_DECLARERUNTIMETYPEDDESCRIPTION( TypedPlug<T> );		

		typedef IECore::TypedData<T> DataType;
		typedef typename DataType::Ptr DataTypePtr;
	
		T m_defaultValue;

};

typedef TypedPlug<bool> BoolPlug;
typedef TypedPlug<std::string> StringPlug;
typedef TypedPlug<Imath::M33f> M33fPlug;
typedef TypedPlug<Imath::M44f> M44fPlug;
typedef TypedPlug<Imath::Box3f> AtomicBox3fPlug;
typedef TypedPlug<Imath::Box2i> AtomicBox2iPlug;

IE_CORE_DECLAREPTR( BoolPlug );
IE_CORE_DECLAREPTR( StringPlug );
IE_CORE_DECLAREPTR( M33fPlug );
IE_CORE_DECLAREPTR( M44fPlug );
IE_CORE_DECLAREPTR( AtomicBox3fPlug );
IE_CORE_DECLAREPTR( AtomicBox2iPlug );

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, BoolPlug> > BoolPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, BoolPlug> > InputBoolPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, BoolPlug> > OutputBoolPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, StringPlug> > StringPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, StringPlug> > InputStringPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, StringPlug> > OutputStringPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, M33fPlug> > M33fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, M33fPlug> > InputM33fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, M33fPlug> > OutputM33fPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, M44fPlug> > M44fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, M44fPlug> > InputM44fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, M44fPlug> > OutputM44fPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, AtomicBox3fPlug> > AtomicBox3fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, AtomicBox3fPlug> > InputAtomicBox3fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, AtomicBox3fPlug> > OutputAtomicBox3fPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, AtomicBox2iPlug> > AtomicBox2iPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, AtomicBox2iPlug> > InputAtomicBox2iPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, AtomicBox2iPlug> > OutputAtomicBox2iPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, BoolPlug>, PlugPredicate<> > RecursiveBoolPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, BoolPlug>, PlugPredicate<> > RecursiveInputBoolPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, BoolPlug>, PlugPredicate<> > RecursiveOutputBoolPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, StringPlug>, PlugPredicate<> > RecursiveStringPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, StringPlug>, PlugPredicate<> > RecursiveInputStringPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, StringPlug>, PlugPredicate<> > RecursiveOutputStringPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, M33fPlug>, PlugPredicate<> > RecursiveM33fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, M33fPlug>, PlugPredicate<> > RecursiveInputM33fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, M33fPlug>, PlugPredicate<> > RecursiveOutputM33fPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, M44fPlug>, PlugPredicate<> > RecursiveM44fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, M44fPlug>, PlugPredicate<> > RecursiveInputM44fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, M44fPlug>, PlugPredicate<> > RecursiveOutputM44fPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, AtomicBox3fPlug>, PlugPredicate<> > RecursiveAtomicBox3fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, AtomicBox3fPlug>, PlugPredicate<> > RecursiveInputAtomicBox3fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, AtomicBox3fPlug>, PlugPredicate<> > RecursiveOutputAtomicBox3fPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, AtomicBox2iPlug>, PlugPredicate<> > RecursiveAtomicBox2iPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, AtomicBox2iPlug>, PlugPredicate<> > RecursiveInputAtomicBox2iPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, AtomicBox2iPlug>, PlugPredicate<> > RecursiveOutputAtomicBox2iPlugIterator;

} // namespace Gaffer

#endif // GAFFER_TYPEDPLUG_H
