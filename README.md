Implementation of BitTorrent client in Python.

## Running Client
Run `python /src/run.py` to launch console. The console currently supports the following commands:

`add [torrent_file_path] [download_to_path]`
Add torrent to start download.

`refresh`
Force client get new peer list from tracker.

`status`
Prints status of torrents.

`peer`
Prints status of peers.

`quit`
Quit program.

## Files Contained
`/resource` contains sample torrents to test with.

`/src` contains source code and tests.

`/tracker` is a naive implementation of tracker, to use, run `node /tracker/bin/www`, not optimized for production.
