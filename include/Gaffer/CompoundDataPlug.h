//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFER_COMPOUNDDATAPLUG_H
#define GAFFER_COMPOUNDDATAPLUG_H

#include "IECore/CompoundData.h"
#include "IECore/CompoundObject.h"

#include "Gaffer/CompoundPlug.h"

namespace Gaffer
{

/// This plug provides an easy means of building CompoundData containing
/// arbitrary keys and values, where each key and value is represented
/// by an individual child plug.
class CompoundDataPlug : public Gaffer::CompoundPlug
{

	public :

		CompoundDataPlug(
			const std::string &name = defaultName<CompoundDataPlug>(),
			Direction direction=In,
			unsigned flags = Default
		);
		virtual ~CompoundDataPlug();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::CompoundDataPlug, CompoundDataPlugTypeId, Gaffer::CompoundPlug );

		/// Accepts only children that can generate values for the CompoundData.
		virtual bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const;
		virtual PlugPtr createCounterpart( const std::string &name, Direction direction ) const;

		/// The plug type used to represent the data members.
		class MemberPlug : public CompoundPlug
		{

			public :

				IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::CompoundDataPlug::MemberPlug, CompoundDataMemberPlugTypeId, Gaffer::CompoundPlug );

				MemberPlug( const std::string &name=defaultName<MemberPlug>(), Direction direction=In, unsigned flags=Default );

				virtual bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const;
				virtual PlugPtr createCounterpart( const std::string &name, Direction direction ) const;

		};

		typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, MemberPlug> > MemberPlugIterator;
		IE_CORE_DECLAREPTR( MemberPlug )

		/// Adds a CompoundPlug to represent a CompoundData member with the specified name and default value.
		/// \todo Consider replacing all these add*Member() methods with convenience constructors on MemberPlug,
		/// and a simple addChild( new MemberPlug( ... ) ).
		MemberPlug *addMember( const std::string &name, const IECore::Data *defaultValue, const std::string &plugName = "member1", unsigned plugFlags = Plug::Default | Plug::Dynamic );
		MemberPlug *addMember( const std::string &name, ValuePlug *valuePlug, const std::string &plugName = "member1" );
		/// As above, but adds an additional BoolPlug to allow the user to control whether or not
		/// this particular member is enabled.
		MemberPlug *addOptionalMember( const std::string &name, const IECore::Data *defaultValue, const std::string &plugName = "member1", unsigned plugFlags = Plug::Default | Plug::Dynamic, bool enabled = false );
		MemberPlug *addOptionalMember( const std::string &name, ValuePlug *valuePlug, const std::string &plugName = "member1", bool enabled = false );
		/// Adds each member from the specified CompoundData.
		void addMembers( const IECore::CompoundData *members, bool useNameAsPlugName = false );

		/// Returns the value for the member specified by the child parameterPlug, and fills name with the
		/// name for the member. If the user has disabled the member or the name is the empty string, then
		/// 0 is returned.
		IECore::DataPtr memberDataAndName( const MemberPlug *parameterPlug, std::string &name ) const;

		/// Fills the CompoundDataMap with values based on the child plugs of this node.
		void fillCompoundData( IECore::CompoundDataMap &compoundDataMap ) const;
		/// As above but fills a CompoundObjectMap instead.
		void fillCompoundObject( IECore::CompoundObject::ObjectMap &compoundObjectMap ) const;

		/// Creates an appropriate plug to hold the specified data.
		/// \todo This is exposed so it may be reused elsewhere, but is there a better place for it? What about PlugType.h?
		static ValuePlugPtr createPlugFromData( const std::string &name, Plug::Direction direction, unsigned flags, const IECore::Data *value );
		/// Extracts a Data value from a plug previously created with createPlugFromData().
		static IECore::DataPtr extractDataFromPlug( const ValuePlug *plug );

	private :

		template<typename T>
		static ValuePlugPtr boxValuePlug( const std::string &name, Plug::Direction direction, unsigned flags, const T *value );

		template<typename T>
		static ValuePlugPtr compoundNumericValuePlug( const std::string &name, Plug::Direction direction, unsigned flags, const T *value );

		template<typename T>
		static ValuePlugPtr typedObjectValuePlug( const std::string &name, Plug::Direction direction, unsigned flags, const T *value );

};

IE_CORE_DECLAREPTR( CompoundDataPlug );

typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, CompoundDataPlug> > CompoundDataPlugIterator;
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::In, CompoundDataPlug> > InputCompoundDataPlugIterator;
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Out, CompoundDataPlug> > OutputCompoundDataPlugIterator;

typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, CompoundDataPlug>, PlugPredicate<> > RecursiveCompoundDataPlugIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::In, CompoundDataPlug>, PlugPredicate<> > RecursiveInputCompoundDataPlugIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Out, CompoundDataPlug>, PlugPredicate<> > RecursiveOutputCompoundDataPlugIterator;

} // namespace Gaffer

#endif // GAFFER_COMPOUNDDATAPLUG_H
