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

#ifndef GAFFERUI_POINTER_H
#define GAFFERUI_POINTER_H

#include "boost/signals.hpp"

#include "IECore/ImagePrimitive.h"

namespace GafferUI
{

/// The Pointer class allows the mouse pointer to be
/// manipulated.
class Pointer
{
	
	public :
	
		/// Sets the image used to represent the mouse pointer.
		/// Passing null resets the pointer to its default state.
		static void set( IECore::ConstImagePrimitivePtr image );
		/// Returns the image used to represent the mouse pointer.
		static const IECore::ImagePrimitive *get();
		
		/// Convenience function to load an image file and call
		/// set(). Images are loaded from the paths specified by
		/// the GAFFERUI_IMAGE_PATHS environment variable. Passing
		/// "" resets the pointer to its default state.
		static void setFromFile( const std::string &name );
		
		/// A signal emitted whenever the pointer is changed.
		typedef boost::signal<void ()> ChangedSignal; 
		static ChangedSignal &changedSignal();
		
};

} // namespace GafferUI

#endif // GAFFERUI_POINTER_H
