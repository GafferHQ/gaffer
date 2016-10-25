Creating Configuration Files
============================

Introduction
------------

Gaffer applications are intended to be easily extensible and customisable, and to this end provide many scripting hooks for registering new behaviours and customising the user interface. At application startup, a series of configuration files are executed, providing an opportunity for the intrepid TD to make his or her mark.

Startup file locations
----------------------

The location of Gaffer’s configuration files are specified using the `GAFFER_STARTUP_PATHS` environment variable. This is a colon separated list of paths to directories where the startup files reside. Config directories at the end of the list are executed first, allowing them to be overridden by config directories earlier in the list.

Gaffer automatically adds the `~/gaffer/startup` config directory to the `GAFFER_STARTUP_PATHS` to allow users to create their own config files without having to faff around with the environment. This user level config is run last, allowing it to take precedence over all other configuration files.

Within a startup directory, config files are stored in subdirectories by application name - each application only executes the files in the appropriate directory. So for instance, the browser app executes files from the `~/gaffer/startup/browser` directory.

Creating a simple startup file
------------------------------

We can add a startup script for the main gaffer application by creating a file in the "gui" subdirectory of the user startup location :

`~/gaffer/startup/gui/startupTest.py`


For now, let’s just create a really simple script to provide a nice little distraction from work.

```
import urllib2
import datetime
day = datetime.date.today()
factInfoURL = urllib2.urlopen( "http://numbersapi.com/%d/%d/date?json" % ( day.month, day.day ) )
factURL = urllib2.urlopen( "http://numbersapi.com/%d/%d/date" % ( day.month, day.day ) )
print "".join( factURL.readlines() )
```

Hopefully now when we run gaffer, we’ll receive an edifying fact, and know that the config mechanism is working as expected.

```
>gaffer
July 13th is the day in 1919 that the British airship R34 lands in Norfolk, England,
completing the first airship return journey across the Atlantic in 182 hours of flight.
```

A more useful example
---------------------

Gaffer's file browsers all support user-defined bookmarks to help users in their day-to-day navigation. In addition to users creating their own bookmarks via the UI, you can also create bookmarks via Gaffer's configuration files, making it very easy to create standard bookmarks for shared use across a facility. The following example code demonstrates how we might do so using a fictional `MyJobEnvironment` module to provide facility specific information.

```
import GafferUI
import MyJobEnvironment

# Bookmarks are associated with an application, so we must first acquire the right set
# of bookmarks for this particular application.
bookmarks = GafferUI.Bookmarks.acquire( application )

# Now we can go about adding some bookmarks for our current job, sequence and shot,
# assuming we have a handy custom module for getting them.
bookmarks.add( "Job", MyJobEnvironment.currentJobPath() )
bookmarks.add( "Sequence", MyJobEnvironment.currentSequencePath() )
bookmarks.add( "Shot", MyJobEnvironment.currentShotPath() )

# We might want some bookmarks to only appear in certain contexts related to the
# sort of file we're interested in. These are stored in a category-specific set
# of bookmarks which we must acquire on its own.
bookmarks = GafferUI.Bookmarks.acquire( application, category="image" )
bookmarks.add( "Output", MyJobEnvironment.currentShotPath() + "/outputImages" )
bookmarks.add( "Input", MyJobEnvironment.currentShotPath() + "/inputImages" )

# We can also define default locations to be used as the starting point for
# file browsers when the path being edited is empty.
bookmarks = GafferUI.Bookmarks.acquire( application, category="plateImport" )
bookmarks.setDefault( MyJobEnvironment.currentJobPath() + "/fromClient/plates" )
```

Next steps
----------

Naturally, we might want to do something slightly more useful at startup. Taking a look at [Gaffer’s internal config
files][1] might provide some good starting points for more useful customisations.

[1]: https://github.com/GafferHQ/gaffer/tree/!GAFFER_VERSION!/startup/gui
