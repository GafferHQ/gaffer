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

#ifndef GAFFERIMAGE_GRADE_H
#define GAFFERIMAGE_GRADE_H

#include "GafferImage/ChannelDataProcessor.h"
#include "GafferImage/ImagePlug.h"
#include "Gaffer/PlugType.h"

namespace GafferImage
{

/// The grade node implements the common grade operation to the RGB channels of the input.
/// The computation performed is:
/// A = multiply * (gain - lift) / (whitePoint - blackPoint)
/// B = offset + lift - A * blackPoint
/// output = pow( A * input + B, 1/gamma )
//
class Grade : public ChannelDataProcessor
{

	public :
		
		Grade( const std::string &name=defaultName<Grade>() );
		virtual ~Grade();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::Grade, GradeTypeId, ChannelDataProcessor );
		
        //! @name Plug Accessors
        /// Returns a pointer to the node's plugs.
        //////////////////////////////////////////////////////////////
        //@{	
		Gaffer::Color3fPlug *blackPointPlug();
		const Gaffer::Color3fPlug *blackPointPlug() const;
		Gaffer::Color3fPlug *whitePointPlug();
		const Gaffer::Color3fPlug *whitePointPlug() const;
		Gaffer::Color3fPlug *liftPlug();
		const Gaffer::Color3fPlug *liftPlug() const;
		Gaffer::Color3fPlug *gainPlug();
		const Gaffer::Color3fPlug *gainPlug() const;
		Gaffer::Color3fPlug *multiplyPlug();
		const Gaffer::Color3fPlug *multiplyPlug() const;
		Gaffer::Color3fPlug *offsetPlug();
		const Gaffer::Color3fPlug *offsetPlug() const;
		Gaffer::Color3fPlug *gammaPlug();
		const Gaffer::Color3fPlug *gammaPlug() const;
		Gaffer::BoolPlug *blackClampPlug();
		const Gaffer::BoolPlug *blackClampPlug() const;
		Gaffer::BoolPlug *whiteClampPlug();
		const Gaffer::BoolPlug *whiteClampPlug() const;
        //@}
		
		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;
	
	protected :

		/// Disables the output of any channel that has a gamma value of 0.	
		virtual bool channelEnabled( const std::string &channel ) const;
		
		virtual void hashChannelDataPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		void processChannelData( const Gaffer::Context *context, const ImagePlug *parent, const std::string &channelIndex, IECore::FloatVectorDataPtr outData ) const;

	private :
		
		static size_t g_firstPlugIndex;
		
};

} // namespace GafferImage

#endif // GAFFERIMAGE_GRADE_H
