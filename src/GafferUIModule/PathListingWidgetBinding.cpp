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

#include "GafferUI/PathColumn.h"

#include "Gaffer/BackgroundTask.h"
#include "Gaffer/Context.h"
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

#include "boost/algorithm/string/predicate.hpp"
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

#include "QtGui/QGuiApplication"

#include "QtWidgets/QFileIconProvider"
#include "QtWidgets/QTreeView"
#include "QtWidgets/QStyledItemDelegate"

#include "fmt/format.h"

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

IECore::PathMatcher ancestorPaths( const IECore::PathMatcher &paths )
{
	IECore::PathMatcher ancestorPaths;
	for( auto &path : paths )
	{
		if( path.size() > 0 )
		{
			auto parentPath = path; parentPath.pop_back();
			ancestorPaths.addPath( parentPath );
		}
	}

	return ancestorPaths;
}

IECorePreview::LRUCache<std::string, QPixmap> g_pixmapCache(
	// Getter
	[] ( const std::string &fileName, size_t &cost, const IECore::Canceller *canceller ) -> QPixmap
	{
		cost = 1;

		// Contrived code path to allow us to use QFileIconProvider for
		// FileIconColumn, without exposing Qt in the PathColumn API.
		static const std::string g_fileIconPrefix( "fileIcon:" );
		if( boost::starts_with( fileName, g_fileIconPrefix ) )
		{
			static QFileIconProvider g_provider;
			QIcon icon = g_provider.icon( QFileInfo( fileName.c_str() + g_fileIconPrefix.size() ) );
			return icon.pixmap( 16 );
		}

		// Standard code path - load icon from file.
		const char *s = getenv( "GAFFERUI_IMAGE_PATHS" );
		IECore::SearchPath sp( s ? s : "" );
		boost::filesystem::path path = sp.find( fileName );
		if( path.empty() )
		{
			IECore::msg( IECore::Msg::Warning, "PathListingWidget", fmt::format( "Could not find file \"{}\"", fileName ) );
			return QPixmap();
		}
		return QPixmap( QString( path.generic_string().c_str() ) );
	},
	/* maxCost = */ 10000
);

// Equivalent to `GafferUI.NumericWidget.formatValue()`.
QString doubleToString( double v )
{
	QString result = QString::number( v, 'f', 4 );
	for( int i = result.size() - 1; i; --i )
	{
		const QChar c = result.at( i );
		if( c == '.' )
		{
			result.truncate( i );
			return result;
		}
		else if ( c != '0' )
		{
			result.truncate( i + 1 );
			return result;
		}
	}
	return result;
}

template<typename T>
QString vectorToString( const T &v )
{
	QString result;
	for( unsigned i = 0; i < T::dimensions(); ++i )
	{
		if( i )
		{
			result += " ";
		}
		result += doubleToString( v[i] );
	}
	return result;
}

QVariant dataToVariant( const IECore::Data *value, int role )
{
	if( !value )
	{
		return QVariant();
	}

	if( role == Qt::DecorationRole )
	{
		switch( value->typeId() )
		{
			case IECore::StringDataTypeId :
				return g_pixmapCache.get( static_cast<const IECore::StringData *>( value )->readable() );
			case IECore::Color3fDataTypeId : {
				const Imath::Color3f &c = static_cast<const IECore::Color3fData *>( value )->readable();
				return QColor::fromRgbF( c[0], c[1], c[2] );
			}
			case IECore::CompoundDataTypeId : {
				auto d = static_cast<const IECore::CompoundData *>( value );
				QIcon icon;
				if( const auto *s = d->member<IECore::StringData>( "state:normal" ) )
				{
					if( s->readable().size() )
					{
						icon.addPixmap( g_pixmapCache.get( s->readable() ) );
					}
				}
				if( const auto *s = d->member<IECore::StringData>( "state:highlighted" ) )
				{
					if( s->readable().size() )
					{
						QPixmap pixmap = g_pixmapCache.get( s->readable() );
						if( !pixmap.isNull() )
						{
							if( icon.isNull() )
							{
								// We don't have a normal state, meaning we
								// don't want to display anything unless
								// hovered. But Qt interprets this differently,
								// and will fall back (forwards?!) to the Active
								// state if the Normal state isn't there.
								// Provide a transparent pixmap to avoid this.
								QPixmap empty( pixmap.size() );
								empty.fill( QColor( 0, 0, 0, 0 ) );
								icon.addPixmap( empty );
							}
							icon.addPixmap( pixmap, QIcon::Active );
						}
					}
				}
				return !icon.isNull() ? icon : QVariant();
			}
			default :
				return QVariant();
		}
	}

	if( role == Qt::BackgroundRole )
	{
		switch( value->typeId() )
		{
			case IECore::Color3fDataTypeId : {
				const Imath::Color3f c = static_cast<const IECore::Color3fData *>( value )->readable() * 255.0f;
				return QColor( Imath::clamp( c[0], 0.0f, 255.0f ), Imath::clamp( c[1], 0.0f, 255.0f ), Imath::clamp( c[2], 0.0f, 255.0f ) );
			}
			case IECore::Color4fDataTypeId : {
				const Imath::Color4f c = static_cast<const IECore::Color4fData *>( value )->readable() * 255.0f;
				return QColor( Imath::clamp( c[0], 0.0f, 255.0f ), Imath::clamp( c[1], 0.0f, 255.0f ), Imath::clamp( c[2], 0.0f, 255.0f ), Imath::clamp( c[3], 0.0f, 255.0f ) );
			}
			default :
				return QVariant();
		}
	}

	switch( value->typeId() )
	{
		case IECore::StringDataTypeId :
			return static_cast<const IECore::StringData *>( value )->readable().c_str();
		case IECore::IntDataTypeId :
			return static_cast<const IECore::IntData *>( value )->readable();
		case IECore::UIntDataTypeId :
			return static_cast<const IECore::UIntData *>( value )->readable();
		case IECore::UInt64DataTypeId :
			return (quint64)static_cast<const IECore::UInt64Data *>( value )->readable();
		case IECore::FloatDataTypeId :
			return doubleToString( static_cast<const IECore::FloatData *>( value )->readable() );
		case IECore::DoubleDataTypeId :
			return doubleToString( static_cast<const IECore::DoubleData *>( value )->readable() );
		case IECore::V2fDataTypeId :
			return vectorToString( static_cast<const IECore::V2fData *>( value )->readable() );
		case IECore::V3fDataTypeId :
			return vectorToString( static_cast<const IECore::V3fData *>( value )->readable() );
		case IECore::Color3fDataTypeId :
			return vectorToString( static_cast<const IECore::Color3fData *>( value )->readable() );
		case IECore::Color4fDataTypeId :
			return vectorToString( static_cast<const IECore::Color4fData *>( value )->readable() );
		case IECore::DateTimeDataTypeId :
		{
			const IECore::DateTimeData *d = static_cast<const IECore::DateTimeData *>( value );
			time_t t = ( d->readable() - from_time_t( 0 ) ).total_seconds();
			return QVariant( QDateTime::fromTime_t( t ) );
		}
		default :
		{
			// Fall back to using `str()` in python, to emulate old behaviour. If we find commonly
			// used types within large hierarchies falling through to here, we will need to give
			// them their own special case above, for improved performance.
			IECorePython::ScopedGILLock gilLock;
			object pythonValue( IECore::DataPtr( const_cast<IECore::Data *>( value ) ) );
			boost::python::str pythonString( pythonValue );
			return QVariant( boost::python::extract<const char *>( pythonString ) );
		}
	}
}

/// Equivalent to PathModel::CellData, but converted into the form needed by Qt.
struct CellVariants
{

	CellVariants( const GafferUI::PathColumn::CellData &cellData )
		:	m_display( dataToVariant( cellData.value.get(), Qt::DisplayRole ) ),
			m_decoration( dataToVariant( cellData.icon.get(), Qt::DecorationRole ) ),
			m_background( dataToVariant( cellData.background.get(), Qt::BackgroundRole ) ),
			m_toolTip( dataToVariant( cellData.toolTip.get(), Qt::ToolTipRole ) )
	{
	}

	CellVariants() = default;
	CellVariants( const CellVariants &other ) = default;
	CellVariants& operator=( const CellVariants &rhs ) = default;

	QVariant variant( int qtRole ) const
	{
		switch( qtRole )
		{
			case Qt::DisplayRole :
				return m_display;
			case Qt::DecorationRole :
				return m_decoration;
			case Qt::BackgroundRole :
				return m_background;
			case Qt::ToolTipRole :
				return m_toolTip;
			default :
				return QVariant();
		}
	}

	bool operator== ( const CellVariants &rhs ) const
	{
		return
			m_display == rhs.m_display &&
			m_decoration == rhs.m_decoration &&
			m_background == rhs.m_background &&
			m_toolTip == rhs.m_toolTip
		;
	}

	private :

		QVariant m_display;
		QVariant m_decoration;
		QVariant m_background;
		QVariant m_toolTip;

};

IECore::InternedString g_nameProperty( "name" );
IECore::InternedString g_childPlaceholder( "childPlaceholder" );

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
				m_headerDataState( State::Unrequested ),
				m_rootItem( new Item( IECore::InternedString(), nullptr ) ),
				m_flat( true ),
				m_sortColumn( -1 ),
				m_sortOrder( Qt::AscendingOrder ),
				m_modifyingTreeViewExpansion( false ),
				m_updateScheduled( false )
		{
			connect( parent, &QTreeView::expanded, this, &PathModel::treeViewExpanded );
			connect( parent, &QTreeView::collapsed, this, &PathModel::treeViewCollapsed );
			parent->installEventFilter( this );
			parent->setModel( this );
		}

		~PathModel() override
		{
			// Cancel update task before the things it relies on are destroyed.
			// No need to flush pending edits, because Qt won't deliver the events
			// to us after we're destructed anyway.
			cancelUpdate( /* flushPendingEdits = */ false );
		}

		// Selection is stored as a single `IECore::PathMatcher` per column, allowing
		// per-cell selections. An empty selection is represented by a vector of empty
		// `PathMatcher()` equal in size to the number of columns.
		using Selection = std::vector<IECore::PathMatcher>;

		///////////////////////////////////////////////////////////////////
		// Our public methods - these don't mean anything to Qt
		///////////////////////////////////////////////////////////////////

		void setColumns( const std::vector<GafferUI::PathColumnPtr> columns )
		{
			/// \todo Maintain persistent indices etc
			/// using `m_rootItem->update()`.

			// Cancel update and flush edit queue before we destroy
			// the items they reference.
			cancelUpdate();

			beginResetModel();

			m_columnChangedConnections.clear();

			// Keep track of selections that are common between the current and incoming columns
			Selection newSelection( columns.size(), IECore::PathMatcher() );
			for( size_t i = 0; i < columns.size(); ++i )
			{
				auto it = std::find( m_columns.begin(), m_columns.end(), columns[i] );
				if( it != m_columns.end() )
				{
					newSelection[i] = m_selection[ it - m_columns.begin() ];
				}
			}
			setSelection( newSelection );

			m_columns = columns;
			for( const auto &c : m_columns )
			{
				m_columnChangedConnections.push_back(
					c->changedSignal().connect( boost::bind( &PathModel::columnChanged, this ) )
				);
			}

			m_rootItem = new Item( IECore::InternedString(), nullptr );
			m_headerData.clear();
			m_headerDataState = State::Unrequested;

			endResetModel();
		}

		const std::vector<GafferUI::PathColumnPtr> &getColumns() const
		{
			return m_columns;
		}

		Path *getRoot()
		{
			return m_rootPath.get();
		}

		void setRoot( PathPtr root )
		{
			if( m_rootPath && m_rootPath->names() != root->names() )
			{
				// We're changing directory. Our current selection won't make sense
				// relative to the new directory, so we clear it.
				setSelection( Selection( getColumns().size(), IECore::PathMatcher() ) );
			}

			// Cancel update and flush edit queue before we dirty
			// the items they reference.
			cancelUpdate();
			m_rootPath = root;
			m_rootItem->dirty();
			m_recursiveExpansionPath.reset();
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
			m_recursiveExpansionPath.reset();
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
			m_recursiveExpansionPath.reset();
			m_rootItem->dirtyExpansion();
			expansionChanged();

			scheduleUpdate();
		}

		const IECore::PathMatcher &getExpansion() const
		{
			return m_expandedPaths;
		}

		// See comments for `setExpansion()`. The PathMatcher vector is our source of
		// truth, and we don't even use the QItemSelectionModel.
		void setSelection( const Selection &selectedPaths, bool scrollToFirst = true )
		{
			cancelUpdate();

			IECore::PathMatcher mergedPaths;
			for( auto &p : selectedPaths )
			{
				mergedPaths.addPaths( p );
			}

			if( scrollToFirst )
			{
				// Only scroll to previously unselected paths.
				m_scrollToCandidates = mergedPaths;
				m_scrollToCandidates->removePaths( m_selectedPaths );
			}
			else
			{
				m_scrollToCandidates.reset();
			}

			m_selectedPaths = mergedPaths;

			// Copy, so can't be modified without `setSelection()` call.
			m_selection = Selection( selectedPaths );

			if( m_scrollToCandidates )
			{
				m_rootItem->dirtyExpansion();
				scheduleUpdate();
			}

			selectionChanged();
		}

		const Selection &getSelection() const
		{
			return m_selection;
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

		Path::Names namesForIndex( const QModelIndex &index ) const
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

			indicesForPathsWalk( m_rootItem.get(), m_rootPath->names(), QModelIndex(), paths, result );
			return result;
		}

		void waitForPendingUpdates()
		{
			startUpdate( /* skipIfInvisible = */ false );
			if( m_updateTask )
			{
				m_updateTask->wait();
			}
			QCoreApplication::sendPostedEvents( this, EditEvent::staticType() );
		}

	signals :

		void expansionChanged();
		void selectionChanged();
		void updateFinished();

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

			if( role == Qt::UserRole )
			{
				// We use the user role for communicating the
				// selection state to the drawing code.
				const int c = index.column();
				if( (int)m_selection.size() > c )
				{
					return m_selection[c].match( namesForIndex( index ) );
				}
				return false;
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

			if( dirtyIfUnrequested( m_headerDataState ) )
			{
				const_cast<PathModel *>( this )->scheduleUpdate();
			}

			if( section < (int)m_headerData.size() )
			{
				return m_headerData[section].variant( role );
			}
			return QVariant();
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
				[this] () { startUpdate(); }
			);
			m_updateScheduled = true;
		}

		void startUpdate( bool skipIfInvisible = true )
		{
			if( !m_updateScheduled )
			{
				// We can get here if `waitForPendingUpdates()` starts the
				// update early, and the timer triggers afterwards. Or if
				// `waitForPendingUpdates()` is called when there are no
				// updates to do.
				return;
			}

			if( skipIfInvisible && !static_cast<QTreeView *>( QObject::parent() )->isVisible() )
			{
				// No point in performing an update if we're not visible.
				// Wait for `eventFilter()` to start the update in the next
				// `QShowEvent`.
				return;
			}

			// Cancel previous update and flush pending edits, as they
			// may delete or modify the items being visited by the
			// background task.
			cancelUpdate();

			// And then we can reschedule our update task.
			m_updateTask = ParallelAlgo::callOnBackgroundThread(
				getRoot()->cancellationSubject(),
				[this] {
					try
					{
						const IECore::Canceller *canceller = Context::current()->canceller();
						updateHeaderData( canceller );
						m_rootItem->update( this, canceller );
						queueEdit(
							[this] () {
								finaliseRecursiveExpansion();
								updateFinished();
							}
						);
					}
					catch( const IECore::Cancelled & )
					{
						// Cancellation could be due to several causes :
						//
						// - A graph edit that will lead to
						//   `Path::pathChangedSignal()` being emitted.
						// - A graph edit that won't lead to
						//   `Path::pathChangedSignal()` being emitted.
						// - A member of this class cancelling an update to make
						//   an edit and launch a new update.
						// - The QTreeView being hidden.
						//
						// In all cases we need to perform an update eventually,
						// and we can rely on `scheduleUpdate()` to deduplicate
						// multiple requests, and `startUpdate()` to defer
						// requests if we're hidden.
						queueEdit(
							[this] () { scheduleUpdate(); }
						);
					}
				}
			);
			m_updateScheduled = false;
		}

		// Cancels the current background update, optionally flushing the
		// queue of pending edits.
		void cancelUpdate( bool flushPendingEdits = true )
		{
			if( PyGILState_Check() )
			{
				// Resetting the update task implicitly calls `cancelAndWait()`.
				// If we hold the GIL, we need to release it first, in case the
				// Path class is Python-based and needs to acquire the GIL to
				// respond to cancellation.
				//
				// In our own bindings we would release the GIL at the
				// transition point from Python to C++, rather than in the guts
				// here. But several functions called by PySide bindings arrive
				// here, and PySide isn't releasing the GIL before calling into
				// C++. One such culprit is `QWidget.setParent()` being called
				// from Python and leading to `PathModel::eventFilter()` in C++.
				IECorePython::ScopedGILRelease gilRelease;
				m_updateTask.reset();
			}
			else
			{
				m_updateTask.reset();
			}

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

		bool eventFilter( QObject *object, QEvent *event ) override
		{
			// We are installed as an event filter on our QTreeView
			// so that we can react to it being shown and hidden.
			assert( object == QObject::parent() );

			switch( event->type() )
			{
				case QEvent::Show :
					// Do any updates that have been requested
					// while we were hidden.
					startUpdate();
					break;
				case QEvent::Hide :
					cancelUpdate();
					break;
				default :
					break;
			}

			return false;
		}

		void updateHeaderData( const IECore::Canceller *canceller )
		{
			if( m_headerDataState != State::Dirty )
			{
				return;
			}

			std::vector<CellVariants> newHeaderData;
			for( auto &column : m_columns )
			{
				newHeaderData.push_back( column->headerData( canceller ) );
			}

			if( m_headerData == newHeaderData )
			{
				m_headerDataState = State::Clean;
				return;
			}

			queueEdit(

				[this, newHeaderData = std::move( newHeaderData )] () mutable {

					m_headerData.swap( newHeaderData );
					m_headerDataState = State::Clean;
					headerDataChanged( Qt::Horizontal, 0, m_headerData.size() - 1 );

				}

			);
		}

		// State transitions :
		//
		// - Unrequested->Dirty : When first queried.
		// - Dirty->Clean : When updated.
		// - Clean->Dirty : When path changes.
		enum class State
		{
			// Initial state. Not yet requested by clients
			// of the model, therefore not yet computed, and not
			// in need of consideration during recursive updates.
			Unrequested,
			// Computed and up to date.
			Clean,
			// Stale data that needs recomputing.
			Dirty
		};

		static bool dirtyIfUnrequested( std::atomic<State> &state )
		{
			State unrequested = State::Unrequested;
			return state.compare_exchange_strong( unrequested, State::Dirty );
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

			void dirty( bool dirtyChildItems = true, bool dirtyData = true )
			{
				// This is just intended to be called on the root item by the
				// PathModel when the path changes.
				assert( !m_parent );
				dirtyWalk( dirtyChildItems, dirtyData );
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

			void update( PathModel *model, const IECore::Canceller *canceller )
			{
				// We take a copy of `expandedPaths` because it may be modified
				// on the UI thread by `treeViewExpanded()` while we run in the
				// background.
				PathPtr workingPath = model->m_rootPath->copy();
				updateWalk( model, workingPath.get(), IECore::PathMatcher( model->m_expandedPaths ), canceller );
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
				if( dirtyIfUnrequested( m_dataState ) )
				{
					const_cast<PathModel *>( model )->scheduleUpdate();
				}

				if( column >= (int)m_data.size() )
				{
					// We haven't computed any data yet.
					if( column < (int)model->m_columns.size() && role == Qt::DisplayRole )
					{
						if( auto *standardColumn = dynamic_cast<const GafferUI::StandardPathColumn *>( model->m_columns[column].get() ) )
						{
							if( standardColumn->property() == g_nameProperty )
							{
								// Optimisation for standard name column. We
								// know the name already, so there is no need to
								// wait for the data to be computed. This
								// reduces flicker when scrolling rapidly
								// through many items, making it easier to
								// orientate yourself.
								return m_name.c_str();
							}
						}
					}
					return QVariant();
				}

				return m_data[column].variant( role );
			}

			using ChildContainer = std::vector<Ptr>;

			ChildContainer &childItems( const PathModel *model )
			{
				if( dirtyIfUnrequested( m_childItemsState ) )
				{
					const_cast<PathModel *>( model )->scheduleUpdate();
				}
				return *m_childItems;
			}

			private :

				void dirtyWalk( bool dirtyChildItems, bool dirtyData )
				{
					if( dirtyData && ( m_dataState == State::Clean ) )
					{
						m_dataState = State::Dirty;
					}
					if( dirtyChildItems && ( m_childItemsState == State::Clean ) )
					{
						m_childItemsState = State::Dirty;
					}
					for( const auto &child : *m_childItems )
					{
						child->dirtyWalk( dirtyChildItems, dirtyData );
					}
				}

				void updateWalk( PathModel *model, Path *path, const IECore::PathMatcher &expandedPaths, const IECore::Canceller *canceller )
				{
					IECore::Canceller::check( canceller );
					updateData( model, path, canceller );
					updateExpansion( model, path, expandedPaths );
					std::shared_ptr<ChildContainer> updatedChildItems = updateChildItems( model, path, canceller );

					const size_t pathSize = path->names().size();
					Path::Names childName( 1 );

					/// \todo We could consider using `parallel_for()` here for improved
					/// performance. But given all the other modules vying for processor time
					/// (the Viewer and Renderer in particular), perhaps limiting ourselves to
					/// a single core is reasonable. If we do use `parallel_for` we need to
					/// consider the interaction with `m_scrollToCandidates` because the order
					/// we visit children in would no longer be deterministic.
					for( const auto &child : *updatedChildItems )
					{
						// Append child name to path, bearing in mind that recursion
						// in `updateWalk()` may have left us with a longer path than
						// we had before.
						childName.back() = child->name();
						path->set( pathSize, path->names().size(), childName );
						child->updateWalk( model, path, expandedPaths, canceller );
					}
				}

				static QVariant dataForSort( const std::vector<CellVariants> &data, PathModel *model )
				{
					if( model->m_sortColumn < 0 || model->m_sortColumn >= (int)data.size() )
					{
						return QVariant();
					}
					return data[model->m_sortColumn].variant( Qt::DisplayRole );
				}

				// Updates data and returns the value that should be used for sorting.
				// This value is returned because the actual edit to `m_data` will not be
				// complete until the queued edit is processed by the UI thread.
				QVariant updateData( PathModel *model, const Path *path, const IECore::Canceller *canceller )
				{
					if( m_dataState == State::Clean || m_dataState == State::Unrequested )
					{
						return dataForSort( m_data, model );
					}

					// We generate data for all columns and roles at once, on the
					// assumption that access to one is likely to indicate upcoming
					// accesses to the others.

					std::vector<CellVariants> newData;

					newData.reserve( model->m_columns.size() );

					for( int i = 0, e = model->m_columns.size(); i < e; ++i )
					{
						CellVariants cellVariants;
						try
						{
							cellVariants = CellVariants( model->m_columns[i]->cellData( *path, canceller ) );
						}
						catch( const IECore::Cancelled & )
						{
							throw;
						}
						catch( const std::exception &e )
						{
							// Qt doesn't use exceptions for error handling,
							// so we must suppress them.
							cellVariants = CellVariants(
								GafferUI::PathColumn::CellData(
									nullptr,  // value
									new IECore::StringData( "errorSmall.png" ),  // icon
									nullptr,  // background
									new IECore::StringData( e.what() )  // toolTip
								)
							);
						}
						catch( ... )
						{
							IECore::msg( IECore::Msg::Warning, "PathListingWidget", "Unknown error" );
						}

						newData.push_back( cellVariants );
					}

					if( newData == m_data )
					{
						// No update necessary.
						m_dataState = State::Clean;
						return dataForSort( m_data, model );
					}

					if( m_row == -1 )
					{
						// We have just been created in `updateChildItems()` and haven't
						// been made visible to Qt yet. No need to emit `dataChanged` or
						// worry about concurrent access from the UI thread.
						m_data.swap( newData );
						m_dataState = State::Clean;
						return dataForSort( m_data, model );
					}

					// Mark clean _now_, to avoid a double update if we are
					// called from our parent's `updateChildItems()` (to obtain
					// data for sorting) and then called again from
					// `updateWalk()` before the queued edit is applied.
					m_dataState = State::Clean;

					// Get result before we move `newDisplayData` into the lambda.
					const QVariant result = dataForSort( newData, model );

					model->queueEdit(

						[this, model, newData = std::move( newData )] () mutable {

							m_data.swap( newData );
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

					// Handle expanded paths and recursive expansion.

					unsigned match = expandedPaths.match( path->names() );
					bool expanded = match & IECore::PathMatcher::ExactMatch;

					if( model->m_recursiveExpansionPath )
					{
						if( boost::starts_with( path->names(), *model->m_recursiveExpansionPath ) )
						{
							match |= IECore::PathMatcher::DescendantMatch;
							expanded = true;
						}
					}

					if( expanded )
					{
						// The QTreeView is inevitably going to query the
						// children after we call `treeView->setExpanded()`.
						// Get ahead of the game by creating them during this
						// update.
						dirtyIfUnrequested( m_childItemsState );
					}

					if( expanded != m_expandedInTreeView )
					{
						model->queueEdit(
							[this, model, expanded] {
								QTreeView *treeView = dynamic_cast<QTreeView *>( model->QObject::parent() );
								Private::ScopedAssignment<bool> assignment( model->m_modifyingTreeViewExpansion, true );
								treeView->setExpanded( model->createIndex( m_row, 0, this ), expanded );
							}
						);
					}

					// Handle expansion for selection updates.

					if( model->m_scrollToCandidates )
					{
						const unsigned scrollToMatch = model->m_scrollToCandidates->match( path->names() );
						if( scrollToMatch & IECore::PathMatcher::ExactMatch )
						{
							model->queueEdit(
								[this, model] {
									QTreeView *treeView = dynamic_cast<QTreeView *>( model->QObject::parent() );
									const QModelIndex index = model->createIndex( m_row, 0, this );
									treeView->scrollTo( index, QTreeView::EnsureVisible );
									treeView->selectionModel()->setCurrentIndex( index, QItemSelectionModel::Current );
								}
							);
							// OK to modify from background thread, because only use on UI thread
							// is preceded by call to `cancelUpdate()`.
							model->m_scrollToCandidates.reset();
						}

						if( scrollToMatch & IECore::PathMatcher::DescendantMatch )
						{
							// Force creation of children so we can scroll to them.
							dirtyIfUnrequested( m_childItemsState );
						}
					}

					m_expansionDirty = false;
				}

				// Returns the updated ChildContainer. This will not be visible in the model
				// until the queued edit is executed. It is returned so that we can update
				// the not-yet-visible children in `updateWalk()`.
				std::shared_ptr<ChildContainer> updateChildItems( PathModel *model, const Gaffer::Path *path, const IECore::Canceller *canceller )
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
						path->children( children, canceller );
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
						bool sortingByName = false;
						if( auto *standardColumn = dynamic_cast<const GafferUI::StandardPathColumn *>( model->m_columns[model->m_sortColumn].get() ) )
						{
							if( standardColumn->property() == g_nameProperty )
							{
								sortingByName = true;
								for( const auto &childItem : newChildItems )
								{
									// Optimisation for standard name column. We
									// know the name already, so there is no need to
									// wait for the data to be computed. This reduces
									// delay when displaying items sorted by name.
									sortedIndices.push_back( SortablePair(
										childItem->name().c_str(),
										sortedIndices.size()
									) );
								}
							}
						}

						if( !sortingByName )
						{
							for( const auto &childItem : newChildItems )
							{
								dirtyIfUnrequested( childItem->m_dataState );
								sortedIndices.push_back( SortablePair(
									childItem->updateData( model, children[sortedIndices.size()].get(), canceller ),
									sortedIndices.size()
								) );
							}
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

				std::atomic<State> m_dataState;
				std::vector<CellVariants> m_data;

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
			// Store the expansion state in the Item, so that it can be looked
			// up in a thread-safe way in `Item::updateExpansion(). We do this
			// no matter the source of the change to the tree view, so that the
			// Item has an exact mirror of the tree view state.
			static_cast<Item *>( index.internalPointer() )->treeViewExpansionChanged( true );

			if( m_modifyingTreeViewExpansion )
			{
				// We're modifying the expansion ourselves, to mirror
				// `m_expandedPaths` into the tree view. In this case there is
				// no need to sync back into `m_expandedPaths`.
				return;
			}

			// The user has modified the expansion interactively. We need to
			// reflect this back into `m_expandedPaths` and report it via
			// `expansionChanged()`.

			const Path::Names expandedPath = namesForIndex( index );
			// It's possible for `addPath()` to return false if the path is
			// already added, but the async update hasn't transferred it to
			// the QTreeView yet (allowing a user to expand it manually in
			// the meantime).
			if( m_expandedPaths.addPath( expandedPath ) )
			{
				expansionChanged();
			}

			if( QGuiApplication::keyboardModifiers() & Qt::ShiftModifier )
			{
				// Recursively expand everything below this index. This
				// could be expensive, so we do it during the async update.
				cancelUpdate();
				m_recursiveExpansionPath = expandedPath;
				static_cast<Item *>( index.internalPointer() )->dirtyExpansion();
				scheduleUpdate();
			}
		}

		void finaliseRecursiveExpansion()
		{
			if( !m_recursiveExpansionPath )
			{
				return;
			}
			// We've expanded a bunch of paths on the Qt side, and now
			// we need to reflect that in `m_expandedPaths`.
			QModelIndex index = indexForPath( *m_recursiveExpansionPath );
			assert( index.isValid() );
			m_expandedPaths.addPath( *m_recursiveExpansionPath );
			m_expandedPaths.addPaths( descendantPaths( static_cast<Item *>( index.internalPointer() ) ), *m_recursiveExpansionPath );
			m_recursiveExpansionPath.reset();
			expansionChanged();
		}

		IECore::PathMatcher descendantPaths( Item *item )
		{
			IECore::PathMatcher result;
			for( const auto &child : item->childItems( this ) )
			{
				std::vector<IECore::InternedString> childPath( { child->name() } );
				result.addPath( childPath );
				result.addPaths( descendantPaths( child.get() ), childPath );
			}
			return result;
		}

		void treeViewCollapsed( const QModelIndex &index )
		{
			static_cast<Item *>( index.internalPointer() )->treeViewExpansionChanged( false );
			if( m_modifyingTreeViewExpansion )
			{
				return;
			}

			const Path::Names collapsedPath = namesForIndex( index );
			bool expandedPathsChanged = m_expandedPaths.removePath( collapsedPath );

			if( m_recursiveExpansionPath && boost::starts_with( *m_recursiveExpansionPath, collapsedPath ) )
			{
				// Abort recursive expansion because a parent path has been
				// collapsed.
				cancelUpdate();
				m_recursiveExpansionPath.reset();
				scheduleUpdate();
			}

			if( QGuiApplication::keyboardModifiers() & Qt::ShiftModifier )
			{
				// Recursively collapse everything below this index.
				expandedPathsChanged |= m_expandedPaths.prune( collapsedPath );
				Private::ScopedAssignment<bool> assignment( m_modifyingTreeViewExpansion, true );
				collapseDescendants( static_cast<QTreeView *>( QObject::parent() ), index );
			}

			if( expandedPathsChanged )
			{
				expansionChanged();
			}
		}

		void collapseDescendants( QTreeView *treeView, const QModelIndex &index )
		{
			for( int i = 0, e = rowCount( index ); i < e; ++i )
			{
				const QModelIndex childIndex = this->index( i, 0, index );
				treeView->setExpanded( childIndex, false );
				collapseDescendants( treeView, childIndex );
			}
		}

		// Column change handling

		void columnChanged()
		{
			cancelUpdate();
			m_rootItem->dirty( /* dirtyChildItems = */ false, /* dirtyData = */ true );
			if( m_headerDataState == State::Clean )
			{
				m_headerDataState = State::Dirty;
			}
			scheduleUpdate();
		}

		// Member data

		Gaffer::PathPtr m_rootPath;

		std::vector<CellVariants> m_headerData;
		mutable std::atomic<State> m_headerDataState;
		Item::Ptr m_rootItem;
		bool m_flat;
		std::vector<GafferUI::PathColumnPtr> m_columns;
		std::vector<Gaffer::Signals::ScopedConnection> m_columnChangedConnections;
		int m_sortColumn;
		Qt::SortOrder m_sortOrder;
		std::unique_ptr<QAbstractItemModelTester> m_tester;

		IECore::PathMatcher m_expandedPaths;
		bool m_modifyingTreeViewExpansion;
		std::optional<Path::Names> m_recursiveExpansionPath;

		// A vector of `IECore::PathMatcher` objects, one for each column
		Selection m_selection;
		// All of the `PathMatchers` from `m_selection` merged into one
		// to avoid merging every time paths are expanded.
		IECore::PathMatcher m_selectedPaths;
		// Parameters used to control expansion update following call to
		// `setSelection()`.
		std::optional<IECore::PathMatcher> m_scrollToCandidates;

		std::unique_ptr<Gaffer::BackgroundTask> m_updateTask;
		bool m_updateScheduled;

};

class PathListingWidgetItemDelegate : public QStyledItemDelegate
{

	public :

		PathListingWidgetItemDelegate( QObject *parent = nullptr )
			:	QStyledItemDelegate( parent )
		{
		}

		using DisplayTransform = std::function<Imath::Color3f ( const Imath::Color3f & )>;
		DisplayTransform displayTransform;

	protected :

		void initStyleOption( QStyleOptionViewItem *option, const QModelIndex &index ) const override
		{
			QStyledItemDelegate::initStyleOption( option, index );

			if( displayTransform )
			{
				const QVariant decoration = index.data( Qt::DecorationRole );
				if( decoration.userType() == QMetaType::QColor )
				{
					// Apply display transform to the colour.
					const QColor qc = qvariant_cast<QColor>( decoration );
					const Imath::Color3f c = displayTransform(
						Imath::Color3f( qc.redF(), qc.greenF(), qc. blueF() )
					);
					// Update `option`. Making a QPixmap for this seems wasteful,
					// but that's what the QStyledItemDelegate does.
					QPixmap pixmap( option->decorationSize );
					pixmap.fill( QColor::fromRgbF( c[0], c[1], c[2] ) );
					option->icon = QIcon( pixmap );
				}
			}

			if( option->state & QStyle::State_MouseOver )
			{
				// Ideally the QStyle would automatically use `State_MouseOver`
				// to draw the `QIcon::Active` version of an icon. But it
				// doesn't do that. So instead, we switch in the active version
				// of the icon here, before it gets passed to the style for
				// drawing.
				option->icon = QIcon( option->icon.pixmap( option->decorationSize, QIcon::Active ) );
			}
		}

};

void setColumns( uint64_t treeViewAddress, object pythonColumns )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	std::vector<GafferUI::PathColumnPtr> columns;
	boost::python::container_utils::extend_container( columns, pythonColumns );
	IECorePython::ScopedGILRelease gilRelease;
	model->setColumns( columns );
}

list getColumns( uint64_t treeViewAddress )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	list result;
	for( const auto &column : model->getColumns() )
	{
		result.append( column );
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
	}
	model->setRoot( path );
}

void updateDelegate( uint64_t treeViewAddress, boost::python::object pythonDisplayTransform )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	auto *delegate = dynamic_cast<PathListingWidgetItemDelegate *>( treeView->itemDelegate() );
	if( !delegate )
	{
		delegate = new PathListingWidgetItemDelegate( treeView );
		treeView->setItemDelegate( delegate );
	}

	PathListingWidgetItemDelegate::DisplayTransform displayTransform;
	if( pythonDisplayTransform )
	{
		// The lambda below needs to own a reference to `pythonDisplayTransform`,
		// and in turn will be owned by the PathListingWidgetItemDelegate C++ object.
		// Wrap `pythonDisplayTransform` so we acquire the GIL when the lambda is
		// destroyed from C++.
		auto pythonDisplayTransformPtr = std::shared_ptr<boost::python::object>(
			new boost::python::object( pythonDisplayTransform ),
			[]( boost::python::object *o ) {
				IECorePython::ScopedGILLock gilLock;
				delete o;
			}
		);

		delegate->displayTransform = [pythonDisplayTransformPtr] ( const Imath::Color3f &color ) -> Imath::Color3f {
			IECorePython::ScopedGILLock gilLock;
			try
			{
				return extract<Imath::Color3f>( (*pythonDisplayTransformPtr)( color ) );
			}
			catch( const boost::python::error_already_set & )
			{
				return color;
			}
		};
	}
	else
	{
		delegate->displayTransform = nullptr;
	}

	treeView->update();
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

void setSelection( uint64_t treeViewAddress, object pythonPaths, bool scrollToFirst )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );

	PathModel::Selection paths;
	boost::python::container_utils::extend_container( paths, pythonPaths );

	IECorePython::ScopedGILRelease gilRelease;
	model->setSelection( paths, scrollToFirst );
}

list getSelection( uint64_t treeViewAddress )
{
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );

	list result;

	for( auto &p : model->getSelection() )
	{
		result.append( p );
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

IECore::PathMatcher pathsForIndexRange( uint64_t treeViewAddress, uint64_t index0Address, uint64_t index1Address )
{
	IECorePython::ScopedGILRelease r;
	QTreeView *treeView = reinterpret_cast<QTreeView *>( treeViewAddress );
	PathModel *model = dynamic_cast<PathModel *>( treeView->model() );
	assert( model );
	QModelIndex index0 = *reinterpret_cast<QModelIndex *>( index0Address );
	QModelIndex index1 = *reinterpret_cast<QModelIndex *>( index1Address );

	const int y0 = treeView->visualRect( index0 ).y();
	const int y1 = treeView->visualRect( index1 ).y();
	if( y0 > y1 )
	{
		std::swap( index0, index1 );
	}

	IECore::PathMatcher result;
	// Range is inclusive, so always includes index0 and index1, even
	// if they are equal.
	while( index0.isValid() ) {
		result.addPath( model->namesForIndex( index0 ) );
		if( index0.internalPointer() == index1.internalPointer() )
		{
			break;
		}
		index0 = treeView->indexBelow( index0 );
	}

	return result;
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
	def( "_pathListingWidgetUpdateDelegate", &updateDelegate );
	def( "_pathListingWidgetSetFlat", &setFlat );
	def( "_pathListingWidgetGetFlat", &getFlat );
	def( "_pathListingWidgetSetExpansion", &setExpansion );
	def( "_pathListingWidgetGetExpansion", &getExpansion );
	def( "_pathListingWidgetSetSelection", &setSelection );
	def( "_pathListingWidgetGetSelection", &getSelection );
	def( "_pathListingWidgetPathForIndex", &pathForIndex );
	def( "_pathListingWidgetIndexForPath", &indexForPath );
	def( "_pathListingWidgetPathsForIndexRange", &pathsForIndexRange );
	def( "_pathListingWidgetPathsForPathMatcher", &pathsForPathMatcher );
	def( "_pathListingWidgetAttachTester", &attachTester );
	def( "_pathListingWidgetAncestorPaths", &ancestorPaths );
	def( "_pathModelWaitForPendingUpdates", &waitForPendingUpdates );
}

#include "PathListingWidgetBinding.moc"
