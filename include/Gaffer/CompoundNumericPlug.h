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

#ifndef GAFFER_COMPOUNDNUMERICPLUG_H
#define GAFFER_COMPOUNDNUMERICPLUG_H

#include "OpenEXR/ImathVec.h"
#include "OpenEXR/ImathColor.h"

#include "Gaffer/CompoundPlug.h"
#include "Gaffer/NumericPlug.h"

namespace Gaffer
{

template<typename T>
class CompoundNumericPlug : public CompoundPlug
{

	public :

		typedef T ValueType;
		typedef NumericPlug<typename T::BaseType> ChildType;
		
		IECORE_RUNTIMETYPED_DECLARETEMPLATE( CompoundNumericPlug<T>, CompoundPlug );

		CompoundNumericPlug(
			const std::string &name = defaultName<CompoundNumericPlug>(),
			Direction direction=In,
			T defaultValue = T( 0 ),
			T minValue = T( Imath::limits<typename T::BaseType>::min() ),
			T maxValue = T( Imath::limits<typename T::BaseType>::max() ),
			unsigned flags = Default
		);
		virtual ~CompoundNumericPlug();

		/// Accepts no children following construction.
		virtual bool acceptsChild( const GraphComponent *potentialChild ) const;
		virtual PlugPtr createCounterpart( const std::string &name, Direction direction ) const;

		ChildType *getChild( size_t index );
		const ChildType *getChild( size_t index ) const;	

		T defaultValue() const;
		
		bool hasMinValue() const;
		bool hasMaxValue() const;

		T minValue() const;
		T maxValue() const;
		
		/// Calls setValue for each of the child plugs, passing the components
		/// of value.
		/// \undoable
		void setValue( const T &value );
		/// Returns the value, calling getValue() on each child plug to compute a component
		/// of the result.
		T getValue() const;
		
		/// @name Ganging
		/// CompoundNumericPlugs may be ganged by connecting the child plugs
		/// together so their values are driven by the first child. These
		/// methods allow the children to be ganged and unganged, and for their
		/// ganging status to be queried.
		////////////////////////////////////////////////////////////////////
		//@{
		bool canGang() const;
		/// \undoable
		void gang();
		bool isGanged() const;
		/// \undoable
		void ungang();
		//@}
		
	private :
	
		IE_CORE_DECLARERUNTIMETYPEDDESCRIPTION( CompoundNumericPlug<T> );

		static const char **childNames();
	
};

typedef CompoundNumericPlug<Imath::V2f> V2fPlug;
typedef CompoundNumericPlug<Imath::V3f> V3fPlug;

typedef CompoundNumericPlug<Imath::V2i> V2iPlug;
typedef CompoundNumericPlug<Imath::V3i> V3iPlug;

typedef CompoundNumericPlug<Imath::Color3f> Color3fPlug;
typedef CompoundNumericPlug<Imath::Color4f> Color4fPlug;

IE_CORE_DECLAREPTR( V2fPlug );
IE_CORE_DECLAREPTR( V3fPlug );
IE_CORE_DECLAREPTR( V2iPlug );
IE_CORE_DECLAREPTR( V3iPlug );
IE_CORE_DECLAREPTR( Color3fPlug );
IE_CORE_DECLAREPTR( Color4fPlug );

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, V2fPlug> > V2fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, V2fPlug> > InputV2fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, V2fPlug> > OutputV2fPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, V3fPlug> > V3fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, V3fPlug> > InputV3fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, V3fPlug> > OutputV3fPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, V2iPlug> > V2iPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, V2iPlug> > InputV2iPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, V2iPlug> > OutputV2iPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, V3iPlug> > V3iPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, V3iPlug> > InputV3iPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, V3iPlug> > OutputV3iPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, Color3fPlug> > Color3fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, Color3fPlug> > InputColor3fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Color3fPlug> > OutputColor3fPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, Color4fPlug> > Color4fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, Color4fPlug> > InputColor4fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Color4fPlug> > OutputColor4fPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, V2fPlug>, PlugPredicate<> > RecursiveV2fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, V2fPlug>, PlugPredicate<> > RecursiveInputV2fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, V2fPlug>, PlugPredicate<> > RecursiveOutputV2fPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, V3fPlug>, PlugPredicate<> > RecursiveV3fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, V3fPlug>, PlugPredicate<> > RecursiveInputV3fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, V3fPlug>, PlugPredicate<> > RecursiveOutputV3fPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, V2iPlug>, PlugPredicate<> > RecursiveV2iPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, V2iPlug>, PlugPredicate<> > RecursiveInputV2iPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, V2iPlug>, PlugPredicate<> > RecursiveOutputV2iPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, V3iPlug>, PlugPredicate<> > RecursiveV3iPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, V3iPlug>, PlugPredicate<> > RecursiveInputV3iPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, V3iPlug>, PlugPredicate<> > RecursiveOutputV3iPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, Color3fPlug>, PlugPredicate<> > RecursiveColor3fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Color3fPlug>, PlugPredicate<> > RecursiveInputColor3fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Color3fPlug>, PlugPredicate<> > RecursiveOutputColor3fPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, Color4fPlug>, PlugPredicate<> > RecursiveColor4fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Color4fPlug>, PlugPredicate<> > RecursiveInputColor4fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Color4fPlug>, PlugPredicate<> > RecursiveOutputColor4fPlugIterator;

} // namespace Gaffer

#endif // GAFFER_COMPOUNDNUMERICPLUG_H
