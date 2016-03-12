# gh-rep

This is an experiment with a reputation system using the GitHub API. This is not designed to :ship:, it is a hack to experiment with.

Currently it:

 * Gathers the most recent 90 days of content (limited to 300 events by the API)
 * Processes these events and applies scores (for some events further processing happens)
 * Generates a report with summary lists for the most active participants

## Requirements

 * This is written in Python. It uses the `response`, `sqlite3`, and standard Python library modules.
 * You will also need a Client ID and Secret for the GitHub API.

## Running

Simply run `rep.py` and pass it the following arguments:

 * `-i` - Client ID
 * `-s` - Client Secret
 * `-r` - Repo to process

For example:

    python rep.py -i 000000000000000000 -s 000000000000000000000000000000000 -r "MycroftAI/mimic"
