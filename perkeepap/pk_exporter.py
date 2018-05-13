import perkeeppy 
from perkeeppy import Blob, make_permanode, make_claim
import json
import pathlib
import urllib.parse

from typing import Iterable, Optional
from os import PathLike

from perkeepap.logger import logger
from perkeepap.ap_importer import get_aliased
from perkeepap.exceptions import MissingAsDataError

class ApUploader(object):

    def __init__(self, perkeep: perkeeppy.Connection, root_dir: Optional[PathLike] = None) -> None:
        self.perkeep = perkeep
        self.root_dir = pathlib.Path(root_dir) if root_dir else pathlib.Path()

    def upload_items(self, items: Iterable[dict]):
        """
        Upload all items from iterable ``items``, containing ActivityStreams
        activities.
        """

        added = 0
        skips = 0

        for item in items:
            res = self.upload_item(item)

            if res > 0:
                added += res
            else:
                skips += 1

        logger.info(f'Done processing. Added {added} new entries, skipped {skips} entries.')

    def upload_item(self, item: dict) -> int:
        """
        Upload a single AS item to the server.

        Returns the number of new permanodes uploaded to server
        """

        as_id = get_aliased(item, 'id')

        if not as_id:
            raise MissingAsDataError('Item has no id')

        existing = self.perkeep.searcher.query(f'attr:asId:"{as_id}"')

        if existing:
            logger.info(f'{as_id}: Already exists')
            return 0

        # Collect everything first, and only then start putting.

        pnode = make_permanode().to_blob(self.perkeep.signer)
        
        as_object = Blob(json.dumps(item).encode())

        claims = [('camliType', 'set', 'ActivityStreams:Create:Note'),
                ('camliPath:object', 'add', as_object.blobref),
                ('asId', 'set', as_id)]


        # Re-raise if the item doesn't have a needed field for some reason
        try:
            obj_id = get_aliased(item['object'], 'id')

            if not obj_id:
                raise MissingAsDataError('ActivityStreams object has no id')

            claims.append(('asObjectId', 'set', obj_id))
            claims.append(('asActor', 'set', item['actor']))
            claims.append(('camliPath:object', 'set', as_object.blobref))

            html_text = item['object']['content']

            if item['object'].get('summary'):
                # This is not the most robust way to do this, but it should
                # work for Mastodon data
                html_test = f'<p class="summary">{item["object"]["summary"]}</p>{html_text}'

            claims.append(('content', 'set', html_text))

            # Timestamp should already be a compatible format
            claims.append(('startDate', 'set', item['published']))


        except KeyError as e:
            raise MissingAsDataError('Some of the required data was missing') from e

        # Upload the attachments first. No harm if we put them, and then fail to
        # put the note itself, since they'll just float around as regular files
        if item['object'].get('attachment'):
            for n, attachment in enumerate(item['object']['attachment']):
                # TODO: We might want to fetch from remote URLs here, if
                # encountered

                path_str = attachment['url']

                # Mastodon takeouts give paths relative to archive root, but 
                # with a leading slash, which Python considers absolute paths,
                # at least when POSIX
                if path_str[0] == '/':
                    path_str = path_str[1:]


                path_str = urllib.parse.unquote(path_str)
                path = self.root_dir / pathlib.Path(path_str)

                with open(path, 'rb') as f:
                    attachment_ref = self.perkeep.uploadhelper.upload_file(path.name, f)
                
                claims.append((f'camliPath:attachment{n}', 'set', attachment_ref))
                logger.debug(f'{as_id}: Put attachment {n}: {path.name} → {attachment_ref}')

        claim_blobs = (make_claim(pnode.blobref, *claim).to_blob(self.perkeep.signer) for claim in claims)

        # Now we start putting the ActivityStreams object itself
        self.perkeep.blobs.put_multi(pnode, as_object, *claim_blobs)
        logger.info(f'{as_id}: New permanode → {pnode.blobref}')

        return 1

