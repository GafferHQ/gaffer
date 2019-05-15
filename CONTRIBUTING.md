# Contributing #

The Gaffer team always welcomes quality contributions and issue reports. The following guidelines exist to maintain a consistent quality for the project's history, and facilitate the code adoption and correction processes. The goal is for everyone to assist our project maintainers by delivering the necessary information for them to make informed decisions and reduce as much confusion and guesswork as possible. Adhering to these guidelines will also benefit you, as it will reduce the time it takes for your contribution to be merged or your issue to be resolved.

Feel free to join the discussion on the [Gaffer community group](https://groups.google.com/forum/#!forum/gaffer-dev). It is the main public space for Gaffer-related questions, issues, and requests. If you are new to Gaffer development, we recommend browsing the latest discussions to develop a sense for the current priorities and familiarize yourself with the development flow.


## Reporting bugs ##

If you discover behaviour in Gaffer that you suspect is a bug, first:

1. Check to see whether it is a known bug on our [Issues page](https://github.com/GafferHQ/gaffer/issues).
2. Check the [Gaffer community group](https://groups.google.com/forum/#!forum/gaffer-dev) to see whether others have already discussed it.

Once you have determined that the behaviour you have noticed is a bug, [create a new Issue](https://github.com/GafferHQ/gaffer/issues/new) for it. Make sure to fill out the Issue template on GitHub.

If your Issue requires a debug log, you must run Gaffer in a debugger (GDB) and copy its output:

1. In a terminal, launch Gaffer with `env GAFFER_DEBUG=1 gaffer`. GDB will start.
2. Enter `run` to begin Gaffer in debug mode.
3. When an error or a crash occurs, copy the output of the log.


## Contributing code ##

### Pull requests ###

If you have a fork of Gaffer and have made improvements, and you would like to see them merged with the main project, you can create a new [Pull Request](https://github.com/GafferHQ/gaffer/pulls) (PR). Make sure to fill out the PR template on GitHub.

> **Note:** If you are developing a _separate_ project based on Gaffer, you have no obligation to merge your improvements to the main Gaffer project – you can manage your project independently at your own discretion.

For small bug fixes and code cleanup, feel free to make a PR without consulting a project maintainer.

If you are planning on making a significant change, such as a new feature, a refactorization, or a rewrite, please discuss your plans first with the project maintainers on the [community group](https://groups.google.com/forum/#!forum/gaffer-dev). This will help us all avoid duplicated effort and ensure that your ideas fit with the direction of the project. It's always a good idea to ask anyway, as our developers will be happy to suggest implementations and strategy.

If your PR adds a new feature, it must come with a unit test for the feature. Tested code is good code. We like proof that your code works!

All PRs must be reviewed and approved by the project maintainers before being merged.


### Commits ###

Each commit in your PR must perform one logically distinct set of changes. It must also have an accompanying useful message that gives everyone a good idea of what you've done.

We have several message best practices, which, if followed, result in a succinct, informative commit history that can be natively displayed in a variety of disparate protocols and applications, such as email and IDEs. The goal is for anyone to be able to look through the commit log on its own and have a reasonably detailed idea of what was changed and why.


#### Commit message best practices ####

- Each line of the message should be 72 characters or less.
- The first line's message should start with the name of the module or area of the project being affected, followed by a space, a colon, another space, and finally by a _general_ description. Example: `Interface : Add MyButton`.
- If the message is multi-line, the second line should be blank, to preserve formatting.
- If the commit makes several small but important changes, list them line-by-line, with each line starting with a hyphen followed by a space, followed by a description of the change.


### Example commits for a new Feature ###

#### Commit 1 ####

```
Interface : Add MyButton

Button to add my new function, which does x. Uses similar  
implementation to a standard MenuButton, with a workaround to prevent  
the onClick event.
```

Files changed:
- MyButton.h
- MyButton.cpp
- Interface.cpp

#### Commit 2 ####

```
GUI : Add MyButton to main window
```

Files changed:
- MyButton.py
- GUI.py


#### Commit 3 ####

```
Resources : Add graphics for MyButton

- MyButtonDot.svg : red dot
- MyButtonCursor.svg : cursor for dragging button
- MyButtonBorder.svg : black border
- MyButtonGradient.svg : grey-to-white gradient for background
```

Files changed:
- MyButtonDot.svg
- MyButtonCursor.svg
- MyButtonBorder.svg
- MyButtonGradient.svg


#### Commit 4 ####

```
MyButton : Add unit test
```

Files changed:
- MyButtonTest.py
