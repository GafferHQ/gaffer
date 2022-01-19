//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Matti Gruener. All rights reserved.
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

#ifndef GAFFERUI_ANIMATIONGADGET_H
#define GAFFERUI_ANIMATIONGADGET_H

#include "GafferUI/Gadget.h"

#include "Gaffer/Animation.h"
#include "Gaffer/StandardSet.h"

namespace Gaffer
{

	IE_CORE_FORWARDDECLARE( Context );

}

namespace GafferUI
{

class GAFFERUI_API AnimationGadget : public Gadget
{
	public :

		AnimationGadget();
		~AnimationGadget() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::AnimationGadget, AnimationGadgetTypeId, Gadget );

		Gaffer::StandardSet *visiblePlugs();
		const Gaffer::StandardSet *visiblePlugs() const;

		Gaffer::StandardSet *editablePlugs();
		const Gaffer::StandardSet *editablePlugs() const;

		void setContext( Gaffer::Context *context );
		Gaffer::Context *getContext() const;

		Gaffer::Set *selectedKeys();
		const Gaffer::Set *selectedKeys() const;

		bool onTimeAxis( const IECore::LineSegment3f& line ) const;
		bool onValueAxis( const IECore::LineSegment3f& line ) const;

		std::string getToolTip( const IECore::LineSegment3f &line ) const override;

	protected :

		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override;
		unsigned layerMask() const override;
		Imath::Box3f renderBound() const override;

	private :

		struct SelectionSet;
		IE_CORE_DECLAREPTR( SelectionSet )

		/// \undoable
		void insertKeyframe( Gaffer::Animation::CurvePlug *curvePlug, float time );
		/// \undoable
		void insertKeyframes();
		/// \undoable
		void removeKeyframes();
		/// \undoable
		void removeInactiveKeyframes();
		/// \undoable
		void moveKeyframes( const Imath::V2f currentDragOffset );
		/// \undoable
		void moveTangent( const Imath::V2f currentDragOffset );

		void frame();

		void plugDirtied( Gaffer::Plug *plug );

		bool buttonPress( GadgetPtr gadget, const ButtonEvent &event );
		bool buttonRelease( GadgetPtr gadget, const ButtonEvent &event );
		bool keyPress( GadgetPtr gadget, const KeyEvent &event );
		bool keyRelease( GadgetPtr gadget, const KeyEvent &event );

		bool mouseMove( GadgetPtr gadget, const ButtonEvent &event );
		IECore::RunTimeTypedPtr dragBegin( GadgetPtr gadget, const DragDropEvent &event );
		bool dragEnter( GadgetPtr gadget, const DragDropEvent &event );
		bool dragMove( GadgetPtr gadget, const DragDropEvent &event );
		bool dragEnd( GadgetPtr gadget, const DragDropEvent &event );
		bool leave();

		// Find elements at certain positions
		Gaffer::Animation::ConstKeyPtr keyAt( const IECore::LineSegment3f &position ) const;
		Gaffer::Animation::KeyPtr keyAt( const IECore::LineSegment3f &position );
		std::pair<Gaffer::Animation::ConstKeyPtr, Gaffer::Animation::Direction> tangentAt( const IECore::LineSegment3f &position ) const;
		std::pair<Gaffer::Animation::KeyPtr, Gaffer::Animation::Direction> tangentAt( const IECore::LineSegment3f &position );
		Gaffer::Animation::ConstCurvePlugPtr curveAt( const IECore::LineSegment3f &position ) const;
		Gaffer::Animation::CurvePlugPtr curveAt( const IECore::LineSegment3f &position );
		bool frameIndicatorUnderMouse( const IECore::LineSegment3f &position ) const;

		void visiblePlugAdded( Gaffer::Set *set, IECore::RunTimeTyped *member );
		void visiblePlugRemoved( Gaffer::Set *set, IECore::RunTimeTyped *member );

		void editablePlugAdded( Gaffer::Set *set, IECore::RunTimeTyped *member );
		void editablePlugRemoved( Gaffer::Set *set, IECore::RunTimeTyped *member );

		void renderCurve( const Gaffer::Animation::CurvePlug *curvePlug, const Style *style ) const;
		void renderFrameIndicator( int frame, const Style *style, bool preview=false, float lineWidth=2.0 ) const;

		bool plugSetAcceptor( const Gaffer::Set *s, const Gaffer::Set::Member *m );
		void updateKeyPreviewLocation( const Gaffer::Animation::CurvePlug *curvePlug, float time );

		std::string undoMergeGroup() const;

		Gaffer::Context *m_context;

		Gaffer::StandardSetPtr m_visiblePlugs;
		Gaffer::StandardSetPtr m_editablePlugs;

		SelectionSetPtr m_selectedKeys;

		std::map< const Gaffer::Animation::Key*, std::pair< float, float > > m_originalKeyValues;

		Gaffer::Animation::KeyPtr m_dragTangentKey;
		Gaffer::Animation::Direction m_dragTangentDirection;
		double m_dragTangentOriginalScale;

		Imath::V2f m_dragStartPosition;
		Imath::V2f m_lastDragPosition;

		enum class DragMode
		{
			None,
			Selecting,
			Moving,
			MoveFrame,
			MoveTangent
		};

		DragMode m_dragMode;

		enum class MoveAxis
		{
			Both,
			Undefined,
			X,
			Y
		};

		MoveAxis m_moveAxis;

		Gaffer::Animation::KeyPtr m_snappingClosestKey;
		Gaffer::Animation::KeyPtr m_highlightedKey;
		Gaffer::Animation::CurvePlugPtr m_highlightedCurve;
		Gaffer::Animation::KeyPtr m_highlightedTangentKey;
		Gaffer::Animation::Direction m_highlightedTangentDirection;

		int m_mergeGroupId;

		bool m_keyPreview;
		Imath::V3f m_keyPreviewLocation;

		// details regarding spacing and layouting
		int m_xMargin;
		int m_yMargin;
		int m_textScale;
		int m_labelPadding;

		std::optional<int> m_frameIndicatorPreviewFrame;

};

IE_CORE_DECLAREPTR( AnimationGadget );

} // namespace GafferUI

#endif // GAFFERUI_ANIMATIONGADGET_H
