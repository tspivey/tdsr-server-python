# Python tdsr server
This is a server for [tdsr], written in Python, running on Windows.
[tdsr]: https://github.com/tspivey/tdsr

## Requirements
This requires a working Python installation, and `nvdaControllerClient64.dll`.

## Usage
Run `python server.py`.
It will listen for connections on port 64111.

On the machine running tdsr, create a shell script, something like:
```shell
#!/bin/bash
exec socat - TCP4:SERVER_IP:64111,nodelay
```

Replace `SERVER_IP` with the IP address of the server.

## Security
This program binds to all interfaces on port 64111. The only things it lets you do are speak a string, and stop speech.
