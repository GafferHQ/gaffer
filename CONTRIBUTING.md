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


## Code reviews and labels ##

### Label guidelines ###
For labels, our primary concern is to clearly and consistently distinguish between Issue labels and Pull Request (PR) labels. 

For an up-to-date list of Gaffer's GitHub labels, see the project's [Labels](https://github.com/GafferHQ/gaffer/labels) page.

We have the following general specs for labels:
- Unfortunately, there is currently no way to maintain separate lists of labels based on their intended use. Therefore, PR labels are prefixed with `pr-`.
- PR labels that communicate that the PR needs immediate attention have high-intensity colors.
- PR labels that communicate that the PR should not be merged yet have medium-intensity colors.
- Issue labels have no prefix, and have low-intensity colors.

#### Issue labels ####
Examples: `arnold` `bug`

The purpose of Issue labels is to help us filter and sort our active Issues. We have chosen very subtle colors and short names for them.

If you're creating an Issue, please apply as many of these labels that match. **Do not** apply these labels to PRs.

#### Pull Request labels ####
Examples: `pr-hold` `pr-revision`

The purpose of PR labels is to signal which PRs can't be merged yet. A PR could be unready for merging for two reasons: the PR needs more work (`pr-revision` and `pr-docs`) or the PR must wait for something else to happen in the code base (`pr-hold` and `pr-blocked`).

### Pull Request reviews ###
In order to effectively and efficiently maintain our Pull Requests (PRs), our contributors and reviewers must follow these PR guidelines:

#### When creating a PR (contributor) ####
* Assign yourself as the PR's Assignee. The Assignee is the PR's stakeholder/owner.
* Assign at least one contributor as a Reviewer. We will not merge any PRs that haven't been reviewed.

#### When reviewing a PR (reviewer) ####
* Make sure to _Start a review_. Do not simply leave comments on their own.
> **Tip:** After making line-by-line comment(s) in the _Files changed_ tab of a PR, you can collect all your comment(s) into a review by clicking _Start a review_ on the comments themselves, and then finish by clicking _Review changes_ at the top-right of the tab.
* If you have asked for any changes, apply the `pr-revision` and/or `pr-docs` label.
* If you are a collaborator, do not merge a PR that has either the `pr-revision` or `pr-docs` labels.

#### When addressing a PR review (contributor) ####
* Once you have pushed new commits to address the review, reply to each review comment with "Fixed in <sha1>", linking to the relevant commit. Do **not** click _Resolve conversation_.
* If you think there may be more to discuss with the remaining review comments, reply or leave them as-is.
* Once you believe you've addressed all requests, remove the `pr-revision` and/or `pr-docs` label(s).
* Notify your reviewers that your PR is ready for another look by clicking the re-request icon in the _Reviewers_ section:![Re-request review](https://help.github.com/assets/images/help/pull_requests/request-re-review.png)

#### When re-reviewing a PR (reviewer) ####
* Click _Resolve conversation_ on review comments that the Assignee has addressed in their update.
* Resolve or ask for updates on any review comments the Assignee hasn't responded to.
* If follow-up changes to the PR are required, re-apply the `pr-revision` and/or `pr-docs` label(s).
* If you are a project collaborator, and all feedback is addressed, and the PR does not have any pending reviews, you can merge the PR.
