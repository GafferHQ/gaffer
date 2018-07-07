# Tutorial: Creating a Configuration File #

Gaffer supports scripting configuration files that load when the application starts up. These files have access to the Gaffer API, allowing application customization and extension. In this brief tutorial, we will demonstrate:

- Creating a trivia startup file
- Creating a file that could be useful in a studio environment


## Trivia Script ##

We will start with a tiny script that delivers number trivia to the terminal. The script will go in `~gaffer/gui`, which is where startup scripts main gaffer application should reside.

1. Create a new file `dateTrivia.py` in `~/gaffer/startup/gui/`.

2. Write the following to `dateTrivia.py`:

    ```python
    import urllib2
    import datetime
    day = datetime.date.today()
    factInfoURL = urllib2.urlopen( "http://numbersapi.com/%d/%d/date?json" % ( day.month, day.day ) )
    factURL = urllib2.urlopen( "http://numbersapi.com/%d/%d/date" % ( day.month, day.day ) )
    print "\n" + "".join( factURL.readlines() )
    ```

3. Save the file.

When you next run Gaffer, the terminal will print an edifying fact about today's calendar date in history.

```bash
user@desktop /opt/gaffer-!GAFFER_VERSION!-linux/bin $ ./gaffer
July 13th is the day in 1919 that the British airship R34 lands in Norfolk, England, completing the first airship return journey across the Atlantic in 182 hours of flight.
```


## Studio Bookmark Script ##

All of Gaffer's file browsers support user-defined bookmarks to help users in their day-to-day navigation. In addition to users creating their own bookmarks via the UI, you can also create bookmarks via Gaffer's configuration files, making it very easy to create standard bookmarks for shared use across a facility. The following example code demonstrates how you might provide do so using a fictional `MyJobEnvironment` module.

Write the following to a new file `dateTrivia.py` in `~/gaffer/startup/gui/`:

```python
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


## See Also ##

- [Tutorial: Adding a Menu Item](../AddingAMenuItem/index.md)
- [Gaffer's Default Configuration Files](https://github.com/GafferHQ/gaffer/tree/!GAFFER_VERSION!/startup/gui)

<!-- - [Configuration Files](../ConfigurationFiles/index.md) -->
