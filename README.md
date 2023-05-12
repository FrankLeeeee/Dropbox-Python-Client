# Dropbox-Python-Client

Some simple scripts to perform upload and download for Dropbox

```bash
# set token
dbx crendential --token <your-dropbox-token>

# upload a file/folder
dbx upload -s <your-local-path> -d <remote-folder-path>

# for example
# the destination must be a folder
dbx upload -s ~/Downloads/README.md -d /Downloads
dbx upload -s ~/Downloads -d /Downloads

# download a file

```
