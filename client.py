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

    def download(self, remote_path, local_path):
        """Download a file.

        Return the bytes of the file, or None if it doesn't exist.
        """
        with self.stopwatch('download'):
            try:
                md, res = self.dbx.files_download(remote_path)
            except dropbox.exceptions.HttpError as err:
                print('*** HTTP error', err)
                return None
        data = res.content
        print(len(data), 'bytes; md:', md)

        with open(local_path, 'wb') as f:
            f.write(data)
        return data

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
