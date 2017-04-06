//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "boost/python.hpp"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/PlugBinding.h"

#include "GafferImage/Catalogue.h"
#include "GafferImageBindings/CatalogueBinding.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferImage;

namespace
{

std::string repr( const Catalogue::Image *image )
{
	return "GafferImage.Catalogue.Image( \"" + image->getName().string() + "\" )";
}

class ImageSerialiser : public PlugSerialiser
{

	virtual std::string constructor( const Gaffer::GraphComponent *graphComponent, const Serialisation &serialisation ) const
	{
		return repr( static_cast<const Catalogue::Image *>( graphComponent ) );
	}

};

void save( Catalogue::Image &image, const std::string &fileName )
{
	IECorePython::ScopedGILRelease gilRelease;
	image.save( fileName );
}

} // namespace

namespace GafferImageBindings
{

void bindCatalogue()
{

	scope s = GafferBindings::DependencyNodeClass<Catalogue>();

	GafferBindings::PlugClass<Catalogue::Image>()
		.def(
			init<const std::string &>(
				(
					boost::python::arg_( "name" ) = GraphComponent::defaultName<Catalogue::Image>()
				)
			)
		)
		.def( "__repr__", repr )
		.def( "load", Catalogue::Image::load )
		.def( "save", &save )
		.staticmethod( "load" )
	;

	Serialisation::registerSerialiser( Catalogue::Image::staticTypeId(), new ImageSerialiser );

}

} // namespace GafferImageBindings
