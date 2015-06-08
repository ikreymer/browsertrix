ArchiveThis.WebSite
===================

This project contains a webapp and a Docker compose setup to 
allow for on-demand browsing of any web site, geared towards on-demand archiving.

The current configuration uses chrome workers only.


### Installation

Docker and Docker Compose are the only requirements for running in Docker.

After cloning this repository, run `docker-compose up`

Access at `http://$DOCKER_HOST/` where `DOCKER_HOST` is the host where Docker is running.


#### Cluster Sizing

Using Docker Compose scale feature, it is possible to dynamically resize the number of workers and browsers.
The cluster automatically starts with only one browser and worker.

The `set-scale.sh` script is provided for convenience, eg: to set up 10 workers and browsers, run:

`./set-scale.sh 10`


### Archiving a Url

To archive a url, make a GET request to `http://<DOCKER HOST>/archivepage?url=[url]&handler=[handler]`

The `[handler]` can be one of the hanlders specified in `config.yaml`, currently:

* `ia-save` - for Internet Archive Save Page Now

* `webrecorder` - for https://webrecorder.io/

* `test` - for dry run with https://webrecorder.io/ (preview mode, no actual archiving)

### Results

TODO

#### Support

Initial work on this project was sponsored by the [Hypothes.is Annotation Fund](http://anno.fund/#portfolioModal2)
