//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferSceneUI/Export.h"
#include "GafferSceneUI/TypeIds.h"

#include "GafferScene/SceneAlgo.h"
#include "GafferScene/ScenePlug.h"

#include "Gaffer/EditScope.h"
#include "Gaffer/Path.h"

#include "IECore/RunTimeTyped.h"

#include "boost/multi_index/hashed_index.hpp"
#include "boost/multi_index/member.hpp"
#include "boost/multi_index/random_access_index.hpp"
#include "boost/multi_index_container.hpp"

#include <unordered_set>
#include <unordered_map>
#include <variant>

namespace GafferSceneUIModule
{

// Forward declaration for friendship declared below.
// We don't include InspectorBinding.h because we don't want
// python involved in any way when building the pure C++
// modules.
void bindInspector();

} // namespace GafferSceneUIModule

namespace GafferSceneUI
{

namespace Private
{

IE_CORE_FORWARDDECLARE( Inspector );

/// Inspectors provide an abstraction for querying properties of a scene, and
/// optionally making node graph edits to change those properties. They allow a
/// small set of UI components to expose editable properties without needing to
/// know their underlying details.
///
/// Inspectors are responsible for _what_ is inspected, but the UI components
/// are responsible for the Context in which inspection happens. For example, a
/// ParameterInspector knows which parameter to inspect, but the UI provides the
/// location to inspect via the current context.
///
/// Inspectors are "EditScope aware", allowing the user to create new edits using
/// a target EditScope. One of the main contributions of the Inspector base class
/// is to encode the rules for interaction with EditScopes.
///
/// Notes for future work :
///
/// - This is temporarily in a Private namespace so that we can iterate on it
///   without concerns about ABI breakage. Intended to be public eventually.
/// - We want to generalise Inspectors so they can be used with images as well
///   as scenes. Beware any scene-centric design decisions.
/// - We want to use a TransformInspector to replace much of TransformTool::Selection.
///   This has additional requirements such as knowing the `transformSpace` that a node
///   works in. We think this information can be stored in a dedicated TransformHistory
///   class provided by SceneAlgo, avoiding any need to specialise Inspector::Result.
class GAFFERSCENEUI_API Inspector : public IECore::RunTimeTyped, public Gaffer::Signals::Trackable
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferSceneUI::Private::Inspector, InspectorTypeId, IECore::RunTimeTyped );
		IE_CORE_FORWARDDECLARE( Result );

		/// The type of property being inspected (for instance "attribute" or "parameter").
		const std::string &type() const;

		/// The name of the property being inspected, as it is referred to in
		/// the API. It is the UI's responsibility to format this appropriately
		/// (for example, by converting from "camelCase" or "snake_case").
		const std::string &name() const;

		/// Called by the UI to inspect the property in the current context.
		ResultPtr inspect() const;

		using InspectorSignal = Gaffer::Signals::Signal<void ( Inspector * )>;
		/// Emitted when the property queried by the inspector has changed.
		/// The UI should use this to schedule a refresh.
		InspectorSignal &dirtiedSignal();

		/// Returns a `Path` representing the history for the inspected property
		/// in the current context. The path has a child for each predecessor in
		/// the history, and properties `history:value`, `history:fallbackValue`,
		/// `history:operation`, `history:source`, `history:editWarning` and `history:node`.
		///
		/// Like `inspect()`, this is a one-shot operation : if the inspector is
		/// dirtied then a new call to `historyPath()` will be required. But the
		/// path does defer inspection until its children or properties are
		/// queried, allowing it to be used with PathListingWidget to perform
		/// the queries without blocking the UI.
		Gaffer::PathPtr historyPath() const;

	protected :

		/// Protected constructor for use by derived classes. The `name` argument
		/// will be returned verbatim by the `name()` method.
		Inspector( const Gaffer::ConstPlugPtr &target, const std::string &type, const std::string &name, const Gaffer::PlugPtr &editScope );

		/// Methods to be implemented in derived classes
		/// ============================================
		///
		/// The `inspect()` method delegates to several virtual methods that
		/// should be implemented by derived classes. Inspection starts by
		/// generating a history for the computation of the property, and then
		/// traverses the history making additional queries at various points.

		/// Must be implemented to return the history for the property being
		/// inspected. Should return null if the property does not exist.
		virtual GafferScene::SceneAlgo::History::ConstPtr history() const = 0;

		/// Must be implemented to return the value of the property at this
		/// point in the history. Called with `history->context` as the current
		/// context.
		/// \todo Perhaps this should be available directly from the history
		/// base class?
		virtual IECore::ConstObjectPtr value( const GafferScene::SceneAlgo::History *history ) const = 0;

		/// Can be implemented by derived classes to provide a fallback value for the inspection,
		/// used when no value is returned from `value()`. Called with `history->context` as the current
		/// context. Optionally, `description` may be assigned a description to be shown to the user.
		/// Typically, this description would be used to disambiguate the source of the fallback value.
		virtual IECore::ConstObjectPtr fallbackValue( const GafferScene::SceneAlgo::History *history, std::string &description ) const;

		/// Should be implemented by derived classes to return the source for
		/// the value authored at this point in the history. Optionally,
		/// `editWarning` may be assigned a warning that will be shown to the
		/// user when editing this plug. Called with `history->context` as the
		/// current context. Default implementation returns null.
		/// \todo Perhaps this should also be available directly from the
		/// history class?
		virtual Gaffer::ValuePlugPtr source( const GafferScene::SceneAlgo::History *history, std::string &editWarning ) const;

		using AcquireEditFunction = std::function<Gaffer::ValuePlugPtr ( bool createIfNecessary )>;
		using AcquireEditFunctionOrFailure = std::variant<AcquireEditFunction, std::string>;
		/// Should be implemented to return a function that will acquire
		/// an edit from the EditScope at the specified point in the history.
		/// If this is not possible, should return an error explaining why
		/// (this is typically due to `readOnly` metadata). Called with `history->context`
		/// as the current context.
		///
		/// > Note : Where an EditScope already contains an edit, it is expected
		/// > that this will be dealt with in `source()`, returning a result
		/// > that edits the processor itself.
		virtual AcquireEditFunctionOrFailure acquireEditFunction( Gaffer::EditScope *editScope, const GafferScene::SceneAlgo::History *history ) const;

		using DisableEditFunction = std::function<void ()>;
		using DisableEditFunctionOrFailure = std::variant<DisableEditFunction, std::string>;
		/// Can be implemented to return a function that will disable an edit
		/// at the specified plug. If this is not possible, should return an
		/// error explaining why (this is typically due to `readOnly` metadata).
		/// Called with `history->context` as the current context.
		virtual DisableEditFunctionOrFailure disableEditFunction( Gaffer::ValuePlug *plug, const GafferScene::SceneAlgo::History *history ) const;

		using CanEditFunction = std::function<bool ( const Gaffer::ValuePlug *plug, const IECore::Object *value, std::string &failureReason )>;
		/// Can be implemented to return a function that will return whether
		/// `value` can be set on `plug`. If `value` cannot be set on `plug`,
		/// `failureReason` should provide the reason why.
		virtual CanEditFunction canEditFunction( const GafferScene::SceneAlgo::History *history ) const;

		using EditFunction = std::function<void ( Gaffer::ValuePlug *plug, const IECore::Object *value )>;
		/// Can be implemented to return a function that will directly
		/// edit `plug` to set `value`. Called with `history->context` as the
		/// current context.
		virtual EditFunction editFunction( const GafferScene::SceneAlgo::History *history ) const;

		Gaffer::EditScope *targetEditScope() const;

	private :

		void inspectHistoryWalk( const GafferScene::SceneAlgo::History *history, Result *result ) const;
		void editScopeInputChanged( const Gaffer::Plug *plug );

		/// Utility class representing the history of the property in a
		/// convenient form for use in `PathListingWidget`.
		/// The `names()` of the path are combined hashes of the plug pointer value
		/// and the context at that point in history, which are used as keys into `PlugMap`.
		class GAFFERSCENEUI_API HistoryPath : public Gaffer::Path
		{
			public :

				HistoryPath(
					const ConstInspectorPtr &inspector,
					Gaffer::ConstContextPtr context,
					const std::string &path = "/",
					Gaffer::PathFilterPtr filter = nullptr
				);

				IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Inspector::HistoryPath, HistoryPathTypeId, Path );

				~HistoryPath() override;

				void propertyNames( std::vector<IECore::InternedString> &names, const IECore::Canceller *canceller = nullptr) const override;
				IECore::ConstRunTimeTypedPtr property( const IECore::InternedString &name, const IECore::Canceller *canceller = nullptr ) const override;

				bool isValid( const IECore::Canceller *canceller = nullptr ) const override;
				bool isLeaf( const IECore::Canceller *canceller = nullptr ) const override;
				Gaffer::PathPtr copy() const override;

				const Gaffer::Plug *cancellationSubject() const override;

			protected :

				void doChildren( std::vector<Gaffer::PathPtr> &children, const IECore::Canceller *canceller = nullptr ) const override;

			private :

				struct HistoryProvider;
				using HistoryProviderPtr = std::shared_ptr<HistoryProvider>;

				// Private constructor for creating children and copies sharing
				// the same history provider.
				HistoryPath(
					const HistoryProviderPtr &historyProvider,
					const std::string &path = "/",
					Gaffer::PathFilterPtr filter = nullptr
				);

				const GafferScene::SceneAlgo::History *history( const IECore::Canceller *canceller ) const;
				HistoryProviderPtr m_historyProvider;

		};

		const Gaffer::ConstPlugPtr m_target;
		const std::string m_type;
		const std::string m_name;
		const Gaffer::PlugPtr m_editScope;
		InspectorSignal m_dirtiedSignal;

		// So we can access HistoryPath.
		friend void GafferSceneUIModule::bindInspector();

};

/// The result of a call to `Inspector::inspect()`. Contains everything
/// needed to display a property in the UI and optionally allow it to
/// be edited.
class GAFFERSCENEUI_API Inspector::Result : public IECore::RefCounted
{

	public :

		IE_CORE_DECLAREMEMBERPTR( Result );

		/// Queries
		/// =======

		/// The inspected value that should be displayed by the UI.
		const IECore::Object *value() const;
		/// The inspected value cast to its native type. If the inspected
		/// value is not of the requested type, the given default value
		/// will be returned.
		template<typename T>
		const T typedValue( const T &defaultValue ) const;

		/// The plug that was used to author the current value, or null if
		/// it cannot be determined.
		Gaffer::ValuePlug *source() const;
		/// The target EditScope.
		Gaffer::EditScope *editScope() const;

		enum class SourceType
		{
			/// The value was authored above the current EditScope.
			Upstream,
			/// The value was authored within the current EditScope.
			EditScope,
			/// The value was authored downstream of the current EditScope, and
			/// will override any edits made in it. This includes the case where
			/// the value is authored within a nested EditScope.
			Downstream,
			/// No EditScope was specified, or the EditScope was not found in
			/// the value's history.
			Other,
			/// The value was provided from a fallback value from the Inspector.
			Fallback
		};

		/// The relationship between `source()` and `editScope()`.
		SourceType sourceType() const;
		/// Returns a user-facing description of the source of the
		/// fallback value when `SourceType` is `Fallback`.
		const std::string &fallbackDescription() const;

		/// Editing
		/// =======

		/// Returns `true` if `acquireEdit()` will produce an edit,
		/// and `false` otherwise.
		bool editable() const;
		/// If `editable()` returns false, returns the reason why.
		/// If `canEdit( value )` returns false, `nonEditableReason( value )`
		/// returns the reason why. This should be displayed to the user.
		std::string nonEditableReason( const IECore::Object *value = nullptr ) const;

		/// Returns a plug that can be used to edit the property
		/// represented by this inspector, creating it if necessary.
		/// Throws if `!editable()`.
		Gaffer::ValuePlugPtr acquireEdit( bool createIfNecessary = true ) const;
		/// Returns a warning associated with the plug returned
		/// by `acquireEdit()`. This should be displayed to the user.
		std::string editWarning() const;

		/// Returns `true` if `disableEdit()` will disable the edit
		/// at `source()`, and `false` otherwise.
		bool canDisableEdit() const;
		/// If `canDisableEdit()` returns false, returns the reason why.
		/// This should be displayed to the user.
		std::string nonDisableableReason() const;
		/// Disables the edit at `source()`. Throws if
		/// `!canDisableEdit()`
		void disableEdit() const;

		/// Returns whether a direct edit can be made with the
		/// specified value.
		bool canEdit( const IECore::Object *value, std::string &failureReason ) const;
		/// Applies a direct edit with the specified value.
		/// Calls `acquireEdit()` to ensure a plug exists to
		/// receive the value.
		void edit( const IECore::Object *value ) const;

	private :

		Result( const IECore::ConstObjectPtr &value, const Gaffer::EditScopePtr &editScope );

		friend class Inspector;

		const IECore::ConstObjectPtr m_value;
		Gaffer::ValuePlugPtr m_source;
		SourceType m_sourceType;
		std::string m_fallbackDescription;
		Gaffer::EditScopePtr m_editScope;
		bool m_editScopeInHistory;

		struct Editors
		{
			AcquireEditFunctionOrFailure acquireEditFunction;
			std::string editWarning;
			DisableEditFunctionOrFailure disableEditFunction;
			CanEditFunction canEditFunction;
			EditFunction editFunction;
		};

		std::optional<Editors> m_editors;

};

} // namespace Private

} // namespace GafferSceneUI

#include "GafferSceneUI/Private/Inspector.inl"
