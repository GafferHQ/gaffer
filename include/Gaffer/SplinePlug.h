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

#include "IECore/Spline.h"

#include "Gaffer/CompoundPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/TypedPlug.h"
#include "Gaffer/PlugType.h"

namespace Gaffer
{

/// The SplinePlug allows IECore::Splines to be represented and
/// manipulated. Rather than storing a value atomically, the
/// points and basis matrix are represented as individual plugs,
/// allowing the positions of individual points to have input
/// connections from other nodes. For many common splines, it's
/// useful to repeat the endpoint values to force interpolation
/// all the way to the first and last values, but dealing with
/// such repeated endpoints in scripting and via the user interface
/// would be awkward. For this reason, the setValue() method removes
/// duplicate endpoints, storing the number of duplicates in the
/// endPointMultiplicity plug. When calling getValue(), the
/// endPointMultiplicity is then used to restore the duplicate endpoints.
template<typename T>
class SplinePlug : public CompoundPlug
{

	public :

		typedef T ValueType;
		typedef typename PlugType<typename T::XType>::Type XPlugType;
		typedef typename PlugType<typename T::YType>::Type YPlugType;

		IECORE_RUNTIMETYPED_DECLARETEMPLATE( SplinePlug<T>, CompoundPlug );
		IE_CORE_DECLARERUNTIMETYPEDDESCRIPTION( SplinePlug<T> );

		SplinePlug(
			const std::string &name = defaultName<SplinePlug>(),
			Direction direction=In,
			const T &defaultValue = T(),
			unsigned flags = Default
		);
		virtual ~SplinePlug();

		/// Implemented to only accept children which are suitable for use as points
		/// in the spline.
		virtual bool acceptsChild( const GraphComponent *potentialChild ) const;
		virtual PlugPtr createCounterpart( const std::string &name, Direction direction ) const;

		const T &defaultValue() const;
		virtual void setToDefault();

		/// Sets the value of all the child plugs by decomposing
		/// the passed spline and storing it in the basis, points,
		/// and endPointMultiplicity plug.
		/// \undoable
		void setValue( const T &value );
		/// Recreates the spline by retrieving its basis and points
		/// from the basis, points and endPointMultiplicity plugs.
		T getValue() const;

		CompoundPlug *basisPlug();
		const CompoundPlug *basisPlug() const;
		M44fPlug *basisMatrixPlug();
		const M44fPlug *basisMatrixPlug() const;
		IntPlug *basisStepPlug();
		const IntPlug *basisStepPlug() const;

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

		CompoundPlug *pointPlug( unsigned pointIndex );
		const CompoundPlug *pointPlug( unsigned pointIndex ) const;
		XPlugType *pointXPlug( unsigned pointIndex );
		const XPlugType *pointXPlug( unsigned pointIndex ) const;
		YPlugType *pointYPlug( unsigned pointIndex );
		const YPlugType *pointYPlug( unsigned pointIndex ) const;

		IntPlug *endPointMultiplicityPlug();
		const IntPlug *endPointMultiplicityPlug() const;

	private :

		size_t endPointMultiplicity( const T &value ) const;

		T m_defaultValue;

};

typedef SplinePlug<IECore::Splineff> SplineffPlug;
typedef SplinePlug<IECore::SplinefColor3f> SplinefColor3fPlug;

IE_CORE_DECLAREPTR( SplineffPlug );
IE_CORE_DECLAREPTR( SplinefColor3fPlug );

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, SplineffPlug> > SplineffPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, SplineffPlug> > InputSplineffPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, SplineffPlug> > OutputSplineffPlugIterator;

typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, SplinefColor3fPlug> > SplinefColor3fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, SplinefColor3fPlug> > InputSplinefColor3fPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, SplinefColor3fPlug> > OutputSplinefColor3fPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, SplineffPlug>, PlugPredicate<> > RecursiveSplineffPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, SplineffPlug>, PlugPredicate<> > RecursiveInputSplineffPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, SplineffPlug>, PlugPredicate<> > RecursiveOutputSplineffPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, SplinefColor3fPlug>, PlugPredicate<> > RecursiveSplinefColor3fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, SplinefColor3fPlug>, PlugPredicate<> > RecursiveInputSplinefColor3fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, SplinefColor3fPlug>, PlugPredicate<> > RecursiveOutputSplinefColor3fPlugIterator;

} // namespace Gaffer

#endif // GAFFER_SPLINEPLUG_H
