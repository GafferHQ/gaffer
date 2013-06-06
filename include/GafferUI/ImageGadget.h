//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFERUI_IMAGEGADGET_H
#define GAFFERUI_IMAGEGADGET_H

#include "IECore/ImagePrimitive.h"

#include "GafferUI/Gadget.h"

namespace IECoreGL
{

IE_CORE_FORWARDDECLARE( Texture )

} // namespace IECoreGL

namespace GafferUI
{

class ImageGadget : public Gadget
{

	public :

		/// Images are searched for on the paths defined by
		/// the GAFFERUI_IMAGE_PATHS environment variable.
		/// Throws if the file cannot be loaded.
		ImageGadget( const std::string &fileName );
		/// A copy of the image is taken.
		ImageGadget( const IECore::ConstImagePrimitivePtr image );
		virtual ~ImageGadget();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::ImageGadget, ImageGadgetTypeId, Gadget );

		virtual Imath::Box3f bound() const;
			
	protected :
	
		virtual void doRender( const Style *style ) const;

	private :
		
		Imath::Box3f m_bound;
		// We can't actually generate the GL texture until doRender(), as
		// the GL state might not be valid until then. so we store either
		// the image to convert, the filename to load, or the previously
		// converted texture in this member.
		mutable IECore::ConstRunTimeTypedPtr m_imageOrTextureOrFileName;
		
};

IE_CORE_DECLAREPTR( ImageGadget )

} // namespace GafferUI

#endif // GAFFERUI_IMAGEGADGET_H
