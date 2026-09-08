import contextlib
import os
import time

import dropbox

__all__ = ['DropboxClient']


class DropboxClient:

    def __init__(self, token, timeout=900, chunk=128):
        self.token = token
        self.timeout = timeout
        self.chunk = chunk
        self.dbx = None

    def connect(self):
        self.dbx = dropbox.Dropbox(self.token, timeout=self.timeout)

    @contextlib.contextmanager
    def stopwatch(self, message):
        """Context manager to print how long a block of code took."""
        t0 = time.time()
        try:
            yield
        finally:
            t1 = time.time()
            print('Total elapsed time for %s: %.3f' % (message, t1 - t0))

    def _download_file(self, remote_path, local_path):
        """Download a single file to ``local_path``.

        If ``local_path`` is an existing directory, the file is placed inside
        it using its remote basename.
        """
        if os.path.isdir(local_path):
            local_path = os.path.join(local_path, os.path.basename(remote_path))

        parent = os.path.dirname(local_path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent)

        since = time.time()
        try:
            md = self.dbx.files_download_to_file(local_path, remote_path)
        except (dropbox.exceptions.HttpError, dropbox.exceptions.ApiError) as err:
            print('*** Failed to download {}: {}'.format(remote_path, err))
            return None

        time_elapsed = time.time() - since
        print('Downloaded {} -> {} ({} bytes)'.format(remote_path, local_path, md.size).ljust(15) +
              ' --- {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60).rjust(15))
        return md

    def _list_folder_files(self, remote_path):
        """Yield FileMetadata for every file under ``remote_path``, recursively."""
        result = self.dbx.files_list_folder(remote_path, recursive=True)
        while True:
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    yield entry
            if not result.has_more:
                break
            result = self.dbx.files_list_folder_continue(result.cursor)

    def _download_folder(self, remote_path, local_path):
        """Download every file under ``remote_path`` into the local directory
        ``local_path``, preserving the folder structure."""
        remote_path = remote_path.rstrip('/')
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        num_files = 0
        for entry in self._list_folder_files(remote_path):
            # path_display keeps the original casing for the local file name.
            rel_path = entry.path_display[len(remote_path):].lstrip('/')
            dest = os.path.join(local_path, *rel_path.split('/'))
            self._download_file(entry.path_display, dest)
            num_files += 1

        print('Downloaded {} file(s) from {} to {}'.format(num_files, remote_path, local_path))

    def download(self, remote_path, local_path):
        """Download a file or a folder.

        If ``remote_path`` is a file, it is saved to ``local_path`` (or inside
        it, if ``local_path`` is an existing directory). If ``remote_path`` is
        a folder, its full contents are downloaded recursively into the local
        directory ``local_path``.
        """
        with self.stopwatch('download'):
            try:
                md = self.dbx.files_get_metadata(remote_path)
            except dropbox.exceptions.ApiError as err:
                print('*** Cannot find {}: {}'.format(remote_path, err))
                return None

            if isinstance(md, dropbox.files.FolderMetadata):
                self._download_folder(md.path_display, local_path)
            else:
                self._download_file(remote_path, local_path)

    def _upload_file(self, local_path, remote_path):
        # compute chunk size
        file_size = os.path.getsize(local_path)
        CHUNK_SIZE = self.chunk * 1024 * 1024

        # get upload path
        dest_path = remote_path + '/' + os.path.basename(local_path)

        # upload
        since = time.time()
        with open(local_path, 'rb') as f:
            uploaded_size = 0

            if file_size <= CHUNK_SIZE:
                # use files_upload if the file is smaller than a chunk
                self.dbx.files_upload(f.read(), dest_path)
                time_elapsed = time.time() - since
                print('Uploaded {} - {:.2f}%'.format(local_path, 100).ljust(15) +
                      ' --- {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60).rjust(15))
            else:
                upload_session_start_result = self.dbx.files_upload_session_start(f.read(CHUNK_SIZE))
                cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                           offset=f.tell())
                commit = dropbox.files.CommitInfo(path=dest_path)
                while f.tell() <= file_size:
                    if ((file_size - f.tell()) <= CHUNK_SIZE):
                        self.dbx.files_upload_session_finish(f.read(CHUNK_SIZE), cursor, commit)
                        time_elapsed = time.time() - since
                        print('Uploaded {} - {:.2f}%'.format(local_path, 100).ljust(15) +
                              ' --- {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60).rjust(15))
                        break
                    else:
                        self.dbx.files_upload_session_append_v2(f.read(CHUNK_SIZE), cursor)
                        cursor.offset = f.tell()
                        uploaded_size += CHUNK_SIZE
                        uploaded_percent = 100 * uploaded_size / file_size
                        time_elapsed = time.time() - since
                        print('Uploaded {} - {:.2f}%'.format(local_path, uploaded_percent).ljust(15) +
                              ' --- {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60).rjust(15),
                              end='\r')

    def upload(self, local_path, remote_path):
        # print(local_path)
        # check if local_path is a file
        if os.path.isfile(local_path):
            self._upload_file(local_path, remote_path)
        else:
            # walk through the directory
            # if it is a folder, call upload recursively
            # if it is a file, call _upload_file
            for path in os.listdir(local_path):
                cur_local_path = os.path.join(local_path, path)

                if os.path.isdir(cur_local_path):
                    cur_remote_path = remote_path + '/' + path
                else:
                    cur_remote_path = remote_path
                self.upload(cur_local_path, cur_remote_path)
