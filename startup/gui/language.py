##########################################################################
#
#  Language preferences for i18n.
#
#  Adds a "Language" section to Preferences with:
#    - UI language dropdown (English / Español)
#    - "Use translated node names" checkbox
#    - "Use translated tooltips" checkbox
#
#  The effective language is persisted in ~/gaffer/i18n.json and read
#  by GafferUI.i18n at import time (before the Preferences node exists).
#  Changing the language requires a restart.
#
##########################################################################

import functools

import Gaffer
import GafferUI
from GafferUI.i18n import _
from GafferUI import i18n as _i18n

# ---------------------------------------------------------------------------
# Register preference plugs
# ---------------------------------------------------------------------------

preferences = application.root()["preferences"]

preferences["language"] = Gaffer.Plug()

preferences["language"]["uiLanguage"] = Gaffer.StringPlug(
	defaultValue = "en"
)
preferences["language"]["translateNodeNames"] = Gaffer.BoolPlug(
	defaultValue = True
)
preferences["language"]["translateTooltips"] = Gaffer.BoolPlug(
	defaultValue = True
)

# Set current values from the i18n config that was already loaded
preferences["language"]["uiLanguage"].setValue( _i18n.language() )
preferences["language"]["translateNodeNames"].setValue( _i18n.translateNodeNames() )
preferences["language"]["translateTooltips"].setValue( _i18n.translateTooltips() )

# ---------------------------------------------------------------------------
# Metadata – layout section and widget types
# ---------------------------------------------------------------------------

Gaffer.Metadata.registerValue(
	preferences["language"], "plugValueWidget:type",
	"GafferUI.LayoutPlugValueWidget", persistent = False
)
Gaffer.Metadata.registerValue(
	preferences["language"], "layout:section",
	_( "Language" ), persistent = False
)

# UI language dropdown via presets
Gaffer.Metadata.registerValue(
	preferences["language"]["uiLanguage"], "plugValueWidget:type",
	"GafferUI.PresetsPlugValueWidget", persistent = False
)
Gaffer.Metadata.registerValue(
	preferences["language"]["uiLanguage"], "label",
	"UI Language", persistent = False
)
Gaffer.Metadata.registerValue(
	preferences["language"]["uiLanguage"], "preset:English (en)", "en",
	persistent = False
)
Gaffer.Metadata.registerValue(
	preferences["language"]["uiLanguage"], "preset:Español (es)", "es",
	persistent = False
)

Gaffer.Metadata.registerValue(
	preferences["language"]["translateNodeNames"], "label",
	"Use Translated Node Names", persistent = False
)
Gaffer.Metadata.registerValue(
	preferences["language"]["translateTooltips"], "label",
	"Use Translated Tooltips", persistent = False
)

# ---------------------------------------------------------------------------
# Save hook – persist to i18n.json alongside normal preferences
# ---------------------------------------------------------------------------

__initialising = True

def __languagePlugDirtied( plug ) :

	global __initialising
	if __initialising :
		return

	if plug.parent() != preferences["language"] :
		return
	if plug.getName() not in ( "uiLanguage", "translateNodeNames", "translateTooltips" ) :
		return

	lang = preferences["language"]["uiLanguage"].getValue()
	nodeNames = preferences["language"]["translateNodeNames"].getValue()
	tooltips = preferences["language"]["translateTooltips"].getValue()

	_i18n.saveConf( lang, nodeNames, tooltips )

	# Show restart dialog when the language itself changes
	if plug.getName() == "uiLanguage" and lang != _i18n.language() :
		scriptWindow = GafferUI.ScriptWindow.acquire( application.root()["scripts"].children()[0] ) if len( application.root()["scripts"].children() ) else None
		dialogue = GafferUI.Dialogue( _( "Language Changed" ) )
		dialogue._setWidget(
			GafferUI.Label(
				_( "The language change will take effect after restarting Gaffer." )
			)
		)
		closeButton = dialogue._addButton( _( "OK" ) )
		closeButton.clickedSignal().connect(
			lambda button : button.ancestor( GafferUI.Window ).setVisible( False )
		)
		if scriptWindow is not None :
			scriptWindow.addChildWindow( dialogue )
		dialogue.setVisible( True )

preferences.plugDirtiedSignal().connect(
	__languagePlugDirtied
)

__initialising = False

# ---------------------------------------------------------------------------
# Translate nodule (port) labels on graph node gadgets
# ---------------------------------------------------------------------------
# NoduleLayout (C++) reads "noduleLayout:label" metadata at construction time.
# We register a callable for EVERY specific plug type so the translated label
# is returned when NoduleLayout first queries metadata during gadget creation.

if _i18n.translateNodeNames() :

	import IECore

	def __translatedNoduleLabel( plug ) :
		return _i18n.translateLabel( IECore.CamelCase.toSpaced( plug.getName() ) )

	# Register for all concrete Gaffer plug types
	__plugTypes = [
		Gaffer.Plug,
		Gaffer.ValuePlug,
		Gaffer.BoolPlug,
		Gaffer.IntPlug,
		Gaffer.FloatPlug,
		Gaffer.StringPlug,
		Gaffer.V2fPlug,
		Gaffer.V2iPlug,
		Gaffer.V3fPlug,
		Gaffer.V3iPlug,
		Gaffer.Color3fPlug,
		Gaffer.Color4fPlug,
		Gaffer.Box2fPlug,
		Gaffer.Box2iPlug,
		Gaffer.Box3fPlug,
		Gaffer.Box3iPlug,
		Gaffer.M44fPlug,
		Gaffer.SplinefColor3fPlug,
		Gaffer.SplinefColor4fPlug,
		Gaffer.SplineffPlug,
		Gaffer.CompoundDataPlug,
		Gaffer.CompoundObjectPlug,
	]

	# Also register for scene/image/dispatch plug types if available
	for __modName in ( "GafferScene", "GafferImage", "GafferDispatch" ) :
		try :
			__mod = __import__( __modName )
			for __attr in dir( __mod ) :
				__obj = getattr( __mod, __attr, None )
				if isinstance( __obj, type ) and issubclass( __obj, Gaffer.Plug ) :
					__plugTypes.append( __obj )
		except ImportError :
			pass

	__registered = 0
	__errors = []
	for __plugType in __plugTypes :
		try :
			Gaffer.Metadata.registerValue(
				__plugType.staticTypeId(), "noduleLayout:label", __translatedNoduleLabel
			)
			__registered += 1
		except Exception as __e :
			__errors.append( "%s: %s" % ( __plugType.__name__, __e ) )
