import IECore
import Gaffer
import GafferUI
import IECore
import gtk

## \todo Rejig this to remove all gtk specific code, and use only GafferUI classes instead

window = GafferUI.Window( title="Script editor test" )

window.gtkWidget().connect( "delete_event", gtk.main_quit )

s = GafferUI.ScriptEditor( Gaffer.ScriptNode() )
window.setChild( s )

window.show()

GafferUI.EventLoop.start()
