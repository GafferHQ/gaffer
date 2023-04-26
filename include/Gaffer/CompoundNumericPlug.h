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

#pragma once

#include "Gaffer/NumericPlug.h"

#include "IECore/Export.h"
#include "IECore/GeometricTypedData.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathColor.h"
#include "OpenEXR/ImathVec.h"
#else
#include "Imath/ImathColor.h"
#include "Imath/ImathVec.h"
#endif
IECORE_POP_DEFAULT_VISIBILITY

namespace Gaffer
{

template<typename T>
class GAFFER_API CompoundNumericPlug : public ValuePlug
{

	public :

		using ValueType = T;
		using ChildType = NumericPlug<typename T::BaseType>;

		GAFFER_PLUG_DECLARE_TEMPLATE_TYPE( CompoundNumericPlug<T>, ValuePlug );

		explicit CompoundNumericPlug(
			const std::string &name = defaultName<CompoundNumericPlug>(),
			Direction direction=In,
			T defaultValue = T( 0 ),
			T minValue = T( std::numeric_limits<typename T::BaseType>::lowest() ),
			T maxValue = T( std::numeric_limits<typename T::BaseType>::max() ),
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

using V2fPlug = CompoundNumericPlug<Imath::V2f>;
using V3fPlug = CompoundNumericPlug<Imath::V3f>;

using V2iPlug = CompoundNumericPlug<Imath::V2i>;
using V3iPlug = CompoundNumericPlug<Imath::V3i>;

using Color3fPlug = CompoundNumericPlug<Imath::Color3f>;
using Color4fPlug = CompoundNumericPlug<Imath::Color4f>;

IE_CORE_DECLAREPTR( V2fPlug );
IE_CORE_DECLAREPTR( V3fPlug );
IE_CORE_DECLAREPTR( V2iPlug );
IE_CORE_DECLAREPTR( V3iPlug );
IE_CORE_DECLAREPTR( Color3fPlug );
IE_CORE_DECLAREPTR( Color4fPlug );

} // namespace Gaffer
