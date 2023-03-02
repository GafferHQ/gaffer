//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "GafferCortex/Export.h"

#include "Gaffer/Plug.h"

#include "IECore/Parameter.h"

#include <functional>

namespace GafferCortex
{

IE_CORE_FORWARDDECLARE( ParameterHandler );

/// ParameterHandlers manage a mapping between IECore::Parameter objects
/// and Plugs on a Node.
class GAFFERCORTEX_API ParameterHandler : public IECore::RefCounted
{

	public :

		IE_CORE_DECLAREMEMBERPTR( ParameterHandler );

		~ParameterHandler() override;

		virtual IECore::Parameter *parameter() = 0;
		virtual const IECore::Parameter *parameter() const = 0;

		virtual void restore( Gaffer::GraphComponent *plugParent ) = 0;
		/// Setup a plug to match the parameter. Derived classes may choose to reuse existing plugs where possible.
		/// The flags argument provides the base set of flags for the plug, before parameter user data applies overrides.
		virtual Gaffer::Plug *setupPlug( Gaffer::GraphComponent *plugParent, Gaffer::Plug::Direction direction=Gaffer::Plug::In, unsigned flags = Gaffer::Plug::Default | Gaffer::Plug::Dynamic ) = 0;

		virtual Gaffer::Plug *plug() = 0;
		virtual const Gaffer::Plug *plug() const = 0;

		virtual void setParameterValue() = 0;
		virtual void setPlugValue() = 0;

		/// Returns a hash representing the current state
		/// of the parameter. This is achieved by hashing
		/// all ValuePlug descendants of `plug()` (and the
		/// plug itself if is is a ValuePlug too).
		IECore::MurmurHash hash() const;

		/// Returns a handler for the specified parameter.
		static ParameterHandlerPtr create( IECore::ParameterPtr parameter );
		/// A function for creating ParameterHandlers which will represent a Parameter with a plug on a given
		/// parent.
		using Creator = std::function<ParameterHandlerPtr ( IECore::ParameterPtr )>;
		/// Registers a function which can return a ParameterHandler for a given Parameter type.
		static void registerParameterHandler( IECore::TypeId parameterType, Creator creator );

	protected :

		ParameterHandler();

		/// Should be called by derived classes in setupPlug().
		void setupPlugFlags( Gaffer::Plug *plug, unsigned flags );

		/// Create a static instance of this to automatically register a derived class
		/// with the factory mechanism. Derived class must have a constructor of the form
		/// Derived( ParameterType::Ptr parameter, GraphComponentPtr plugParent ).
		template<typename HandlerType, typename ParameterType>
		struct ParameterHandlerDescription
		{
				ParameterHandlerDescription() { ParameterHandler::registerParameterHandler( ParameterType::staticTypeId(), &creator ); };
			private :
				static ParameterHandlerPtr creator( IECore::ParameterPtr parameter ) { return new HandlerType( boost::static_pointer_cast<ParameterType>( parameter ) ); };
		};

	private :

		using CreatorMap = std::map<IECore::TypeId, Creator>;
		static CreatorMap &creators();

};

} // namespace GafferCortex
