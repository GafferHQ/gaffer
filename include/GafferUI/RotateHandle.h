//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, John Haddon. All rights reserved.
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

#include "GafferUI/Handle.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathEuler.h"
#else
#include "Imath/ImathEuler.h"
#endif
IECORE_POP_DEFAULT_VISIBILITY

namespace GafferUI
{

class GAFFERUI_API RotateHandle : public Handle
{

	public :

		explicit RotateHandle( Style::Axes axes );
		~RotateHandle() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::RotateHandle, RotateHandleTypeId, Handle );

		void setAxes( Style::Axes axes );
		Style::Axes getAxes() const;

		// Returns a vector where each component is 0 or 1,
		// indicating whether or not the handle will produce
		// rotation in that axis.
		Imath::V3i axisMask() const;

		// Measured in radians
		Imath::Eulerf rotation( const DragDropEvent &event );

	protected :

		void renderHandle( const Style *style, Style::State state ) const override;
		void dragBegin( const DragDropEvent &event ) override;

	private :

		bool dragMove( const DragDropEvent &event );
		bool mouseMove( const ButtonEvent &event );
		Imath::V3f pointOnSphere( const IECore::LineSegment3f &line ) const;

		void updatePreciseMotionState( const DragDropEvent &event );
		IECore::LineSegment3f updatedLineFromEvent( const DragDropEvent &event ) const;

		Style::Axes m_axes;
		// For X, Y and Z handles.
		AngularDrag m_drag;
		float m_rotation;
		// For free rotation handle.
		Imath::M44f m_dragBeginWorldTransform;
		Imath::V3f m_dragBeginPointOnSphere;
		Imath::V3f m_highlightVector;

		bool m_preciseMotionEnabled;
		IECore::LineSegment3f m_preciseMotionOriginLine;

};

IE_CORE_DECLAREPTR( RotateHandle )

} // namespace GafferUI
