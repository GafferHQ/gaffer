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

#include "Gaffer/NumericPlug.h"

#include "IECore/Export.h"
#include "IECore/GeometricTypedData.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/ImathColor.h"
#include "OpenEXR/ImathVec.h"
IECORE_POP_DEFAULT_VISIBILITY

namespace Gaffer
{

template<typename T>
class GAFFER_API CompoundNumericPlug : public ValuePlug
{

	public :

		typedef T ValueType;
		typedef NumericPlug<typename T::BaseType> ChildType;

		GAFFER_PLUG_DECLARE_TEMPLATE_TYPE( CompoundNumericPlug<T>, ValuePlug );

		CompoundNumericPlug(
			const std::string &name = defaultName<CompoundNumericPlug>(),
			Direction direction=In,
			T defaultValue = T( 0 ),
			T minValue = T( Imath::limits<typename T::BaseType>::min() ),
			T maxValue = T( Imath::limits<typename T::BaseType>::max() ),
			unsigned flags = Default,
			IECore::GeometricData::Interpretation interpretation = IECore::GeometricData::None
		);
		~CompoundNumericPlug() override;
		/// Accepts no children following construction.
		bool acceptsChild( const GraphComponent *potentialChild ) const override;
		PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		using GraphComponent::getChild;
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

		/// Returns a hash to represent the value of this plug
		/// in the current context.
		IECore::MurmurHash hash() const override;
		/// Convenience function to append the hash to h.
		void hash( IECore::MurmurHash &h ) const;

		/// Returns the interpretation of the vector
		IECore::GeometricData::Interpretation interpretation() const;

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

		static const char **childNames();
		const IECore::GeometricData::Interpretation m_interpretation;

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

[[deprecated("Use `V2fPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, V2fPlug> > V2fPlugIterator;
[[deprecated("Use `V2fPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, V2fPlug> > InputV2fPlugIterator;
[[deprecated("Use `V2fPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, V2fPlug> > OutputV2fPlugIterator;
[[deprecated("Use `V3fPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, V3fPlug> > V3fPlugIterator;
[[deprecated("Use `V3fPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, V3fPlug> > InputV3fPlugIterator;
[[deprecated("Use `V3fPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, V3fPlug> > OutputV3fPlugIterator;
[[deprecated("Use `V2iPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, V2iPlug> > V2iPlugIterator;
[[deprecated("Use `V2iPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, V2iPlug> > InputV2iPlugIterator;
[[deprecated("Use `V2iPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, V2iPlug> > OutputV2iPlugIterator;
[[deprecated("Use `V3iPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, V3iPlug> > V3iPlugIterator;
[[deprecated("Use `V3iPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, V3iPlug> > InputV3iPlugIterator;
[[deprecated("Use `V3iPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, V3iPlug> > OutputV3iPlugIterator;
[[deprecated("Use `Color3fPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, Color3fPlug> > Color3fPlugIterator;
[[deprecated("Use `Color3fPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, Color3fPlug> > InputColor3fPlugIterator;
[[deprecated("Use `Color3fPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Color3fPlug> > OutputColor3fPlugIterator;
[[deprecated("Use `Color4fPlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, Color4fPlug> > Color4fPlugIterator;
[[deprecated("Use `Color4fPlug::InputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::In, Color4fPlug> > InputColor4fPlugIterator;
[[deprecated("Use `Color4fPlug::OutputIterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Color4fPlug> > OutputColor4fPlugIterator;
[[deprecated("Use `V2fPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, V2fPlug>, PlugPredicate<> > RecursiveV2fPlugIterator;
[[deprecated("Use `V2fPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, V2fPlug>, PlugPredicate<> > RecursiveInputV2fPlugIterator;
[[deprecated("Use `V2fPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, V2fPlug>, PlugPredicate<> > RecursiveOutputV2fPlugIterator;
[[deprecated("Use `V3fPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, V3fPlug>, PlugPredicate<> > RecursiveV3fPlugIterator;
[[deprecated("Use `V3fPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, V3fPlug>, PlugPredicate<> > RecursiveInputV3fPlugIterator;
[[deprecated("Use `V3fPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, V3fPlug>, PlugPredicate<> > RecursiveOutputV3fPlugIterator;
[[deprecated("Use `V2iPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, V2iPlug>, PlugPredicate<> > RecursiveV2iPlugIterator;
[[deprecated("Use `V2iPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, V2iPlug>, PlugPredicate<> > RecursiveInputV2iPlugIterator;
[[deprecated("Use `V2iPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, V2iPlug>, PlugPredicate<> > RecursiveOutputV2iPlugIterator;
[[deprecated("Use `V3iPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, V3iPlug>, PlugPredicate<> > RecursiveV3iPlugIterator;
[[deprecated("Use `V3iPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, V3iPlug>, PlugPredicate<> > RecursiveInputV3iPlugIterator;
[[deprecated("Use `V3iPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, V3iPlug>, PlugPredicate<> > RecursiveOutputV3iPlugIterator;
[[deprecated("Use `Color3fPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, Color3fPlug>, PlugPredicate<> > RecursiveColor3fPlugIterator;
[[deprecated("Use `Color3fPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Color3fPlug>, PlugPredicate<> > RecursiveInputColor3fPlugIterator;
[[deprecated("Use `Color3fPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Color3fPlug>, PlugPredicate<> > RecursiveOutputColor3fPlugIterator;
[[deprecated("Use `Color4fPlug::RecursiveIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, Color4fPlug>, PlugPredicate<> > RecursiveColor4fPlugIterator;
[[deprecated("Use `Color4fPlug::RecursiveInputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Color4fPlug>, PlugPredicate<> > RecursiveInputColor4fPlugIterator;
[[deprecated("Use `Color4fPlug::RecursiveOutputIterator` instead")]]
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Color4fPlug>, PlugPredicate<> > RecursiveOutputColor4fPlugIterator;

} // namespace Gaffer

#endif // GAFFER_COMPOUNDNUMERICPLUG_H
