//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_SPLINEPLUGGADGET_H
#define GAFFERUI_SPLINEPLUGGADGET_H

#include "GafferUI/Export.h"
#include "GafferUI/Gadget.h"

#include "Gaffer/SplinePlug.h"
#include "Gaffer/StandardSet.h"

namespace GafferUI
{

/// \todo I think this should work with any sort of Set for the splines.
class GAFFERUI_API SplinePlugGadget : public Gadget
{

	public :

		SplinePlugGadget( const std::string &name=defaultName<SplinePlugGadget>() );
		virtual ~SplinePlugGadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::SplinePlugGadget, SplinePlugGadgetTypeId, Gadget );

		/// The splines to be edited
		Gaffer::StandardSetPtr splines();
		Gaffer::ConstStandardSetPtr splines() const;

		/// The selected spline points
		Gaffer::StandardSetPtr selection();
		Gaffer::ConstStandardSetPtr selection() const;

		virtual Imath::Box3f bound() const;

	protected :

		virtual void doRender( const Style *style ) const;

	private :

		void splineAdded( Gaffer::SetPtr splineSet, IECore::RunTimeTypedPtr splinePlug );
		void splineRemoved( Gaffer::SetPtr splineSet, IECore::RunTimeTypedPtr splinePlug );
		void plugSet( Gaffer::Plug *plug );
		Gaffer::StandardSetPtr m_splines;
		Gaffer::StandardSetPtr m_selection;

		void pointAdded( Gaffer::GraphComponentPtr spline, Gaffer::GraphComponentPtr point );
		void pointRemoved( Gaffer::GraphComponentPtr spline, Gaffer::GraphComponentPtr point );

		bool selectionAcceptance( Gaffer::ConstStandardSetPtr selection, IECore::ConstRunTimeTypedPtr point );

		struct UI;
		typedef std::map<Gaffer::Plug *, UI> SplineUIMap;
		mutable SplineUIMap m_uis;
		void updateCurve( SplineUIMap::iterator it ) const;

		bool buttonPress( GadgetPtr gadget, const ButtonEvent &event );
		IECore::RunTimeTypedPtr dragBegin( GadgetPtr gadget, const ButtonEvent &event );
		bool dragMove( GadgetPtr gadget, const ButtonEvent &event );
		Imath::V2f m_lastDragPosition;

		bool keyPress( GadgetPtr gadget, const KeyEvent &event );

};

IE_CORE_DECLAREPTR( SplinePlugGadget )

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<SplinePlugGadget> > SplinePlugGadgetIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<SplinePlugGadget> > RecursiveSplinePlugGadgetIterator;

} // namespace GafferUI

#endif // GAFFERUI_SPLINEPLUGGADGET_H
