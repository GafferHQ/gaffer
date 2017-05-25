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

std::string maskedRepr( const Catalogue::Image *plug, unsigned flagsMask )
{
	/// \todo We only really need this function because the standard plug serialiser
	/// can't extract the nested class name. We have this problem in a few places now,
	/// so maybe we should have a simple mechanism for providing the name, or we should
	/// use `RunTimeTyped::typeName()` instead.
	std::string result = "GafferImage.Catalogue.Image( \"" + plug->getName().string() + "\", ";

	if( plug->direction()!=Plug::In )
	{
		result += "direction = " + PlugSerialiser::directionRepr( plug->direction() ) + ", ";
	}

	const unsigned flags = plug->getFlags() & flagsMask;
	if( flags != Plug::Default )
	{
		result += "flags = " + PlugSerialiser::flagsRepr( flags ) + ", ";
	}

	result += ")";

	return result;
}

std::string repr( const Catalogue::Image *plug )
{
	return maskedRepr( plug, Plug::All );
}

class ImageSerialiser : public PlugSerialiser
{

	virtual std::string constructor( const Gaffer::GraphComponent *graphComponent, const Serialisation &serialisation ) const
	{
		return maskedRepr( static_cast<const Catalogue::Image *>( graphComponent ), Plug::All & ~Plug::ReadOnly );
	}

};

class CatalogueSerialiser : public NodeSerialiser
{

	virtual bool childNeedsSerialisation( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const
	{
		if( child == child->parent<Catalogue>()->outPlug() )
		{
			/// \todo We don't want to serialise the output plug
			/// because that means an unnecessary `setInput()`
			/// call is emitted, revealing some of our internal
			/// implementation. It feels like we should be able to get this
			/// right by default on the NodeSerialiser, but this might
			/// have a few knock on effects that would require a major
			/// version. Note that we can't do the simple thing and turn off
			/// the Plug::Serialisable flag in the Catalogue constructor
			/// because that means that a promoted plug won't be serialised
			/// either.
			return false;
		}
		return NodeSerialiser::childNeedsSerialisation( child, serialisation );
	}

};

void save( Catalogue::Image &image, const std::string &fileName )
{
	IECorePython::ScopedGILRelease gilRelease;
	image.save( fileName );
}

std::string generateFileName1( Catalogue &catalogue, const Catalogue::Image *image )
{
	IECorePython::ScopedGILRelease gilRelease;
	return catalogue.generateFileName( image );
}

std::string generateFileName2( Catalogue &catalogue, const ImagePlug *image )
{
	IECorePython::ScopedGILRelease gilRelease;
	return catalogue.generateFileName( image );
}

} // namespace

namespace GafferImageBindings
{

void bindCatalogue()
{

	scope s = GafferBindings::DependencyNodeClass<Catalogue>()
		.def( "generateFileName", &generateFileName1 )
		.def( "generateFileName", &generateFileName2 )
		.def( "displayDriverServer", &Catalogue::displayDriverServer, return_value_policy<IECorePython::CastToIntrusivePtr>() )
		.staticmethod( "displayDriverServer" )
	;

	GafferBindings::PlugClass<Catalogue::Image>()
		.def(
			init<const std::string &, Plug::Direction, unsigned>(
				(
					boost::python::arg_( "name" ) = GraphComponent::defaultName<Catalogue::Image>(),
					boost::python::arg_( "direction" ) = Plug::In,
					boost::python::arg_( "flags" ) = Plug::Default
				)
			)
		)
		.def( "__repr__", repr )
		.def( "load", Catalogue::Image::load )
		.def( "save", &save )
		.staticmethod( "load" )
	;

	Serialisation::registerSerialiser( Catalogue::Image::staticTypeId(), new ImageSerialiser );
	Serialisation::registerSerialiser( Catalogue::staticTypeId(), new CatalogueSerialiser );

}

} // namespace GafferImageBindings
