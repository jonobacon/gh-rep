# gh-rep

This is an experiment with a reputation system using the GitHub API. This is not designed to :ship:, it is a hack to experiment with.

Currently it:

 * Gathers the most recent 90 days of content (limited to 300 events by the API)
 * Processes these events and applies scores (for some events further processing happens)
 * Includes a simple web app to present the data.

## Requirements

 * This is written in Python. It uses the `response`, `sqlite3`, `cherrypy`, and standard Python library modules.
 * You will also need a Client ID and Secret for the GitHub API.

## Running

Rename the included `gh-rep.conf.sample` file to `gh-rep.conf` and add your client ID and client secret strings. You can then run the following to process a given repo:

    python rep.py -r "MycroftAI/mimic"

Alternatively, you can pass these arguments:

 * `-i` - Client ID
 * `-s` - Client Secret
 * `-r` - Repo to process

For example:

    python rep.py -i 000000000000000000 -s 000000000000000000000000000000000 -r "MycroftAI/mimic"

Now go to `http://127.0.0.1:8080/` to view the web app.
