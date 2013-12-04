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

#ifndef GAFFERIMAGE_MERGE_H
#define GAFFERIMAGE_MERGE_H

#include "GafferImage/FilterProcessor.h"

namespace GafferImage
{

class Merge : public FilterProcessor
{

	public :
		
		Merge( const std::string &name=defaultName<Merge>() );
		virtual ~Merge();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::Merge, MergeTypeId, FilterProcessor );
		
        //! @name Plug Accessors
        /// Returns a pointer to the node's plugs.
        //////////////////////////////////////////////////////////////
        //@{	
		/// Returns a pointer to the int plug which dictates the operation to perform.
		/// The available operations are:
		///
		/// Add: A + B
		/// Atop: Ab + B(1-a) 
		/// Divide: A / B
		/// In: Ab
		/// Out: A(1-b)
		/// Mask: Ba
		/// Matte: Aa + B(1.-a)
		/// Multiply: AB
		/// Over: A + B(1-a)
		/// Subtract: A - B
		/// Under: A(1-b) + B
		Gaffer::IntPlug *operationPlug();
		const Gaffer::IntPlug *operationPlug() const;
        //@}
		
		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;
		
	protected :

		/// The different types of operation that are available.		
		enum
		{
			kAdd = 0,
			kAtop = 1,
			kDivide = 2,
			kIn = 3,
			kOut = 4,
			kMask = 5,
			kMatte = 6,
			kMultiply = 7,
			kOver = 8,
			kSubtract = 9,
			kUnder = 10
		};

		virtual void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;
	
	protected:	
	
		/// This implementation checks that each of the inputs is connected and if not, returns false.
		virtual bool enabled() const;
	
	private :
		
		/// Performs the merge operation using the functor 'F'.
		template< typename F >
		IECore::ConstFloatVectorDataPtr doMergeOperation( F f, std::vector< IECore::ConstFloatVectorDataPtr > &inData, std::vector< IECore::ConstFloatVectorDataPtr > &inAlpha, const Imath::V2i &tileOrigin ) const;

		/// A useful method which returns true if the StringVector contains the channel "A".
		inline bool hasAlpha( IECore::ConstStringVectorDataPtr channelNamesData ) const;
		
		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Merge )

#include "Merge.inl"

} // namespace GafferImage

#endif // GAFFERIMAGE_MERGE_H
