## Note: This repository is obsolete and represents an original attempt at browser automation.
## Please see the new Browsertrix at [webrecorder/browsertrix](https://github.com/webrecorder/browsertrix)

## Browsertrix 0.1.1

Browsertrix is a web archiving automation system, desgined to create high-fidelity web archives
by automating real browsers running in containers (Docker) using Selenium and other automation tools.
The system does not currently do any archiving of its own, but automates browsing loading through existing archiving
and recording tools.

By loading pages directly through a browser, it will be possible to fully recreate a page as the user experiences it, including all dynamic content
and interaction.

Browsertrix is named after Heritrix, the venerable web crawler technology which has become a standard for web archiving.

## What Browsertrix Does

The first iteration of Browsertrix supports archiving a single web page, through an existing archiving back-end.

Urls can be submitted to Browsertrix via HTTP and it will attempt to load the urls in an available browser right away.
Browsertrix can operate synchronously or asynchronously. If the operation does not complete within the specified timeout
(default 30 secs), a `queued` response is returned and the user may retry the operation to get the result at a later time.
The results of the archiving operation are cached (for 10 mins if successful, for 30 secs otherwise) so that future requests will return the cached result.

Redis is used to queue urls for archiving, and cache results for the archiving operation. Configurable options
are currently available in the `config.py` module.

Additional automated browser "crawling" and multi-url features are planned for the next iteration.


### Installation

Docker and Docker Compose are the only requirements for running Browsertrix.

Install Docker as recommended at: https://docs.docker.com/installation/

Install Docker Compose with: `pip install docker-compose`

After cloning this repository, run `docker-compose up`

### Web Interface

In this version, a basic 'Archive This Website' UI is available on the home page and provides a form to submit urls
to be archived through Chrome or Firefox. The interfaces wraps the Archiving API explained below.

The supported backends are https://webrecorder.io/ and IA Save Page Now feature.

`http://$DOCKER_HOST/` where `DOCKER_HOST` is the host where Docker is running.


### Scaling Workers

By default, Browsertrix starts with one Chrome and one Firefox worker. `docker-compose scale` can be used
to set the number of workers as needed.

The `set-scale.sh` script is provided as a convenience to resize the number of workers, resizing both
the Chrome and Firefox workers. For example, to have 4 of each browser, you can run:

`./set-scale.sh 4`


### Archiving API `/archivepage`

This first iteration of Browsertrix provides an api endpoint at the `/archivepage` endpoint for archiving a single page.

To archive a url, a GET request can be made to `http://<DOCKER HOST>/archivepage?url=URL&archive=ARCHIVE[&browser=browser]`

* `url` - The URL to be archived

* `archive` - One of the available archives specified in `config.py`. Current archives are `ia-save` and `webrecorder`

* `browser` - (Optional) Currently either `chrome` or `firefox`. Chrome is the default if omitted.

### Results

The result of the archiving operation is a JSON block. The block contains one of the following.

* `error: true` is set and `msg` field contains more details about the error.
  The `type` field indicates a specific type of error, eg: `type: blocked` currently indicates the archiving service can not
  archive this page.

* `queued: true` is the timeout for archiving the page (currently 30 secs) has been exceeded. If this is the case, the url has been put on a queue and the query should be retried until the page is archived. `queue-pos` field indicates the position in the queue, with `queue-pos: 1` means the url is up next, and `queue-pos: 0` means the url is currently being loaded in the browser.

* `archived: true` is set if the archiving of the page has fully finished. The following additional properties may be set in the JSON result:

   - `replay_url` - if the archived page is immediately available for replay, this is the url to access the archived content.
  
   - `download_url` - if the archived content is available for download as a WARC file, this is the link to the WARC.
   
   - `actual_url` - if the original url caused a redirect, this will contain the actual url that was archived (only present if different from original).
    
   - `browser_url` - The actual url loaded by the browser to "seed" the archive.
    
   - `time` - Timestamp of when the page was archived.
   
   - `ttl` - time remaining (in seconds) for this entry to be stored in the cache. After the entry expires, a subsequent query will re-archive the page. Default is 10 min (600 secs) and can be configured in `config.py`
   
   - `log` HTTP response log from the browser, available only in Chrome. The format is `{<URL>: <STATUS>}` for each url loaded to archive the current page.



#### Support

Initial work on this project was sponsored by the [Hypothes.is Annotation Fund](http://anno.fund/#portfolioModal2)
