//////////////////////////////////////////////////////////////////////////
//
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

#include "Gaffer/Signals.h"

#include "GafferUI/Export.h"

#include "IECoreImage/ImagePrimitive.h"

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( Pointer )

/// The Pointer class allows the mouse pointer to be
/// manipulated.
class GAFFERUI_API Pointer : public IECore::RefCounted
{

	public :

		IE_CORE_DECLAREMEMBERPTR( Pointer )

		/// A copy of the image is taken.
		explicit Pointer( const IECoreImage::ImagePrimitive *image, const Imath::V2i &hotspot = Imath::V2i( -1 ) );
		/// Images are loaded from the paths specified by the
		/// GAFFERUI_IMAGE_PATHS environment variable.
		Pointer( const std::string &fileName, const Imath::V2i &hotspot = Imath::V2i( -1 ) );

		const IECoreImage::ImagePrimitive *image() const;
		const Imath::V2i &hotspot() const;

		/// Sets the current pointer. Passing null resets the
		/// pointer to its default state.
		static void setCurrent( ConstPointerPtr pointer );
		/// Sets the current pointer to one registered using
		/// registerPointer(). Passing the empty string resets
		/// the pointer to its default state.
		static void setCurrent( const std::string &name );
		static const Pointer *getCurrent();

		/// Registers a named pointer for use in setCurrent().
		static void registerPointer( const std::string &name, ConstPointerPtr pointer );

		/// A signal emitted whenever the pointer is changed.
		using ChangedSignal = Gaffer::Signals::Signal<void ()>;
		static ChangedSignal &changedSignal();

	private :

		IECoreImage::ConstImagePrimitivePtr m_image;
		Imath::V2i m_hotspot;

};

} // namespace GafferUI
