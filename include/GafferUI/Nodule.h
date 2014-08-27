//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_NODULE_H
#define GAFFERUI_NODULE_H

#include "boost/regex.hpp"

#include "Gaffer/FilteredRecursiveChildIterator.h"

#include "GafferUI/Gadget.h"

namespace Gaffer
{
	IE_CORE_FORWARDDECLARE( Plug )
}

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( Nodule )

class Nodule : public Gadget
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::Nodule, NoduleTypeId, Gadget );
		virtual ~Nodule();

		Gaffer::Plug *plug();
		const Gaffer::Plug *plug() const;

		/// Creates a Nodule for the specified plug.
		static NodulePtr create( Gaffer::PlugPtr plug );

		typedef boost::function<NodulePtr ( Gaffer::PlugPtr )> NoduleCreator;
		/// Registers a function which will return a Nodule instance for a plug of a specific
		/// type.
		static void registerNodule( IECore::TypeId plugType, NoduleCreator creator );
		/// Registers a function which will return a Nodule instance for plugs with specific names on
		/// a specific type of node. Nodules registered in this way will take precedence over those registered above.
		/// Note that a creator may return 0 to suppress the creation of a Nodule.
		static void registerNodule( const IECore::TypeId nodeType, const std::string &plugPathRegex, NoduleCreator creator );

		virtual std::string getToolTip( const IECore::LineSegment3f &line ) const;

	protected :

		Nodule( Gaffer::PlugPtr plug );

		/// Creating a static one of these is a convenient way of registering a Nodule type.
		template<class T>
		struct NoduleTypeDescription
		{
			NoduleTypeDescription( IECore::TypeId plugType ) { Nodule::registerNodule( plugType, &creator ); };
			static NodulePtr creator( Gaffer::PlugPtr plug ) { return new T( plug ); };
		};

	private :

		Gaffer::PlugPtr m_plug;

		typedef std::map<IECore::TypeId, NoduleCreator> CreatorMap;
		static CreatorMap &creators();

		typedef std::pair<boost::regex, NoduleCreator> RegexAndCreator;
		typedef std::vector<RegexAndCreator> RegexAndCreatorVector;
		typedef std::map<IECore::TypeId, RegexAndCreatorVector> NamedCreatorMap;
		static NamedCreatorMap &namedCreators();


};

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<Nodule> > NoduleIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<Nodule> > RecursiveNoduleIterator;

IE_CORE_DECLAREPTR( Nodule );

} // namespace GafferUI

#endif // GAFFERUI_NODULE_H
