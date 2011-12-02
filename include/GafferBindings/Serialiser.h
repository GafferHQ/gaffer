//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#ifndef GAFFERBINDINGS_SERIALISER_H
#define GAFFERBINDINGS_SERIALISER_H

#include "Gaffer/Node.h"
#include "Gaffer/Set.h"

#include "boost/function.hpp"

namespace GafferBindings
{

/// \todo Need to be able to serialise nodes within nodes
class Serialiser
{

	public :
	
		Serialiser( Gaffer::ConstNodePtr context, Gaffer::ConstSetPtr filter=0 );

		//! @name Serialisation methods
		/// These add objects to the serialisation.
		/// \todo merge add and serialiseC together? or rename them nicely? make serialiseC
		/// specific to plugs only?
		/////////////////////////////////////////////////////////////////////////////////
		//@{
		/// Makes sure the module needed for object o is imported, and returns a string
		/// which can be used to refer to it.
		std::string modulePath( Gaffer::ConstGraphComponentPtr o );
		/// As above but returns the empty string if the object has no module (is a built in type).
		std::string modulePath( boost::python::object &o );
		/// Adds the specified object to the serialisation and returns the name of
		/// a local variable which can be used to reference it in subsequent parts of the
		/// serialisation. If component is not in filter then nothing is done and the empty
		/// string is returned.
		std::string add( Gaffer::ConstNodePtr o );
		/// Returns a serialisation for component - this will not yet have been added
		/// to the result.
		std::string serialiseC( Gaffer::ConstGraphComponentPtr o );
		/// Adds a string to the result. This can be used for adding comments or custom
		/// serialisations.
		void add( const std::string &s );
		//@}

		/// Returns the complete result of the serialisation.
		std::string result() const;

		/// Convenience function to serialise all the children of context, yielding a string
		/// which should be executed in an equivalent context to reconstruct it. The filter can be
		/// used to restrict the set of children which are serialised.
		static std::string serialise( Gaffer::ConstNodePtr context, Gaffer::ConstSetPtr filter=0 );
		
		typedef boost::function<std::string ( Serialiser &s, Gaffer::ConstGraphComponentPtr g )> SerialisationFunction;
		static void registerSerialiser( IECore::TypeId type, SerialisationFunction serialiser );
		
	private :
		
		std::string m_result;
		
		Gaffer::ConstSetPtr m_filter;
		
		std::set<std::string> m_modules;
		
		typedef std::set<Gaffer::ConstNodePtr> VisitedSet;
		VisitedSet m_visited;		
		
		typedef std::map<IECore::TypeId, SerialisationFunction> FunctionMap;
		static FunctionMap g_serialisers;

};

} // namespace GafferBindings

#endif // GAFFERBINDINGS_SERIALISER_H
