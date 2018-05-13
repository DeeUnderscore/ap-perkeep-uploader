# ActivityPub Perkeep Uploader
This tool takes JSON-LD files with [ActivityStreams](https://www.w3.org/TR/activitystreams-core/) data, such as those found in [Mastodon](https://joinmastodon.org/) data takeouts, and puts them in a [Perkeep](https://perkeep.org/) (formerly known as Camlistore) server. 

The goal is to represent ActivityStream objects, such as a `Note` inside the Perkeep store, much the same way that Twitter tweets can be imported using the importer included with Perkeep.

## Notes and warnings
This tool targets Mastodon data takeouts. ActivityStreams and ActivityPub are standards, which means that the tool *may* also be able to process data acquired elsewhere, but some missing features may make that impossible—for example, files are not fetched from remote URLs. This tool is not a full ActivityPub client, nor is it a Perkeep importer (in that it is not part of the Perkeep daemon).

Deleting things out of Perkeep is currently rather difficult. This includes any data this tool puts in Perkeep. Please keep this in mind when using it. 

As the program issues requests synchronously, and has to sign a large amount of blobs, it can take a while to process a large amount of notes. It will skip already existing permanodes, and so can be reran after interruptions. 

## How to 
### Installation

Dependencies can be downloaded with [Pipenv](https://docs.pipenv.org/).
```shellsession
$ pipenv install 
```

If you do not use Pipenv, you can use the supplied `requirements.txt` with Pip as usual (perhaps activating your own virtualenv beforehand):
```shellsession
$ pip install -r requirements.txt 
```

### Usage
If your data takeout is in an archive (like Mastodon's is), you will need to extract it somewhere. Then, invoke `upload_dump.py` and point it at the directory and the Perkeep server. You can do it via Pipenv:
```shellsession
$ pipenv run upload_dump --directory path/to/extracted/archive http://localhost:3179
```

Without Pipenv, use `python3 upload_dump.py` instead.

If you do not supply an `--actor`, the program will try to find one. The Mastodon takeout contains only one actor node, so it should be found easily. You can also supply `-v` for more verbose logging to stdout. 

## Schema

Each `Create` activity with a `Note` object gets a permanode with the following attributes:

* **asId**: the `id` field of the activity
* **asObjectId**: the `id` of the object the activity created
* **asActor**: the `id` of the Actor responsible for this activity
* **camliPath:object**:  blobref of the ActivityStreams JSON, with both the activity and the object. This is the JSON directly, not a Perkeep schema node.
* **camliPath:attachmentN**: where *N* is replaced by a 0-indexed, non-padded number. These are the attachments to the `Note` object, in the same order as in the attachments array in the ActivityStreams JSON.
* **content**: the content of the note. Summary and content fields are concatenated here.
* **startDate**: set to the time stamp for the activity
* **camliType**: set to `ActivityStreams:Create:Note`


## License
The source files in this project is available under the ISC license. For full text, see [LICENSE](/LICENSE).
