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

#ifndef GAFFER_SPLINEPLUG_H
#define GAFFER_SPLINEPLUG_H

#include "Gaffer/NumericPlug.h"
#include "Gaffer/PlugType.h"
#include "Gaffer/TypedPlug.h"

#include "IECore/Spline.h"

namespace Gaffer
{

// This lives outside the class because we don't want multiple incompatible templated versions of
// the same enum floating around
enum SplineDefinitionInterpolation
{
	SplineDefinitionInterpolationLinear,
	SplineDefinitionInterpolationCatmullRom,
	SplineDefinitionInterpolationBSpline,
	SplineDefinitionInterpolationMonotoneCubic,
};


template<typename T>
struct GAFFER_API SplineDefinition
{
	typedef typename T::XType XType;
	typedef typename T::YType YType;
	typedef typename T::PointContainer PointContainer;
	typedef typename PointContainer::value_type Point;

	SplineDefinition() : interpolation( SplineDefinitionInterpolationCatmullRom )
	{
	}

	SplineDefinition( const PointContainer &p, SplineDefinitionInterpolation i )
		: points( p ), interpolation( i )
	{
	}

	PointContainer points;
	SplineDefinitionInterpolation interpolation;


	// Convert to Cortex Spline
	T spline() const;

	// If you are starting with a curve representation that needs duplicated end point values, and you're
	// converting it into this representation, you need to trim off the duplicated end point values,
	// and you can do that with this method
	bool trimEndPoints();

	bool operator==( const SplineDefinition<T> &rhs ) const
	{
		return interpolation == rhs.interpolation && points == rhs.points;
	}

	bool operator!=( const SplineDefinition<T> &rhs ) const
	{
		return interpolation != rhs.interpolation || points != rhs.points;
	}

private:
	int endPointMultiplicity() const;
};

/// The SplinePlug allows the user to manipulate splines that can be
/// converted to IECore::Splines. It's value is a very simple and easy to edit
/// spline representation named SplineDefinition - just a list of control points
/// with one of the interpolations above.
//
/// Rather than storing the value atomically, the
/// points and interpolation are represented as individual plugs,
/// allowing the positions of individual points to have input
/// connections from other nodes.
///
/// The value stored should be a clean, user editable value.  Underlying technical
/// details such as adding repeated endpoint values are added when converting to
/// IECore::Spline.
template<typename T>
class GAFFER_API SplinePlug : public ValuePlug
{

	public :

		typedef T ValueType;
		typedef typename PlugType<typename T::XType>::Type XPlugType;
		typedef typename PlugType<typename T::YType>::Type YPlugType;

		GAFFER_PLUG_DECLARE_TEMPLATE_TYPE( SplinePlug<T>, ValuePlug );

		SplinePlug(
			const std::string &name = defaultName<SplinePlug>(),
			Direction direction=In,
			const T &defaultValue = T(),
			unsigned flags = Default
		);
		~SplinePlug() override;

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

typedef SplineDefinition<IECore::Splineff> SplineDefinitionff;
typedef SplineDefinition<IECore::SplinefColor3f> SplineDefinitionfColor3f;
typedef SplineDefinition<IECore::SplinefColor4f> SplineDefinitionfColor4f;

typedef SplinePlug< SplineDefinitionff > SplineffPlug;
typedef SplinePlug< SplineDefinitionfColor3f > SplinefColor3fPlug;
typedef SplinePlug< SplineDefinitionfColor4f > SplinefColor4fPlug;

IE_CORE_DECLAREPTR( SplineffPlug );
IE_CORE_DECLAREPTR( SplinefColor3fPlug );
IE_CORE_DECLAREPTR( SplinefColor4fPlug );

} // namespace Gaffer

#endif // GAFFER_SPLINEPLUG_H
