import IECore
import Gaffer
import GafferUI
import IECore
import gtk

## \todo Rejig this to remove all gtk specific code, and use only GafferUI classes instead

def callback( t ) :

	print t

definition = IECore.MenuDefinition(

	[
		( "/apple/pear/banana", { "command" : lambda : callback( "banana" ) } ),
		( "/apple/pear/divider", { "divider" : True } ),
		( "/apple/pear/submarine", { } ),
		( "/dog/inactive", { "active" : False } ),
	]
	
)

menu = GafferUI.Menu( definition )
menuBar = GafferUI.MenuBar( definition )

window = gtk.Window( gtk.WINDOW_TOPLEVEL )
window.set_size_request( 200, 100 )
window.set_title( "Menu test" )
window.connect( "delete_event", gtk.main_quit )
vbox = gtk.VBox()
button = gtk.Button( "button" )
vbox.add( menuBar.gtkWidget() )
vbox.add( button )
window.add( vbox )
button.show()

## \todo Use one of the methods below to apply
# a nice high end grey style to all widgets
# this works!
#c = gtk.gdk.Color()
#window.modify_bg( gtk.STATE_NORMAL, c )
#window.modify_fg( gtk.STATE_NORMAL, c )
#button.modify_bg( gtk.STATE_NORMAL, c )
#button.modify_fg( gtk.STATE_NORMAL, c )

# this works too!
#s = gtk.Style()
#c = gtk.gdk.Color()
#s.fg[gtk.STATE_NORMAL] = c
#s.bg[gtk.STATE_NORMAL] = c
#window.set_style( s )
#button.set_style( s )

# and this works!
#s = button.get_style()
#c = gtk.gdk.Color()
#s.fg[gtk.STATE_NORMAL] = c
#s.bg[gtk.STATE_NORMAL] = c
#button.set_style( s )

def popup( widget, event, menu ) :
		
	menu.popup()

button.connect( "button-press-event", popup, menu )

window.show_all()

GafferUI.EventLoop.start()
