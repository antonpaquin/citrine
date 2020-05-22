"""
An "interface" is the UI version of a package.
Not to be confused with "UI", which is the stuff that runs on QT.
"""

"""

So it comes time to figure out UI packages

What does a UI package need to do?
Ultimately, deliver a view to the UI
    which is a bundle of html / js / css / assets
    which is effectively just a file structure
    (I kinda really don't want to deal with cgi in this case)

How do I want to deal with it?
I kinda like the idea of having a metadata file

Converging on
root directory: meta.json, + other stuff
meta.json points to / names directories in root dir which hold web packs

Like
{
    "name": "fooPkg",
    "version": "1.0.0",
    "humanname": "foo",
    "views": {
        "fooView": {
            "root": "/foo",
            "page": "index.html",
        }
    },
    "requires_daemon": [
        "TWDNEv3==1.0.0",
    ]
}

For now, let's group everything under (package name -> view name)

Do I have a different metaphor than "package" to use? Overloading for UI and daemon is probably confusing

"""