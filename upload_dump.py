#!/usr/bin/env/python3

from perkeepap import pk_exporter, ap_importer
import perkeeppy

if __name__ == "__main__":
    import argparse
    import logging
    from perkeepap.logger import logger
    import sys

    arg_parser = argparse.ArgumentParser(prog="upload_dump")
    arg_parser.add_argument("--directory", "-d", metavar="PATH", type=str,
                            help="path to the dump files")
    arg_parser.add_argument("--actor", "-a", type=str,
                            help="ActivityStreams id of the target actor")
    arg_parser.add_argument("perkeep", metavar="PERKEEP", type=str,
                            help="Address of the running Perkeep server")
    arg_parser.add_argument("-v", "--verbose", action="store_true",
                            help="Turn on debug logging")


    args = arg_parser.parse_args()

    # Logging setup
    handler = logging.StreamHandler()
    logger.addHandler(handler)

    if args.verbose:
        handler.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    else:
        handler.setLevel(logging.INFO)
        logger.setLevel(logging.INFO)


    data = ap_importer.ApData.from_dir(args.directory)

    # Mastodon dumps have a single actor, so using the first one we find should
    # work pretty well
    if not args.actor:
        actor = next(data.find_persons())
    else:
        actor = args.actor
    
    notes = ap_importer.ApOutbox(data, actor).notes_only()
    conn = perkeeppy.connect(args.perkeep)

    if args.directory:
        exporter = pk_exporter.ApUploader(conn, args.directory)
    else:
        exporter = pk_exporter.ApUploader(conn)
    exporter.upload_items(notes)

