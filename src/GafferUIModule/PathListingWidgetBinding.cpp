//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "boost/python.hpp"

#include "PathListingWidgetBinding.h"

#include "Gaffer/BackgroundTask.h"
#include "Gaffer/FileSystemPath.h"
#include "Gaffer/ParallelAlgo.h"
#include "Gaffer/Path.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"
#include "Gaffer/Private/ScopedAssignment.h"

#include "IECorePython/RefCountedBinding.h"
#include "IECorePython/ScopedGILLock.h"
#include "IECorePython/ScopedGILRelease.h"

#include "IECore/DateTimeData.h"
#include "IECore/MessageHandler.h"
#include "IECore/PathMatcher.h"
#include "IECore/SearchPath.h"
#include "IECore/SimpleTypedData.h"

#include "boost/date_time/posix_time/conversion.hpp"
#include "boost/python/suite/indexing/container_utils.hpp"

#include "QtTest/QAbstractItemModelTester"

#include "QtCore/QAbstractItemModel"
#include "QtCore/QCoreApplication"
#include "QtCore/QDateTime"
#include "QtCore/QEvent"
#include "QtCore/QModelIndex"
#include "QtCore/QTimer"
#include "QtCore/QVariant"

#include "QtWidgets/QTreeView"
#include "QtWidgets/QFileIconProvider"

#include <chrono>
#include <unordered_map>

using namespace std::chrono_literals;
using namespace boost::python;
using namespace boost::posix_time;
using namespace Gaffer;

namespace
{

// QVariant does have `operator <`, but it's deprecated as it doesn't define a
// total ordering, making it unsuitable for our purposes.
// See https://doc.qt.io/qt-5/qvariant-obsolete.html#operator-lt.
bool variantLess( const QVariant &left, const QVariant &right )
{
	// Lexicographical comparison, first on type and then on value.

	if( left.userType() < right.userType() )
	{
		return true;
	}
	else if( right.userType() < left.userType() )
	{
		return false;
	}

	assert( left.userType() == right.userType() );

	switch( left.userType() )
	{
		case QVariant::Invalid :
			// Both values are invalid, making them equal.
			return false;
		case QVariant::Int :
			return left.toInt() < right.toInt();
		case QVariant::UInt :
			return left.toUInt() < right.toUInt();
		case QVariant::LongLong:
			return left.toLongLong() < right.toLongLong();
		case QVariant::ULongLong:
			return left.toULongLong() < right.toULongLong();
		case QMetaType::Float:
			return left.toFloat() < right.toFloat();
		case QVariant::Double:
			return left.toDouble() < right.toDouble();
		case QVariant::Char:
			return left.toChar() < right.toChar();
		case QVariant::Date:
			return left.toDate() < right.toDate();
		case QVariant::Time:
			return left.toTime() < right.toTime();
		case QVariant::DateTime:
			return left.toDateTime() < right.toDateTime();
		default :
			return left.toString() < right.toString();
	}
}

IECore::InternedString g_namePropertyName( "name" );

// Abstract class for extracting QVariants from Path objects
// in order to populate columns in the PathMode. Column
// objects only do the extraction, they are not responsible
// for storage at all.
class Column : public IECore::RefCounted
{

	public :

		IE_CORE_DECLAREMEMBERPTR( Column )

		virtual QVariant data( const Path *path, int role = Qt::DisplayRole ) const = 0;
		virtual QVariant headerData( int role = Qt::DisplayRole ) const = 0;

};

IE_CORE_DECLAREPTR( Column )

class StandardColumn : public Column
{

	public :

		IE_CORE_DECLAREMEMBERPTR( StandardColumn )

		StandardColumn( const std::string &label, IECore::InternedString propertyName )
			:	m_label( label.c_str() ), m_propertyName( propertyName )
		{
		}

		QVariant data( const Path *path, int role = Qt::DisplayRole ) const override
		{
			switch( role )
			{
				case Qt::DisplayRole :
					return variantFromProperty( path );
				default :
					return QVariant();
			}
		}

		QVariant headerData( int role = Qt::DisplayRole ) const override
		{
			if( role == Qt::DisplayRole )
			{
				return m_label;
			}
			return QVariant();
		}

	private :

		QVariant variantFromProperty( const Path *path ) const
		{
			// shortcut for getting the name property directly
			if( m_propertyName == g_namePropertyName )
			{
				if( path->names().size() )
				{
					return QVariant( path->names().back().c_str() );
				}
				else
				{
					return QVariant();
				}
			}

			IECore::ConstRunTimeTypedPtr property = path->property( m_propertyName );

			if( !property )
			{
				return QVariant();
			}

			switch( property->typeId() )
			{
				case IECore::StringDataTypeId :
					return static_cast<const IECore::StringData *>( property.get() )->readable().c_str();
				case IECore::IntDataTypeId :
					return static_cast<const IECore::IntData *>( property.get() )->readable();
				case IECore::UIntDataTypeId :
					return static_cast<const IECore::UIntData *>( property.get() )->readable();
				case IECore::UInt64DataTypeId :
					return (quint64)static_cast<const IECore::UInt64Data *>( property.get() )->readable();
				case IECore::FloatDataTypeId :
					return static_cast<const IECore::FloatData *>( property.get() )->readable();
				case IECore::DoubleDataTypeId :
					return static_cast<const IECore::DoubleData *>( property.get() )->readable();
				case IECore::DateTimeDataTypeId :
				{
					const IECore::DateTimeData *d = static_cast<const IECore::DateTimeData *>( property.get() );
					time_t t = ( d->readable() - from_time_t( 0 ) ).total_seconds();
					return QVariant( QDateTime::fromTime_t( t ) );
				}
				default :
				{
					// Fall back to using `str()` in python, to emulate old behaviour. If we find commonly
					// used types within large hierarchies falling through to here, we will need to give
					// them their own special case above, for improved performance.
					IECorePython::ScopedGILLock gilLock;
					object pythonProperty( boost::const_pointer_cast<IECore::RunTimeTyped>( property ) );
					boost::python::str pythonString( pythonProperty );
					return QVariant( boost::python::extract<const char *>( pythonString ) );
				}
			}
		}

		QVariant m_label;
		IECore::InternedString m_propertyName;

};

IE_CORE_DECLAREPTR( StandardColumn )

class IconColumn : public Column
{

	public :

		IE_CORE_DECLAREMEMBERPTR( IconColumn )

		IconColumn( const std::string &label, const std::string &prefix, IECore::InternedString propertyName )
			:	m_label( label.c_str() ), m_prefix( prefix ), m_propertyName( propertyName )
		{
		}

		QVariant data( const Path *path, int role = Qt::DisplayRole ) const override
		{
			if( role == Qt::DecorationRole )
			{
				IECore::ConstRunTimeTypedPtr property = path->property( m_propertyName );
				if( !property )
				{
					return QVariant();
				}

				std::string fileName = m_prefix;
				switch( property->typeId() )
				{
					case IECore::StringDataTypeId :
						fileName += static_cast<const IECore::StringData *>( property.get() )->readable();
						break;
					case IECore::IntDataTypeId :
						fileName += boost::lexical_cast<std::string>( static_cast<const IECore::IntData *>( property.get() )->readable() );
						break;
					case IECore::UInt64DataTypeId :
						fileName += boost::lexical_cast<std::string>( static_cast<const IECore::UInt64Data *>( property.get() )->readable() );
						break;
					case IECore::BoolDataTypeId :
						fileName += boost::lexical_cast<std::string>( static_cast<const IECore::BoolData *>( property.get() )->readable() );
						break;
					default :
						IECore::msg( IECore::Msg::Warning, "PathListingWidget", boost::str( boost::format( "Unsupported property type \"%s\"" ) % property->typeName() ) );
						return QVariant();
				}

				fileName += ".png";
				return g_iconCache.get( fileName );
			}
			return QVariant();
		}

		QVariant headerData( int role = Qt::DisplayRole ) const override
		{
			if( role == Qt::DisplayRole )
			{
				return m_label;
			}
			return QVariant();
		}

	private :

		QVariant m_label;
		std::string m_prefix;
		IECore::InternedString m_propertyName;

		static QVariant iconGetter( const std::string &fileName, size_t &cost, const IECore::Canceller *canceller )
		{
			const char *s = getenv( "GAFFERUI_IMAGE_PATHS" );
			IECore::SearchPath sp( s ? s : "" );

			boost::filesystem::path path = sp.find( fileName );
			if( path.empty() )
			{
				IECore::msg( IECore::Msg::Warning, "PathListingWidget", boost::str( boost::format( "Could not find file \"%s\"" ) % fileName ) );
				return QVariant();
			}

			cost = 1;
			return QPixmap( QString( path.string().c_str() ) );
		}

		typedef IECorePreview::LRUCache<std::string, QVariant> IconCache;
		static IconCache g_iconCache;

};

IconColumn::IconCache IconColumn::g_iconCache( IconColumn::iconGetter, 10000 );

IE_CORE_DECLAREPTR( IconColumn )

class FileIconColumn : public Column
{

	public :

		IE_CORE_DECLAREMEMBERPTR( FileIconColumn )

		FileIconColumn()
			:	m_label( "Type" )
		{
		}

		QVariant data( const Path *path, int role = Qt::DisplayRole ) const override
		{
			if( role == Qt::DecorationRole )
			{
				std::string s = path->string();

				if( const FileSystemPath *fileSystemPath = IECore::runTimeCast<const FileSystemPath>( path ) )
				{
					if( fileSystemPath->getIncludeSequences() )
					{
						IECore::FileSequencePtr seq = fileSystemPath->fileSequence();
						if( seq )
						{
							std::vector<IECore::FrameList::Frame> frames;
							seq->getFrameList()->asList( frames );
							s = seq->fileNameForFrame( *frames.begin() );
						}
					}
				}

				QString qs( s.c_str() );
				return m_iconProvider.icon( QFileInfo( qs ) );
			}
			return QVariant();
		}

		QVariant headerData( int role = Qt::DisplayRole ) const override
		{
			if( role == Qt::DisplayRole )
			{
				return m_label;
			}
			return QVariant();
		}

	private :

		QVariant m_label;
		QFileIconProvider m_iconProvider;

};

IE_CORE_DECLAREPTR( FileIconColumn )

static IECore::InternedString g_childPlaceholder( "childPlaceholder" );

// A QAbstractItemModel for the navigation of Gaffer::Paths.
// This allows us to view Paths in QTreeViews. This forms part
// of the internal implementation of PathListingWidget, the rest
// of which is implemented in Python.
class PathModel : public QAbstractItemModel
{

	Q_OBJECT

	public :

		PathModel( QTreeView *parent )
			:	QAbstractItemModel( parent ),
				m_rootItem( new Item( IECore::InternedString(), nullptr ) ),
				m_flat( true ),
				m_sortColumn( -1 ),
				m_sortOrder( Qt::AscendingOrder ),
				m_modifyingTreeViewExpansion( false ),
				m_updateScheduled( false )
		{
			connect( parent, &QTreeView::expanded, this, &PathModel::treeViewExpanded );
			connect( parent, &QTreeView::collapsed, this, &PathModel::treeViewCollapsed );
		}

		~PathModel()
		{
			// Cancel update task before the things it relies on are destroyed.
			// No need to flush pending edits, because Qt won't deliver the events
			// to us after we're destructed anyway.
			cancelUpdate( /* flushPendingEdits = */ false );
		}

		///////////////////////////////////////////////////////////////////
		// Our public methods - these don't mean anything to Qt
		///////////////////////////////////////////////////////////////////

		void setColumns( const std::vector<ColumnPtr> columns )
		{
			/// \todo Maintain persistent indices etc
			/// using `m_rootItem->update()`.

			// Cancel update and flush edit queue before we destroy
			// the items they reference.
			cancelUpdate();

			beginResetModel();
			m_columns = columns;
			m_rootItem = new Item( IECore::InternedString(), nullptr );
			endResetModel();
		}

		const std::vector<ColumnPtr> &getColumns() const
		{
			return m_columns;
		}

		Path *getRoot()
		{
			return m_rootPath.get();
		}

		void setRoot( PathPtr root )
		{
			// Cancel update and flush edit queue before we dirty
			// the items they reference.
			cancelUpdate();
			m_rootPath = root;
			m_rootItem->dirty();
			// Schedule update to process the dirtied items.
			scheduleUpdate();
		}

		void setFlat( bool flat )
		{
			if( flat == m_flat )
			{
				return;
			}

			cancelUpdate();
			beginResetModel();
			m_flat = flat;
			endResetModel();
		}

		bool getFlat() const
		{
			return m_flat;
		}

		// In Qt, the expanded indices are a property of the View rather than
		// the Model. This is perfectly logical, but it's tricky for an
		// asynchronous model, where the indices you want to expand may not
		// exist at the time you want to expand them. So we treat expansion as a
		// property of our model, allowing us to factor it in to our background
		// update logic. Our "source of truth" is the PathMatcher, not
		// `QTreeView::isExpanded()`.
		void setExpansion( const IECore::PathMatcher &expandedPaths )
		{
			cancelUpdate();

			m_expandedPaths = IECore::PathMatcher( expandedPaths );
			m_rootItem->dirtyExpansion();
			expansionChanged();

			scheduleUpdate();
		}

		const IECore::PathMatcher &getExpansion() const
		{
			return m_expandedPaths;
		}

		void attachTester()
		{
			if( !m_tester )
			{
				m_tester = std::make_unique<QAbstractItemModelTester>(
					this,
					// Outputs messages that are turned into test failures by
					// the handler installed by `GafferUI.TestCase.setUp()`.
					QAbstractItemModelTester::FailureReportingMode::Warning
				);
			}
		}

		Path::Names namesForIndex( const QModelIndex &index )
		{
			if( !index.isValid() || !m_rootPath )
			{
				return Path::Names();
			}

			std::vector<IECore::InternedString> result;
			Item *item = static_cast<Item *>( index.internalPointer() );
			while( item->parent() )
			{
				result.push_back( item->name() );
				item = item->parent();
			}
			std::reverse( result.begin(), result.end() );
			result.insert( result.begin(), m_rootPath->names().begin(), m_rootPath->names().end() );
			return result;
		}

		PathPtr pathForIndex( const QModelIndex &index )
		{
			if( !index.isValid() || !m_rootPath )
			{
				return nullptr;
			}
			PathPtr result = m_rootPath->copy();
			std::vector<IECore::InternedString> relativePath;
			Item *item = static_cast<Item *>( index.internalPointer() );
			while( item->parent() )
			{
				relativePath.push_back( item->name() );
				item = item->parent();
			}
			for( auto it = relativePath.rbegin(); it != relativePath.rend(); ++it )
			{
				result->append( *it );
			}
			return result;
		}

		QModelIndex indexForPath( const std::vector<IECore::InternedString> &path )
		{
			if( !m_rootPath )
			{
				return QModelIndex();
			}

			if( path.size() <= m_rootPath->names().size() )
			{
				return QModelIndex();
			}

			if( !equal( m_rootPath->names().begin(), m_rootPath->names().end(), path.begin() ) )
			{
				return QModelIndex();
			}

			QModelIndex result;
			Item *item = m_rootItem.get();
			for( size_t i = m_rootPath->names().size(); i < path.size(); ++i )
			{
				bool foundNextItem = false;
				const Item::ChildContainer &childItems = item->childItems( this );
				for( auto it = childItems.begin(), eIt = childItems.end(); it != eIt; ++it )
				{
					if( (*it)->name() == path[i] )
					{
						result = index( it - childItems.begin(), 0, result );
						item = it->get();
						foundNextItem = true;
						break;
					}
				}
				if( !foundNextItem )
				{
					return QModelIndex();
				}
			}

			return result;
		}

		QModelIndex indexForPath( const Path *path )
		{
			return indexForPath( path->names() );
		}

		std::vector<QModelIndex> indicesForPaths( const IECore::PathMatcher &paths )
		{
			std::vector<QModelIndex> result;
			if( !m_rootPath )
			{
				return result;
			}

			indicesForPathsWalk( m_rootItem.get(), Path::Names(), QModelIndex(), paths, result );
			return result;
		}

		void waitForPendingUpdates()
		{
			startUpdate();
			if( m_updateTask )
			{
				m_updateTask->wait();
			}
			QCoreApplication::sendPostedEvents( this, EditEvent::staticType() );
		}

	signals :

		void expansionChanged();

		///////////////////////////////////////////////////////////////////
		// QAbstractItemModel implementation - this is what Qt cares about
		///////////////////////////////////////////////////////////////////

	public :

		QVariant data( const QModelIndex &index, int role ) const override
		{
			if( !index.isValid() )
			{
				return QVariant();
			}

			Item *item = static_cast<Item *>( index.internalPointer() );
			return item->data( index.column(), role, this );
		}

		QVariant headerData( int section, Qt::Orientation orientation, int role = Qt::DisplayRole ) const override
		{
			if( orientation != Qt::Horizontal )
			{
				return QVariant();
			}
			return m_columns[section]->headerData( role );
		}

		QModelIndex index( int row, int column, const QModelIndex &parentIndex = QModelIndex() ) const override
		{
			Item *parentItem = parentIndex.isValid() ? static_cast<Item *>( parentIndex.internalPointer() ) : m_rootItem.get();

			if( row >=0 and row < (int)parentItem->childItems( this ).size() and column >=0 and column < (int)m_columns.size() )
			{
				return createIndex( row, column, parentItem->childItems( this )[row].get() );
			}
			else
			{
				return QModelIndex();
			}
		}

		QModelIndex parent( const QModelIndex &index ) const override
		{
			if( !index.isValid() )
			{
				return QModelIndex();
			}

			Item *item = static_cast<Item *>( index.internalPointer() );
			if( !item || item->parent() == m_rootItem )
			{
				return QModelIndex();
			}

			return createIndex( item->parent()->row(), 0, item->parent() );
		}

		int rowCount( const QModelIndex &parentIndex = QModelIndex() ) const override
		{
			Item *parentItem;
			if( parentIndex.isValid() )
			{
				// Parent is not the root item.
				if( m_flat || parentIndex.column() != 0 )
				{
					return 0;
				}
				parentItem = static_cast<Item *>( parentIndex.internalPointer() );
			}
			else
			{
				parentItem = m_rootItem.get();
			}
			return parentItem->childItems( this ).size();
		}

		int columnCount( const QModelIndex &parent = QModelIndex() ) const override
		{
			return m_columns.size();
		}

		// Although this method sounds like it means "take what you've got and
		// sort it right now", it seems really to also mean "and remember that
		// this is how you should sort all other stuff you might generate later".
		// So that's what we do. We also use a column of < 0 to say "turn off
		// sorting".
		void sort( int column, Qt::SortOrder order = Qt::AscendingOrder ) override
		{
			if( m_sortColumn == column && m_sortOrder == order )
			{
				return;
			}

			cancelUpdate();

			m_sortColumn = column;
			m_sortOrder = order;
			m_rootItem->dirty();

			scheduleUpdate();
		}

	private :

		// Async update mechanism
		// ======================
		//
		// Queries such as `Path::children()` and `Path::property()` can take
		// significant amounts of time, for instance when querying a slow
		// filesystem via FileSystemPath or a complex scene via ScenePath. We
		// want to avoid blocking the UI when making such queries, to avoid user
		// frustration.
		//
		// We therefore return immediately from methods such as
		// `PathModel::rowCount()` and `PathModel::data()`, even if it means
		// returning default or stale results. At the same time, we call
		// `scheduleUpdate()` to launch a background task which will compute updates for the
		// model asynchronously.
		//
		// We need to apply the updates and signal them to Qt on the main thread,
		// for which we use `queueEdit()`.

		// Arranges to peform a background update after a short delay.
		void scheduleUpdate()
		{
			if( !m_rootPath || m_updateScheduled )
			{
				return;
			}

			// It's typical for several queries to `PathModel::data()` and
			// `PathModel::rowCount()` etc to come in a little flurry, for all
			// of the visible items in the QTreeView. So we delay the start of
			// the update for a grace period to avoid repeatedly starting and
			// cancelling updates when each query happens.
			QTimer::singleShot(
				50ms,
				// Using `this` as the context for Qt means that we can safely
				// call a method, because the timer will be cancelled if we are
				// destroyed.
				this,
				&PathModel::startUpdate
			);
			m_updateScheduled = true;
		}

		void startUpdate()
		{
			if( !m_updateScheduled )
			{
				// We can get here if `waitForPendingUpdates()` starts the
				// update early, and the timer triggers afterwards. Or if
				// `waitForPendingUpdates()` is called when there are no
				// updates to do.
				return;
			}

			// Cancel previous update and flush pending edits, as they
			// may delete or modify the items being visited by the
			// background task.
			cancelUpdate();

			// And then we can reschedule our update task.
			m_updateTask = ParallelAlgo::callOnBackgroundThread(
				/// \todo We need to pass an appropriate subject here
				/// based on the root path, so that we can participate
				/// in cancellation appropriately.
				/* subject = */ nullptr,
				[this] {
					m_rootItem->update( this );
				}
			);
			m_updateScheduled = false;
		}

		// Cancels the current background update, optionally flushing the
		// queue of pending edits.
		void cancelUpdate( bool flushPendingEdits = true )
		{
			m_updateTask.reset(); // Implicitly calls `cancelAndWait()`.
			if( flushPendingEdits )
			{
				QCoreApplication::sendPostedEvents( this, EditEvent::staticType() );
			}
		}

		// Custom event class used by `queueEdit()`. This simply holds a
		// `std::function` to be executed on the main thread, allowing us to
		// write the edit as a lambda at the call site.
		struct EditEvent : public QEvent
		{

			using Edit = std::function<void()>;

			EditEvent( const Edit &edit )
				:	QEvent( staticType() ), edit( edit )
			{
			}

			Edit edit;

			static QEvent::Type staticType()
			{
				static QEvent::Type g_type = (QEvent::Type)registerEventType();
				return g_type;
			}

		};

		// Queues an arbitrary edit to be made on the UI thread.
		template<typename F>
		void queueEdit( const F &edit )
		{
			// Qt takes responsibility for deleting the event after it is
			// delivered.
			QCoreApplication::postEvent( this, new EditEvent( edit ) );
		}

		// Executed the edit events posted by `queueEdit()`.
		void customEvent( QEvent *event ) override
		{
			if( event->type() == EditEvent::staticType() )
			{
				static_cast<EditEvent *>( event )->edit();
				return;
			}
			QObject::customEvent( event );
		}

		// A single item in the PathModel - stores a path and caches
		// data extracted from it to provide the model content.
		// Uses `scheduleUpdate()` and `queueEdit()` to update itself
		// asynchronously.
		struct Item : public IECore::RefCounted
		{

			Item( const IECore::InternedString &name, Item *parent )
				:	m_name( name ),
					m_parent( parent ),
					m_row( -1 ), // Assigned true value in `updateChildItems()`
					m_dataState( State::Unrequested ),
					m_childItemsState( State::Unrequested ),
					m_expansionDirty( true ),
					m_expandedInTreeView( false )
			{
				static auto g_emptyChildItems = std::make_shared<PathModel::Item::ChildContainer>();
				m_childItems = g_emptyChildItems;
			}

			IE_CORE_DECLAREMEMBERPTR( Item )

			const IECore::InternedString &name() const
			{
				return m_name;
			}

			void dirty()
			{
				// This is just intended to be called on the root item by the
				// PathModel when the path changes.
				assert( !m_parent );
				dirtyWalk();
			}

			void dirtyExpansion()
			{
				m_expansionDirty = true;
				for( const auto &child : *m_childItems )
				{
					child->dirtyExpansion();
				}
			}

			void treeViewExpansionChanged( bool expanded )
			{
				m_expandedInTreeView = expanded;
			}

			void update( PathModel *model )
			{
				// We take a copy of `expandedPaths` because it may be modified
				// on the UI thread by `treeViewExpanded()` while we run in the
				// background.
				updateWalk( model, model->m_rootPath.get(), IECore::PathMatcher( model->m_expandedPaths ) );
			}

			Item *parent()
			{
				return m_parent;
			}

			int row()
			{
				return m_row;
			}

			// Returns the data for the specified column and role. The Item is
			// responsible for caching the results of these queries internally.
			QVariant data( int column, int role, const PathModel *model )
			{
				if( requestIfUnrequested( m_dataState ) )
				{
					const_cast<PathModel *>( model )->scheduleUpdate();
				}

				if( column >= (int)m_displayData.size() )
				{
					// We haven't computed any data yet.
					return QVariant();
				}

				switch( role )
				{
					case Qt::DisplayRole :
						return m_displayData[column];
					case Qt::DecorationRole :
						return m_decorationData[column];
					default :
						return QVariant();
				}
			}

			using ChildContainer = std::vector<Ptr>;

			ChildContainer &childItems( const PathModel *model )
			{
				if( requestIfUnrequested( m_childItemsState ) )
				{
					const_cast<PathModel *>( model )->scheduleUpdate();
				}
				return *m_childItems;
			}

			private :

				void dirtyWalk()
				{
					if( m_dataState == State::Clean )
					{
						m_dataState = State::Dirty;
					}
					if( m_childItemsState == State::Clean )
					{
						m_childItemsState = State::Dirty;
					}
					for( const auto &child : *m_childItems )
					{
						child->dirtyWalk();
					}
				}

				void updateWalk( PathModel *model, const Path *path, const IECore::PathMatcher &expandedPaths )
				{
					updateData( model, path );
					updateExpansion( model, path, expandedPaths );
					std::shared_ptr<ChildContainer> updatedChildItems = updateChildItems( model, path );
					PathPtr childPath = path->copy();
					childPath->append( g_childPlaceholder );
					for( const auto &child : *updatedChildItems )
					{
						childPath->set( childPath->names().size() - 1, child->name() );
						child->updateWalk( model, childPath.get(), expandedPaths );
					}
				}

				static QVariant dataForSort( const std::vector<QVariant> &displayData, PathModel *model )
				{
					if( model->m_sortColumn < 0 || model->m_sortColumn >= (int)displayData.size() )
					{
						return QVariant();
					}
					return displayData[model->m_sortColumn];
				}

				// Updates data and returns the value that should be used for sorting.
				// This value is returned because the actual edit to `m_displayData` will not be
				// complete until the queued edit is processed by the UI thread.
				QVariant updateData( PathModel *model, const Path *path )
				{
					if( m_dataState == State::Clean || m_dataState == State::Unrequested )
					{
						return dataForSort( m_displayData, model );
					}

					// We generate data for all columns and roles at once, on the
					// assumption that access to one is likely to indicate upcoming
					// accesses to the others.

					std::vector<QVariant> newDisplayData;
					std::vector<QVariant> newDecorationData;

					newDisplayData.reserve( model->m_columns.size() );
					newDecorationData.reserve( model->m_columns.size() );

					for( int i = 0, e = model->m_columns.size(); i < e; ++i )
					{
						QVariant displayData;
						QVariant decorationData;
						try
						{
							displayData = model->m_columns[i]->data( path, Qt::DisplayRole );
							decorationData = model->m_columns[i]->data( path, Qt::DecorationRole );
						}
						catch( const std::exception &e )
						{
							// Qt doesn't use exceptions for error handling,
							// so we must suppress them.
							IECore::msg( IECore::Msg::Warning, "PathListingWidget", e.what() );
						}
						catch( ... )
						{
							IECore::msg( IECore::Msg::Warning, "PathListingWidget", "Unknown error" );
						}

						newDisplayData.push_back( displayData );
						newDecorationData.push_back( decorationData );
					}

					if( newDisplayData == m_displayData && newDecorationData == m_decorationData )
					{
						// No update necessary.
						m_dataState = State::Clean;
						return dataForSort( m_displayData, model );
					}

					if( m_row == -1 )
					{
						// We have just been created in `updateChildItems()` and haven't
						// been made visible to Qt yet. No need to emit `dataChanged` or
						// worry about concurrent access from the UI thread.
						m_displayData.swap( newDisplayData );
						m_decorationData.swap( newDecorationData );
						m_dataState = State::Clean;
						return dataForSort( m_displayData, model );
					}

					// Mark clean _now_, to avoid a double update if we are
					// called from our parent's `updateChildItems()` (to obtain
					// data for sorting) and then called again from
					// `updateWalk()` before the queued edit is applied.
					m_dataState = State::Clean;

					// Get result before we move `newDisplayData` into the lambda.
					const QVariant result = dataForSort( newDisplayData, model );

					model->queueEdit(

						[this, model, newDisplayData = std::move( newDisplayData ), newDecorationData = std::move( newDecorationData )] () mutable {

							m_displayData.swap( newDisplayData );
							m_decorationData.swap( newDecorationData );
							model->dataChanged( model->createIndex( m_row, 0, this ), model->createIndex( m_row, model->m_columns.size() - 1, this ) );

						}

					);

					return result;
				}

				void updateExpansion( PathModel *model, const Gaffer::Path *path, const IECore::PathMatcher &expandedPaths )
				{
					if( !m_expansionDirty )
					{
						return;
					}

					const unsigned match = expandedPaths.match( path->names() );
					const bool expanded = match & IECore::PathMatcher::ExactMatch;

					if( expanded != m_expandedInTreeView )
					{
						model->queueEdit(
							[this, model, expanded] {
								QTreeView *treeView = dynamic_cast<QTreeView *>( model->QObject::parent() );
								Private::ScopedAssignment<bool> assignment( model->m_modifyingTreeViewExpansion, true );
								treeView->setExpanded( model->createIndex( m_row, 0, this ), expanded );
								m_expandedInTreeView = expanded;
							}
						);
					}

					if( match & IECore::PathMatcher::DescendantMatch )
					{
						// Force creation of children so we can expand them.
						requestIfUnrequested( m_childItemsState );
					}

					m_expansionDirty = false;
				}

				// Returns the updated ChildContainer. This will not be visible in the model
				// until the queued edit is executed. It is returned so that we can update
				// the not-yet-visible children in `updateWalk()`.
				std::shared_ptr<ChildContainer> updateChildItems( PathModel *model, const Gaffer::Path *path )
				{
					if( m_childItemsState == State::Unrequested || m_childItemsState == State::Clean )
					{
						return m_childItems;
					}

					// Construct a new ChildContainer to replace our previous children.
					// Where possible we reuse existing children instead of creating new
					// ones.

					auto newChildItemsPtr = std::make_shared<ChildContainer>();
					ChildContainer &newChildItems = *newChildItemsPtr;

					std::vector<Gaffer::PathPtr> children;
					try
					{
						path->children( children );
					}
					catch( const std::exception &e )
					{
						IECore::msg( IECore::Msg::Error, "PathListingWidget", e.what() );
					}

					std::unordered_map<IECore::InternedString, Item *> oldChildMap;
					for( const auto &oldChild : *m_childItems )
					{
						oldChildMap[oldChild->m_name] = oldChild.get();
					}

					for( auto it = children.begin(), eIt = children.end(); it != eIt; ++it )
					{
						auto oldIt = oldChildMap.find( (*it)->names().back() );
						if( oldIt != oldChildMap.end() )
						{
							// Reuse previous item.
							Ptr itemToReuse = oldIt->second;
							newChildItems.push_back( itemToReuse );
						}
						else
						{
							// Make new item.
							newChildItems.push_back( new Item( (*it)->names().back(), this ) );
						}
					}

					// Sort the new container if necessary.

					if( model->m_sortColumn >= 0 && model->m_sortColumn < (int)model->m_columns.size() )
					{
						using SortablePair = std::pair<QVariant, size_t>;
						std::vector<SortablePair> sortedIndices;
						sortedIndices.reserve( newChildItems.size() );

						for( const auto &childItem : newChildItems )
						{
							requestIfUnrequested( childItem->m_dataState );
							sortedIndices.push_back( SortablePair(
								childItem->updateData( model, children[sortedIndices.size()].get() ),
								sortedIndices.size()
							) );
						}

						std::sort(
							sortedIndices.begin(), sortedIndices.end(),
							[model] ( const SortablePair &l, const SortablePair &r ) {
								return model->m_sortOrder == Qt::AscendingOrder ? variantLess( l.first, r.first ) : variantLess( r.first, l.first );
							}
						);

						ChildContainer sortedChildItems;
						sortedChildItems.reserve( sortedIndices.size() );
						for( const auto &item : sortedIndices )
						{
							sortedChildItems.push_back( newChildItems[item.second] );
						}
						newChildItems.swap( sortedChildItems );
					}

					// Early out if nothing has changed.

					if( newChildItems == *m_childItems )
					{
						m_childItemsState = State::Clean;
						return m_childItems;
					}

					// If we had children before, figure out the mapping from old to new,
					// so we can tell Qt about it. This is necessary so that persistent
					// indices used to represent selection and expansion remain valid.

					QModelIndexList changedPersistentIndexesFrom, changedPersistentIndexesTo;

					std::unordered_map<IECore::InternedString, size_t> newChildMap;
					for( size_t i = 0; i < newChildItems.size(); ++i )
					{
						newChildMap[newChildItems[i]->m_name] = i;
					}

					for( const auto &oldChild : *m_childItems )
					{
						auto nIt = newChildMap.find( oldChild->m_name );
						if( nIt != newChildMap.end() )
						{
							const int toRow = nIt->second;
							for( int c = 0, ce = model->getColumns().size(); c < ce; ++c )
							{
								changedPersistentIndexesFrom.append( model->createIndex( oldChild->row(), c, oldChild.get() ) );
								changedPersistentIndexesTo.append( model->createIndex( toRow, c, newChildItems[toRow].get() ) );
							}
						}
						else
						{
							oldChild->invalidateIndexes( model, changedPersistentIndexesFrom, changedPersistentIndexesTo );
						}
					}

					// Apply the update.

					model->queueEdit(

						[this, model, newChildItemsPtr, changedPersistentIndexesFrom, changedPersistentIndexesTo]() mutable {

							// We have to mark ourselves clean _before_ changing
							// layout, to avoid recursion when Qt responds to
							// `layoutAboutToBeChanged()`.
							m_childItemsState = State::Clean;
							QList<QPersistentModelIndex> parents = { model->createIndex( row(), 0, this ) };
							model->layoutAboutToBeChanged( parents );

							m_childItems = newChildItemsPtr;
							for( size_t i = 0; i < m_childItems->size(); ++i )
							{
								(*m_childItems)[i]->m_row = i;
							}

							model->changePersistentIndexList( changedPersistentIndexesFrom, changedPersistentIndexesTo );
							model->layoutChanged( parents );

						}

					);

					return newChildItemsPtr;
				}

				void invalidateIndexes( PathModel *model, QModelIndexList &from, QModelIndexList &to )
				{
					for( int c = 0, ce = model->getColumns().size(); c < ce; ++c )
					{
						from.append( model->createIndex( m_row, c, this ) );
						to.append( QModelIndex() );
					}
					for( const auto &child : *m_childItems )
					{
						child->invalidateIndexes( model, from, to );
					}
				}

				const IECore::InternedString m_name;
				Item *m_parent;
				int m_row;

				// State transitions :
				//
				// - Unrequested->Requested : When first queried.
				// - Requested->Clean : When first updated.
				// - Clean->Dirty : When path changes.
				// - Dirty->Clean : On all subsequent updates.
				enum class State
				{
					// Initial state. Not yet requested by clients
					// of the model, therefore not yet computed, and not
					// in need of consideration during recursive updates.
					Unrequested,
					// Has just been requested for the first time. Needs
					// to be updated, but there is no need to emit change
					// signals for the first update.
					Requested,
					// Computed and up to date.
					Clean,
					// Stale data that needs recomputing.
					Dirty
				};

				static bool requestIfUnrequested( std::atomic<State> &state )
				{
					State unrequested = State::Unrequested;
					return state.compare_exchange_strong( unrequested, State::Requested );
				}

				std::atomic<State> m_dataState;
				std::vector<QVariant> m_displayData;
				std::vector<QVariant> m_decorationData;

				std::atomic<State> m_childItemsState;
				// Children are held by `shared_ptr` in order to support
				// asynchronous update. Newly created children aren't owned
				// by the Item until `m_childItems` is assigned on the UI
				// thread, which may happen before, during, or after the
				// recursive background update completes.
				std::shared_ptr<ChildContainer> m_childItems;

				bool m_expansionDirty;
				// Mirrors current Qt expansion status, because we can't query it
				// directly in a threadsafe way.
				bool m_expandedInTreeView;

		};

		void indicesForPathsWalk( Item *item, const Path::Names &itemPath, const QModelIndex &itemIndex, const IECore::PathMatcher &paths, std::vector<QModelIndex> &indices )
		{
			/// \todo Using `match()` here isn't right, because we want to
			/// treat wildcards in the selection verbatim rather than perform
			/// matching with them. We should use `find()`, but that doesn't
			/// provide a convenient way of checking for descendant matches.
			const unsigned match = paths.match( itemPath );
			if( match & IECore::PathMatcher::ExactMatch )
			{
				indices.push_back( itemIndex );
			}

			if( !(match & IECore::PathMatcher::DescendantMatch) )
			{
				return;
			}

			size_t row = 0;
			Path::Names childItemPath = itemPath;
			childItemPath.push_back( IECore::InternedString() ); // Room for child name
			for( const auto &childItem : item->childItems( this ) )
			{
				const QModelIndex childIndex = index( row++, 0, itemIndex );
				childItemPath.back() = childItem->name();
				indicesForPathsWalk( childItem.get(), childItemPath, childIndex, paths, indices );
			}
		}

		void treeViewExpanded( const QModelIndex &index )
		{
			if( m_modifyingTreeViewExpansion )
			{
				// When we're modifying the expansion ourselves, it's to mirror
				// `m_expandedPaths` into the tree view. In this case there is
				// no need to sync back into `m_expandedPaths`.
				return;
			}

			static_cast<Item *>( index.internalPointer() )->treeViewExpansionChanged( true );

			const Path::Names expandedPath = namesForIndex( index );
			// It's possible for `addPath()` to return false if the path is
			// already added, but the async update hasn't transferred it to
			// the QTreeView yet (allowing a user to expand it manually in
			// the meantime).
			if( m_expandedPaths.addPath( expandedPath ) )
			{
				expansionChanged();
			}
		}

		void treeViewCollapsed( const QModelIndex &index )
		{
			if( m_modifyingTreeViewExpansion )
			{
				return;
			}

			static_cast<Item *>( index.internalPointer() )->treeViewExpansionChanged( false );

			const Path::Names collapsedPath = namesForIndex( index );
			if( m_expandedPaths.removePath( collapsedPath ) )
			{
				expansionChanged();
			}
		}

		Gaffer::PathPtr m_rootPath;

		Item::Ptr m_rootItem;
		bool m_flat;
		std::vector<ColumnPtr> m_columns;
		int m_sortColumn;
		Qt::SortOrder m_sortOrder;
		std::unique_ptr<QAbstractItemModelTester> m_tester;

		IECore::PathMatcher m_expandedPaths;
		bool m_modifyingTreeViewExpansion;

		std::unique_ptr<Gaffer::BackgroundTask> m_updateTask;
		bool m_updateScheduled;

};

void setColumns( uint64_t treeViewAddress, object pythonColumns )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	std::vector<ColumnPtr> columns;
	boost::python::container_utils::extend_container( columns, pythonColumns );
	IECorePython::ScopedGILRelease gilRelease;
	model->setColumns( columns );
}

list getColumns( uint64_t treeViewAddress )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	const std::vector<ColumnPtr> &columns = model->getColumns();
	list result;
	for( std::vector<ColumnPtr>::const_iterator it = columns.begin(), eIt = columns.end(); it != eIt; ++it )
	{
		result.append( *it );
	}
	return result;
}

void updateModel( uint64_t treeViewAddress, Gaffer::PathPtr path )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	IECorePython::ScopedGILRelease gilRelease;
	if( !model )
	{
		model = new PathModel( treeView );
		treeView->setModel( model );
	}
	model->setRoot( path );
}

void setFlat( uint64_t treeViewAddress, bool flat )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	IECorePython::ScopedGILRelease gilRelease;
	model->setFlat( flat );
}

bool getFlat( uint64_t treeViewAddress )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	return model->getFlat();
}

void setExpansion( uint64_t treeViewAddress, const IECore::PathMatcher &paths )
{
	IECorePython::ScopedGILRelease gilRelease;

	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	model->setExpansion( paths );
}

IECore::PathMatcher getExpansion( uint64_t treeViewAddress )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	return model ? model->getExpansion() : IECore::PathMatcher();
}

void propagateExpandedWalk( QTreeView *treeView, PathModel *model, QModelIndex index, bool expanded, int numLevels )
{
	for( int i = 0, e = model->rowCount( index ); i < e; ++i )
	{
		QModelIndex childIndex = model->index( i, 0, index );
		treeView->setExpanded( childIndex, expanded );
		if( numLevels - 1 > 0 )
		{
			propagateExpandedWalk( treeView, model, childIndex, expanded, numLevels - 1 );
		}
	}
}

void propagateExpanded( uint64_t treeViewAddress, uint64_t modelIndexAddress, bool expanded, int numLevels )
{
	IECorePython::ScopedGILRelease gilRelease;

	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	if( !model )
	{
		return;
	}

	QModelIndex *modelIndex = reinterpret_cast<QModelIndex *>( modelIndexAddress );
	propagateExpandedWalk( treeView, model, *modelIndex, expanded, numLevels );
}

void setSelection( uint64_t treeViewAddress, const IECore::PathMatcher &paths, bool scrollToFirst, bool expandNonLeaf )
{
	IECorePython::ScopedGILRelease gilRelease;

	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	if( !model )
	{
		return;
	}

	const std::vector<QModelIndex> indices = model->indicesForPaths( paths );
	if( treeView->selectionMode() != QAbstractItemView::ExtendedSelection && indices.size() > 1 )
	{
		throw IECore::InvalidArgumentException( "More than one path selected" );
	}

	QItemSelection itemSelection;
	for( const auto &modelIndex : indices )
	{
		if( !modelIndex.isValid() )
		{
			continue;
		}
		itemSelection.select( modelIndex, modelIndex.sibling( modelIndex.row(), model->columnCount() - 1 ) );
		if( expandNonLeaf && !model->pathForIndex( modelIndex )->isLeaf() )
		{
			treeView->setExpanded( modelIndex, true );
		}
	}

	QItemSelectionModel *selectionModel = treeView->selectionModel();
	selectionModel->select( itemSelection, QItemSelectionModel::Select );

	if( scrollToFirst && !indices.empty() )
	{
		treeView->scrollTo( indices[0], QTreeView::EnsureVisible );
		selectionModel->setCurrentIndex( indices[0], QItemSelectionModel::Current );
	}
}

IECore::PathMatcher getSelection( uint64_t treeViewAddress )
{
	IECorePython::ScopedGILRelease gilRelease;

	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );

	QModelIndexList selectedIndices = treeView->selectionModel()->selectedIndexes();
	IECore::PathMatcher result;
	for( const auto &index : selectedIndices )
	{
		result.addPath( model->pathForIndex( index )->names() );
	}
	return result;
}

PathPtr pathForIndex( uint64_t treeViewAddress, uint64_t modelIndexAddress )
{
	// put a GIL release here in case scene child name computations etc triggered by
	// this function end up calling into python:
	IECorePython::ScopedGILRelease r;
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	if( !model )
	{
		return nullptr;
	}

	QModelIndex *modelIndex = reinterpret_cast<QModelIndex *>( modelIndexAddress );
	return model->pathForIndex( *modelIndex );
}

void indexForPath( uint64_t treeViewAddress, const Path *path, uint64_t modelIndexAddress )
{
	// put a GIL release here in case scene child name computations etc triggered by
	// this function end up calling into python:
	IECorePython::ScopedGILRelease r;
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	QModelIndex *modelIndex = reinterpret_cast<QModelIndex *>( modelIndexAddress );
	*modelIndex = model->indexForPath( path );
}

list pathsForPathMatcher( uint64_t treeViewAddress, const IECore::PathMatcher &pathMatcher )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	if( !model )
	{
		return list();
	}

	std::vector<QModelIndex> indices;
	{
		IECorePython::ScopedGILRelease gilRelease;
		indices = model->indicesForPaths( pathMatcher );
	}

	list result;
	for( const auto &index : indices )
	{
		result.append( PathPtr( model->pathForIndex( index ) ) );
	}

	return result;
}

void attachTester( uint64_t treeViewAddress )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	model->attachTester();
}

void waitForPendingUpdates( uint64_t modelAddress )
{
	PathModel *model = reinterpret_cast<PathModel *>( modelAddress );
	IECorePython::ScopedGILRelease gilRelease;
	model->waitForPendingUpdates();
}

} // namespace

void GafferUIModule::bindPathListingWidget()
{
	// Ideally we'd bind PathModel so it could be used in
	// the normal fashion from Python. But that would mean
	// using SIP or Shiboken to make bindings compatible
	// with PyQt or PySide. It would also mean each Gaffer
	// build would only be compatible with one or the other
	// of the Qt bindings, whereas we want a single build
	// to be compatible with either. We therefore simply
	// bind the minimum set of methods we need as free
	// functions and then use them from within PathListingWidget.py.

	def( "_pathListingWidgetSetColumns", &setColumns );
	def( "_pathListingWidgetGetColumns", &getColumns );
	def( "_pathListingWidgetUpdateModel", &updateModel );
	def( "_pathListingWidgetSetFlat", &setFlat );
	def( "_pathListingWidgetGetFlat", &getFlat );
	def( "_pathListingWidgetSetExpansion", &setExpansion );
	def( "_pathListingWidgetGetExpansion", &getExpansion );
	def( "_pathListingWidgetPropagateExpanded", &propagateExpanded );
	def( "_pathListingWidgetSetSelection", &setSelection );
	def( "_pathListingWidgetGetSelection", &getSelection );
	def( "_pathListingWidgetPathForIndex", &pathForIndex );
	def( "_pathListingWidgetIndexForPath", &indexForPath );
	def( "_pathListingWidgetPathsForPathMatcher", &pathsForPathMatcher );
	def( "_pathListingWidgetAttachTester", &attachTester );
	def( "_pathModelWaitForPendingUpdates", &waitForPendingUpdates );

	IECorePython::RefCountedClass<Column, IECore::RefCounted>( "_PathListingWidgetColumn" );

	IECorePython::RefCountedClass<StandardColumn, Column>( "_PathListingWidgetStandardColumn" )
		.def( init<const std::string &, IECore::InternedString>() )
	;

	IECorePython::RefCountedClass<IconColumn, Column>( "_PathListingWidgetIconColumn" )
		.def( init<const std::string &, const std::string &, IECore::InternedString>() )
	;

	IECorePython::RefCountedClass<FileIconColumn, Column>( "_PathListingWidgetFileIconColumn" )
		.def( init<>() )
	;
}

#include "PathListingWidgetBinding.moc"
