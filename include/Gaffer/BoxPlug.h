//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "Gaffer/CompoundNumericPlug.h"

#include "IECore/BoxTraits.h"
#include "IECore/Export.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/ImathBox.h"
IECORE_POP_DEFAULT_VISIBILITY

namespace Gaffer
{

template<typename T>
class GAFFER_API BoxPlug : public ValuePlug
{

	public :

		using ValueType = T;
		using PointType = typename IECore::BoxTraits<T>::BaseType;
		using ChildType = CompoundNumericPlug<PointType>;

		GAFFER_PLUG_DECLARE_TEMPLATE_TYPE( BoxPlug<T>, ValuePlug );

		BoxPlug(
			const std::string &name = defaultName<BoxPlug>(),
			Direction direction=In,
			T defaultValue = T(),
			unsigned flags = Default
		);

		BoxPlug(
			const std::string &name,
			Direction direction,
			T defaultValue,
			const PointType &minValue,
			const PointType &maxValue,
			unsigned flags = Default
		);

		~BoxPlug() override;

		/// Accepts no children following construction.
		bool acceptsChild( const GraphComponent *potentialChild ) const override;
		PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		ChildType *minPlug();
		const ChildType *minPlug() const;

		ChildType *maxPlug();
		const ChildType *maxPlug() const;

		T defaultValue() const;

		bool hasMinValue() const;
		bool hasMaxValue() const;

		PointType minValue() const;
		PointType maxValue() const;

		/// Calls setValue for the min and max child plugs, using the min and max of
		/// value.
		/// \undoable
		void setValue( const T &value );
		/// Returns the value, calling getValue() on the min and max child plugs to compute a component
		/// of the result.
		T getValue() const;

};

using Box2iPlug = BoxPlug<Imath::Box2i>;
using Box3iPlug = BoxPlug<Imath::Box3i>;

using Box2fPlug = BoxPlug<Imath::Box2f>;
using Box3fPlug = BoxPlug<Imath::Box3f>;

IE_CORE_DECLAREPTR( Box2iPlug );
IE_CORE_DECLAREPTR( Box3iPlug );

IE_CORE_DECLAREPTR( Box2fPlug );
IE_CORE_DECLAREPTR( Box3fPlug );

} // namespace Gaffer
