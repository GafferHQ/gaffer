//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

#ifndef GAFFER_NUMERICPLUG_H
#define GAFFER_NUMERICPLUG_H

#include "OpenEXR/ImathLimits.h"

#include "IECore/SimpleTypedData.h"

#include "Gaffer/ValuePlug.h"

namespace Gaffer
{

template<typename T>
class NumericPlug : public ValuePlug
{

	public :

		typedef T ValueType;

		IECORE_RUNTIMETYPED_DECLARETEMPLATE( NumericPlug<T>, ValuePlug );

		NumericPlug(
			const std::string &name = defaultName<NumericPlug>(),
			Direction direction=In,
			T defaultValue = T(),
			T minValue = Imath::limits<T>::min(),
			T maxValue = Imath::limits<T>::max(),
			unsigned flags = Default
		);
		virtual ~NumericPlug();

		/// Accepts other NumericPlugs, including those of different types.
		virtual bool acceptsInput( const Plug *input ) const;
		virtual PlugPtr createCounterpart( const std::string &name, Direction direction ) const;

		T defaultValue() const;
		
		bool hasMinValue() const;
		bool hasMaxValue() const;

		T minValue() const;
		T maxValue() const;
		
		/// Clamps the value between min and max.
		/// \undoable
		void setValue( T value );
		/// Returns the value.
		T getValue() const;

		virtual void setToDefault();
		virtual void setFrom( const ValuePlug *other );

	private :
	
		IE_CORE_DECLARERUNTIMETYPEDDESCRIPTION( NumericPlug<T> );

		typedef IECore::TypedData<T> DataType;
		typedef typename DataType::Ptr DataTypePtr;
			
		T m_defaultValue;
		T m_minValue;
		T m_maxValue;

};

typedef NumericPlug<float> FloatPlug;
typedef NumericPlug<int> IntPlug;

IE_CORE_DECLAREPTR( FloatPlug );
IE_CORE_DECLAREPTR( IntPlug );

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, FloatPlug> > FloatPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, FloatPlug> > InputFloatPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, FloatPlug> > OutputFloatPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, IntPlug> > IntPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, IntPlug> > InputIntPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, IntPlug> > OutputIntPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, FloatPlug> > RecursiveFloatPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, FloatPlug> > RecursiveInputFloatPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, FloatPlug> > RecursiveOutputFloatPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, IntPlug> > RecursiveIntPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, IntPlug> > RecursiveInputIntPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, IntPlug> > RecursiveOutputIntPlugIterator;

} // namespace Gaffer

#endif // GAFFER_NUMERICPLUG_H
