//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, John Haddon. All rights reserved.
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

#ifndef GAFFERSCENEUI_VISUALISER_H
#define GAFFERSCENEUI_VISUALISER_H

#include "IECore/Object.h"
#include "IECoreGL/Renderable.h"

namespace GafferSceneUI
{

IE_CORE_FORWARDDECLARE( Visualiser )

/// Base class for providing OpenGL visualisations of otherwise
/// non-renderable objects. For geometric objects such as meshes,
/// the IECoreGL::ToGLConverter is sufficient for providing
/// OpenGL rendering, but for non-geometric types such as cameras
/// and lights, IECoreGL provides no visualisation capabilities.
/// This class allows custom visualisers to be registered to
/// perform an appropriate visualisation for any such type.
class Visualiser : public IECore::RefCounted
{

	public :

		IE_CORE_DECLAREMEMBERPTR( Visualiser )

		virtual ~Visualiser();

		/// Must be implemented by derived classes to return a suitable
		/// visualisation of the object.
		virtual IECoreGL::ConstRenderablePtr visualise( const IECore::Object *object ) const = 0;

		/// @name Factory
		///////////////////////////////////////////////////////////////////
		//@{
		/// Acquires a visualiser for the specified Object type.
		static const Visualiser *acquire( IECore::TypeId objectType );
		/// Registers a visualiser to use for the specified object type.
		static void registerVisualiser( IECore::TypeId objectType, ConstVisualiserPtr visualiser );
		//@}

	protected :

		Visualiser();

		template<typename VisualiserType>
		struct VisualiserDescription
		{

			VisualiserDescription()
			{
				registerVisualiser( VisualiserType::ObjectType::staticTypeId(), new VisualiserType );
			}

		};

};

} // namespace GafferSceneUI

#endif // GAFFERSCENEUI_VISUALISER_H
