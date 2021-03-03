//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERBINDINGS_SERIALISATION_H
#define GAFFERBINDINGS_SERIALISATION_H

#include "GafferBindings/Export.h"

#include "Gaffer/GraphComponent.h"
#include "Gaffer/Set.h"

#include "IECore/Canceller.h"
#include "IECore/Object.h"

namespace GafferBindings
{

class GAFFERBINDINGS_API Serialisation : boost::noncopyable
{

	public :

		/// Supports cancellation via the usual mechanism of scoping a Context
		/// containing an `IECore::Canceller`.
		Serialisation( const Gaffer::GraphComponent *parent, const std::string &parentName = "parent", const Gaffer::Set *filter = nullptr );

		/// Returns the parent passed to the constructor.
		const Gaffer::GraphComponent *parent() const;

		/// Returns the name of a variable used to reference the specified object
		/// within the serialisation. Returns the empty string if the object is not
		/// to be included in the serialisation.
		std::string identifier( const Gaffer::GraphComponent *graphComponent ) const;
		/// Returns an identifier for a child relative to its parent identifier. This
		/// is quicker than calling `identifier( child )` if you already have the
		/// parent identifier to hand.
		std::string childIdentifier( const std::string &parentIdentifier, const Gaffer::GraphComponent *child ) const;
		/// \todo This overload provides improved performance in some situations,
		/// but we should instead optimise GraphComponent storage so that it is not
		/// necessary.
		std::string childIdentifier( const std::string &parentIdentifier, Gaffer::GraphComponent::ChildIterator child ) const;

		/// Ensures that `import moduleName` is included in the result.
		void addModule( const std::string &moduleName );

		/// Returns the result of the serialisation.
		std::string result() const;

		/// Convenience function to return the name of the module where object is defined.
		static std::string modulePath( const IECore::RefCounted *object );
		/// As above, but returns the empty string for built in python types.
		static std::string modulePath( const boost::python::object &object );
		/// Convenience function to return the name of the class which object is an instance of.
		/// \note Prior to Python 3.3 there is no way to automatically obtain a qualified name for
		/// a nested class (see http://www.python.org/dev/peps/pep-3155). In the meantime,
		/// you may manually add your own __qualname__ attribute, and it will be used by this
		/// function.
		static std::string classPath( const IECore::RefCounted *object );
		/// Convenience function to return the name of the class which object is an instance of.
		/// If object is a type object rather than an instance, then the path for the type
		/// object itself is returned.
		static std::string classPath( const boost::python::object &object );

		/// Encodes any IECore::Object into a base64 encoded string.
		/// \todo Perhaps these would be useful as `IECore::ObjectAlgo`?
		static std::string objectToBase64( const IECore::Object *object );
		/// Creates an object from a string previously encoded with `objectToBase64()`.
		static IECore::ObjectPtr objectFromBase64( const std::string &base64 );

		/// The Serialiser class may be implemented differently for specific types to customise
		/// their serialisation.
		///
		/// \todo This was initially conceived as a read-only API, where Serialisation
		/// made requests of Serialiser and used the results. That has proved to be a bit
		/// awkward and slow as each of the virtual methods often do duplicate work such as
		/// converting `graphComponent` to Python. The addition of `Serialisation::addModule()`
		/// marked a departure from this design, allowing Serialisers to modify the serialisation
		/// directly. It may make sense to continue in this direction by reducing the methods
		/// on Serialiser and adding to the methods on Serialisation. The logical conclusion
		/// may be a single `Serialiser::serialise()` method and various `Serialisation::add*()`
		/// methods.
		class Serialiser : public IECore::RefCounted
		{

			public :

				IE_CORE_DECLAREMEMBERPTR( Serialiser );

				/// May be implemented to insert the names of any modules the serialiser will need
				/// into the modules set. The default implementation returns modulePath( graphComponent ).
				/// > Note : It is often more convenient to call `serialisation.addModule()` from one of
				/// > the other virtual methods.
				virtual void moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const;
				/// Should be implemented to return a string which when executed will reconstruct the specified object.
				/// The default implementation uses repr().
				virtual std::string constructor( const Gaffer::GraphComponent *graphComponent, Serialisation &serialisation ) const;
				/// May be implemented to return a string which will be executed immediately after the object has been constructed and
				/// parented. identifier is the name of a variable which refers to the object. The Serialisation may be used to query
				/// the identifiers for other objects, but note that at this stage those objects may not have been constructed so it
				/// is not safe to use them directly. Default implementation returns the empty string.
				virtual std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const;
				/// May be implemented to return a string which will be executed once all objects have been constructed and parented.
				/// At this point it is possible to request the identifiers of other objects via the Serialisation and refer to them in the result.
				/// Typically this would be used for forming connections between plugs. The default implementation returns the empty string.
				virtual std::string postHierarchy( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const;
				/// May be implemented to return a string to be executed after all the postHierarchy strings. This
				/// can be used to perform a final setup step. The default implementation returns an empty string.
				virtual std::string postScript( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const;
				/// May be implemented to say whether or not the child needs to be serialised. The default
				/// implementation returns true.
				virtual bool childNeedsSerialisation( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const;
				/// May be implemented to say whether or not the child needs to be constructed explicitly by the serialisation,
				/// or it will be created by the parent automatically on construction of the parent. Default
				/// implementation returns false.
				virtual bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const;

		};

		IE_CORE_DECLAREPTR( Serialiser );

		static void registerSerialiser( IECore::TypeId targetType, SerialiserPtr serialiser );
		/// Returns a Serialiser suitable for serialisation of the specified object. Note that
		/// Serialisers do not have state, so this method may return the same Serialiser from
		/// different calls even when the objects are different.
		static const Serialiser *acquireSerialiser( const Gaffer::GraphComponent *graphComponent );

	private :

		const Gaffer::GraphComponent *m_parent;
		const std::string m_parentName;
		const Gaffer::Set *m_filter;
		const bool m_protectParentNamespace;

		std::string m_hierarchyScript;
		std::string m_connectionScript;
		std::string m_postScript;

		std::set<std::string> m_modules;

		void walk( const Gaffer::GraphComponent *parent, const std::string &parentIdentifier, const Serialiser *parentSerialiser, const IECore::Canceller *canceller );

		using SerialiserMap = std::map<IECore::TypeId, SerialiserPtr>;
		static SerialiserMap &serialiserMap();

};

} // namespace GafferBindings

#endif // GAFFERBINDINGS_SERIALISATION_H
