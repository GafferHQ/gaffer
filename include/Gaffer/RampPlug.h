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
#include "Gaffer/PlugType.h"
#include "Gaffer/TypedPlug.h"

#include "IECore/Ramp.h"

namespace Gaffer
{

/// The RampPlug allows the user to manipulate an IECore::Ramp, which is
/// a simple curve representation with a list of control points and an
/// interpolations.
//
/// Rather than storing the value atomically, the
/// points and interpolation are represented as individual plugs,
/// allowing the positions of individual points to have input
/// connections from other nodes.

template<typename T>
class GAFFER_API RampPlug : public ValuePlug
{

	public :

		using ValueType = T;
		using XPlugType = typename PlugType<typename T::XType>::Type;
		using YPlugType = typename PlugType<typename T::YType>::Type;

		GAFFER_PLUG_DECLARE_TEMPLATE_TYPE( RampPlug<T>, ValuePlug );

		explicit RampPlug(
			const std::string &name = defaultName<RampPlug>(),
			Direction direction=In,
			const T &defaultValue = T(),
			unsigned flags = Default
		);
		~RampPlug() override;

		/// Implemented to only accept children which are suitable for use as points
		/// in the spline.
		bool acceptsChild( const GraphComponent *potentialChild ) const override;
		PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		const T &defaultValue() const;
		void setToDefault() override;
		bool isSetToDefault() const override;
		void resetDefault() override;
		IECore::MurmurHash defaultHash() const override;

		/// Sets the value of the points and interpolation child plugs
		/// \undoable
		void setValue( const T &value );
		/// Matching to setValue
		T getValue() const;

		IntPlug *interpolationPlug();
		const IntPlug *interpolationPlug() const;

		/// Returns the number of point plugs - note that
		/// because duplicate endpoints are not stored directly as
		/// plugs, this may differ from the number of points
		/// in the spline passed to setValue().
		unsigned numPoints() const;
		/// \undoable
		unsigned addPoint();
		/// \undoable
		void removePoint( unsigned pointIndex );
		/// \undoable
		void clearPoints();

		ValuePlug *pointPlug( unsigned pointIndex );
		const ValuePlug *pointPlug( unsigned pointIndex ) const;
		XPlugType *pointXPlug( unsigned pointIndex );
		const XPlugType *pointXPlug( unsigned pointIndex ) const;
		YPlugType *pointYPlug( unsigned pointIndex );
		const YPlugType *pointYPlug( unsigned pointIndex ) const;

	private :

		T m_defaultValue;
};

using RampffPlug = RampPlug<IECore::Rampff>;
using RampfColor3fPlug = RampPlug<IECore::RampfColor3f>;
using RampfColor4fPlug = RampPlug<IECore::RampfColor4f>;

IE_CORE_DECLAREPTR( RampffPlug );
IE_CORE_DECLAREPTR( RampfColor3fPlug );
IE_CORE_DECLAREPTR( RampfColor4fPlug );

} // namespace Gaffer
