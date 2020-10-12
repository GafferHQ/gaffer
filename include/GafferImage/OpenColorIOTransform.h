//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERIMAGE_OPENCOLORIOTRANSFORM_H
#define GAFFERIMAGE_OPENCOLORIOTRANSFORM_H

#include "GafferImage/ColorProcessor.h"

#include "Gaffer/CompoundDataPlug.h"

#include "OpenColorIO/OpenColorIO.h"

namespace GafferImage
{

/// Abstract base class for nodes which apply an OpenColorIO Transform
class GAFFERIMAGE_API OpenColorIOTransform : public ColorProcessor
{

	public :

		~OpenColorIOTransform() override;

		/// Fills the vector will the available color spaces,
		/// as defined by the current OpenColorIO config.
		static void availableColorSpaces( std::vector<std::string> &colorSpaces );
		/// Fills the vector will the available roles,
		/// as defined by the current OpenColorIO config.
		static void availableRoles( std::vector<std::string> &Roles );

		/// May return null if the derived class does not
		/// request OCIO context variable support.
		Gaffer::CompoundDataPlug *contextPlug();
		const Gaffer::CompoundDataPlug *contextPlug() const;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferImage::OpenColorIOTransform, OpenColorIOTransformTypeId, ColorProcessor );

		/// Returns the OCIO processor for this node, taking into account
		/// the current Gaffer context and the OCIO context specified by
		/// `contextPlug()`. Returns nullptr if this node is a no-op.
		OpenColorIO::ConstProcessorRcPtr processor() const;
		/// Returns a hash that uniquely represents the result of calling
		/// `processor()` in the current context.
		IECore::MurmurHash processorHash() const;

	protected :

		OpenColorIOTransform( const std::string &name=defaultName<OpenColorIOTransform>(), bool withContextPlug=false );
		/// Implemented to return true if hashTransform() has
		/// an affect. Derived classed should implement
		/// hashTransform() to return a default hash if the
		/// node should be in a disabled state.
		/// \todo: rework ColorProcessor so we can remove this.
		bool enabled() const override;

		/// Implemented to call affectsTransform() if the base class
		/// does not affect the color data for this input. Derived
		/// classes should implement affectsTransform() instead.
		bool affectsColorData( const Gaffer::Plug *input ) const override;
		/// Implemented to call hashTransform() after hashing the
		/// affect of the base class. Derived classes should
		/// implement hashTransform() instead.
		void hashColorData( const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		/// Implemented to fetch an OpenColorIO Processor from the
		/// OpenColorIO Config and apply it to the output channels.
		/// Derived classes should implement transform() instead.
		void processColorData( const Gaffer::Context *context, IECore::FloatVectorData *r, IECore::FloatVectorData *g, IECore::FloatVectorData *b ) const override;

		/// Derived classes must implement this to return true if the specified input
		/// is used in transform().
		virtual bool affectsTransform( const Gaffer::Plug *input ) const = 0;
		/// Derived classes must implement this to compute the hash for the transform.
		virtual void hashTransform( const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		/// Derived classes must implement this to return a valid OpenColorIO
		/// Transform which can be used by an OpenColorIO Processor or a null
		/// pointer if no processing should take place.
		virtual OpenColorIO::ConstTransformRcPtr transform() const = 0;

	private :

		OpenColorIO::ConstContextRcPtr ocioContext( OpenColorIO::ConstConfigRcPtr config ) const;

		static size_t g_firstPlugIndex;
		bool m_hasContextPlug;

};

IE_CORE_DECLAREPTR( OpenColorIOTransform )

} // namespace GafferImage

#endif // GAFFERIMAGE_OPENCOLORIOTRANSFORM_H
