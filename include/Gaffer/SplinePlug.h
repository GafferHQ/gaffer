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
			const std::string &name = staticTypeName(),
			Direction direction=In,
			const T &defaultValue = T(),
			unsigned flags = Default
		);
		virtual ~SplinePlug();

		/// Implemented to only accept children which are suitable for use as points
		/// in the spline.
		virtual bool acceptsChild( const GraphComponent *potentialChild ) const;

		const T &defaultValue() const;
		virtual void setToDefault();
		
		/// \undoable
		void setValue( const T &value );
		T getValue() const;
		
		CompoundPlugPtr basisPlug();
		ConstCompoundPlugPtr basisPlug() const;
		M44fPlugPtr basisMatrixPlug();
		ConstM44fPlugPtr basisMatrixPlug() const;
		IntPlugPtr basisStepPlug();
		ConstIntPlugPtr basisStepPlug() const;
		
		unsigned numPoints() const;
		/// \undoable
		unsigned addPoint();
		/// \undoable
		void removePoint( unsigned pointIndex );
		/// \undoable
		void clearPoints();

		CompoundPlugPtr pointPlug( unsigned pointIndex );
		ConstCompoundPlugPtr pointPlug( unsigned pointIndex ) const;
		typename XPlugType::Ptr pointXPlug( unsigned pointIndex );
		typename XPlugType::ConstPtr pointXPlug( unsigned pointIndex ) const;
		typename YPlugType::Ptr pointYPlug( unsigned pointIndex );
		typename YPlugType::ConstPtr pointYPlug( unsigned pointIndex ) const;

	private :

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

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, SplineffPlug> > RecursiveSplineffPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, SplineffPlug> > RecursiveInputSplineffPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, SplineffPlug> > RecursiveOutputSplineffPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, SplinefColor3fPlug> > RecursiveSplinefColor3fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, SplinefColor3fPlug> > RecursiveInputSplinefColor3fPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, SplinefColor3fPlug> > RecursiveOutputSplinefColor3fPlugIterator;

} // namespace Gaffer

#endif // GAFFER_SPLINEPLUG_H
