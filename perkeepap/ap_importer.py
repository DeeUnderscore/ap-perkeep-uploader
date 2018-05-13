import json
import pathlib
import queue

from os import PathLike
from typing import Union, Optional, Any, Iterable 

from perkeepap.logger import logger
from perkeepap.exceptions import MissingAsDataError


def get_collection(parent: dict):
    """
    Returns an ActivityStreams collection for items that have one. Returns None 
    if there is no collection.
    """
    
    ld_type = get_aliased(parent, 'type')

    # Names below are per spec
    if ld_type == 'Collection':
        return parent['items']

    if ld_type == 'OrderedCollection':
        return parent['orderedItems']

    return None


def get_aliased(ld_object: dict, ld_key: str) -> dict:
    """
    Get a JSON-LD field, checking for @-aliases. If neither the @form nor the
    aliased form is present, returns ``None``.
    """ 
    if ld_key in ld_object:
        return ld_object[ld_key]
    
    ld_key = '@' + ld_key

    if ld_key in ld_object:
        return ld_object[ld_key]

    return None

class ApData(object):
    """
    Class representing some ActivityPub data in ActivityStreams format
    """

    def __init__(self, jsons: Iterable[Any]) -> None:
        """
        Initialize the object from an iterable of parsed json objects. 
        """

        self.jsons: Union[list,dict] = list(jsons)

    @classmethod
    def from_dir(cls, directory: Optional[PathLike] = None):
        """
        Load all jsons from a directory. If directory is not defined, the 
        jsons are collected from current working directory

        Unopenable or unreadable files are skipped.
        """
        datadir = pathlib.Path(directory) if directory else pathlib.Path()

        def get_jsons():
            for file in datadir.glob('**/*.json'):
                try:
                    with open(file, 'r') as f:
                        logger.debug(f'Loading file: {file}...')
                        yield json.load(f)

                except json.JSONDecodeError:
                    logger.exception(f'Problem decoding {file.name} as JSON. Skipping...')
                except OSError:
                    logger.exception(f'Problem reading {file.name}. Skipping...')


        return cls(get_jsons())

    def get_by_id(self, ld_id: str) -> dict:
        """
        Return the top-level object with matching id. ``None`` is returned if no
        matching object wass found.
        """

        # TODO: remote fetching?
        return next((item for item in self.jsons if get_aliased(item, 'id') == ld_id), None)

    def find_persons(self):
        """
        Find all Person nodes, and yield the id for each.

        In the most common case, this function will return only one id.
        """

        for node in self.jsons:
            if get_aliased(node, 'type') == 'Person':
                yield get_aliased(node, 'id')


class ApOutbox(object):
    """
    A class representing an activitypub outbox

    :param ap_data: The :class:`ApData` object with the relevant jsons
    :param actor_id: The ActivityPub id of the actor who we are trying to
        get the outbox. 

    :raises MissingAsDataError: Raised when the supplied ``ap_data`` does 
        not contain the necessary data
    """

    def __init__(self, ap_data: ApData, actor_id: str) -> None:
        self.ap_data = ap_data
        self.actor = ap_data.get_by_id(actor_id)

        if not self.actor:
            raise MissingAsDataError(f'Could not find actor with id {actor_id}')

        try:
            outbox_id = self.actor['outbox']
        except KeyError as ex:
            raise MissingAsDataError('Actor has no outbox') from ex

        outbox_node = ap_data.get_by_id(outbox_id)
        if not outbox_node:
            raise MissingAsDataError('Outbox with requested id was not found')

        # An outbox is always a collection per spec
        self.outbox = get_collection(outbox_node)


    def __iter__(self):
        yield from self.outbox


    def notes_only(self):
        """
        Generator which filters collection objects to include only ActivityStreams 
        Note creations. 

        This skips announces and creations of other stuff.
        """

        for item in self.outbox:
            if (get_aliased(item, 'type') == 'Create'and 
                get_aliased(item['object'], 'type') == 'Note'):

                yield item

