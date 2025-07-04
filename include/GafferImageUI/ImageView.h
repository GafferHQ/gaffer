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

#include "GafferImageUI/Export.h"
#include "GafferImageUI/TypeIds.h"

#include "GafferUI/View.h"

#include "Gaffer/BoxPlug.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/ContextVariables.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/Switch.h"
#include "Gaffer/TypedPlug.h"
#include "Gaffer/TypedObjectPlug.h"

#include <functional>
#include <memory>

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferImage
{

IE_CORE_FORWARDDECLARE( ImagePlug )

} // namespace GafferImage

namespace GafferImageUI
{

IE_CORE_FORWARDDECLARE( ImageGadget )

/// \todo Refactor this into smaller components, along the lines of the SceneView class.
/// Consider redesigning the View/Tool classes so that view functionality can be built up
/// by adding tools like samplers etc.
class GAFFERIMAGEUI_API ImageView : public GafferUI::View
{

	public :

		explicit ImageView( Gaffer::ScriptNodePtr scriptNode );
		~ImageView() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImageUI::ImageView, ImageViewTypeId, GafferUI::View );

		Gaffer::StringVectorDataPlug *channelsPlug();
		const Gaffer::StringVectorDataPlug *channelsPlug() const;

		Gaffer::StringPlug *viewPlug();
		const Gaffer::StringPlug *viewPlug() const;
		Gaffer::StringPlug *compareModePlug();
		const Gaffer::StringPlug *compareModePlug() const;
		Gaffer::BoolPlug *compareWipePlug();
		const Gaffer::BoolPlug *compareWipePlug() const;
		GafferImage::ImagePlug *compareImagePlug();
		const GafferImage::ImagePlug *compareImagePlug() const;
		Gaffer::StringPlug *compareCatalogueOutputPlug();
		const Gaffer::StringPlug *compareCatalogueOutputPlug() const;
		Gaffer::BoolPlug *compareMatchDisplayWindowsPlug();
		const Gaffer::BoolPlug *compareMatchDisplayWindowsPlug() const;

		/// The gadget responsible for displaying the image.
		ImageGadget *imageGadget();
		const ImageGadget *imageGadget() const;

	protected :

		/// May be called from a subclass constructor to add a converter
		/// from non-image input types, allowing them to be viewed as images.
		/// The converter must have an "in" Plug (of any desired type), and
		/// convert the incoming data to an image to view on an "out" ImagePlug.
		/// \note If the necessary conversion requires several nodes, a Box
		/// provides a means of packaging them to meet these requirements.
		/// \note Subclasses are not allowed to call setPreprocessor() as the
		/// preprocessor is managed by the ImageView base class.
		void insertConverter( Gaffer::NodePtr converter );

	private :

		void contextChanged();
		void plugSet( Gaffer::Plug *plug );
		bool keyPress( const GafferUI::KeyEvent &event );
		void preRender();

		void setWipeActive( bool active );

		ImageGadgetPtr m_imageGadgets[2];
		bool m_framed;

		IE_CORE_FORWARDDECLARE( WipeHandle );
		WipeHandlePtr m_wipeHandle;

		Gaffer::ContextVariablesPtr m_comparisonSelect;
		static ViewDescription<ImageView> g_viewDescription;

};

IE_CORE_DECLAREPTR( ImageView );

} // namespace GafferImageUI
