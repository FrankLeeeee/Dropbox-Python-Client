<p align="center">
  <img src="assets/logo.svg" alt="dbx - Dropbox Python Client" width="480">
</p>

<p align="center">
  A tiny command-line client for uploading and downloading files and folders to and from Dropbox.
</p>

## Installation

```bash
pip install -e .
```

## Usage

```bash
# set token
dbx credential --token <your-dropbox-token>

# upload a file/folder
dbx upload -s <your-local-path> -d <remote-folder-path>

# for example
# the destination must be a folder
dbx upload -s ~/Downloads/README.md -d /Downloads
dbx upload -s ~/Downloads -d /Downloads

# download a file
dbx download -s /Downloads/README.md -d ~/Downloads/README.md

# download a folder (recursively, preserving structure)
# the destination is a local directory and is created if missing
dbx download -s /Downloads -d ~/Downloads
```
