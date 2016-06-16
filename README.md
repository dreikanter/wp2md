# WordPress to Markdown Exporter

> **Update:** I don't have much time to maintain this project, but I would really appreciate community help. If you looking for an open source project to contribute, it's a great opportunity. Pull request a very appreciated by me and migrating WordPress users.

A python script to convert WordPress XML dump to a set of plain text/[markdown](http://daringfireball.net/projects/markdown) files. Intended to be used for migration from WordPress to [public-static](http://github.com/dreikanter/public-static) website generator, but could also be helpful as general purpose WordPress content processor.


## Installation

The script could be installed by command:

	pip install git+https://github.com/dreikanter/wp2md

It will install wp2md and the following dependencies:

* [html2text](https://github.com/aaronsw/html2text/)
* [python-markdown](http://pypi.python.org/pypi/Markdown/)


## Usage

[Export](http://en.support.wordpress.com/export/) WordPress data to XML file (Tools → Export → All content):

![WordPress content export](http://img-fotki.yandex.ru/get/6403/988666.0/0_a05db_af845b23_L.jpg)

And then run the following command:

	wp2md -d /export/path/ wordpress-dump.xml

Where `/export/path/` is the directory where post and page files will be generated, and `wordpress-dump.xml` is the XML file exported by WordPress.

Use `--help` parameter to see the complete list of command line options:

	usage: wp2md [options] source

	Export WordPress XML dump to markdown files

	positional arguments:
	  source      source XML dump exported from WordPress

	optional arguments:
	  -h, --help  show this help message and exit
	  -v          verbose logging
	  -l FILE     log to file
	  -d PATH     destination path for generated files
	  -u FMT      <pubDate> date/time parsing format
	  -o FMT      <wp:post_date> and <wp:post_date_gmt> parsing format
	  -f FMT      date/time fields format for exported data
	  -p FMT      date prefix format for generated files
	  -m          preprocess content with Markdown (helpful for MD input)
	  -n LEN      post name (slug) length limit for file naming
	  -r          generate reference links instead of inline
	  -ps PATH    post files path (see docs for variable names)
	  -pg PATH    page files path
	  -dr PATH    draft files path
	  -url        keep absolute URLs in hrefs and image srcs
	  -b URL      base URL to subtract from hrefs (default is the root)


## The output

The script generates a separate file for each post, page and draft, and groups it by configurable directory structure. By default posts are grouped by year-named directories and pages are just stored to the output folder.

![Exported files](http://img-fotki.yandex.ru/get/6500/988666.0/0_a05da_66f67f9f_L.jpg)

But you could specify different directory structure and file naming pattern using `-ps`, `-pg` and `-dr` parameters for posts, pages and drafts respectively. For example `-ps {year}/{month}/{day}/{title}.md` will produce date-based subfolders for blog posts.

Each exported file has a straightforward structure intended for further processing with [public-static](http://github.com/dreikanter/public-static) website generator. It has an INI-like formatted header followed by markdown-formatted post (or page) contents:

	title: Я.Субботник в Санкт-Петербурге, 3 декабря
	link: http://paradigm.ru/yandex-subbotni
	creator: admin
	description: 
	post_id: 635
	post_date: 2011-11-23 22:10:35
	post_date_gmt: 2011-11-23 19:10:35
	comment_status: open
	post_name: yandex-subbotnik
	status: publish
	post_type: post

	# Я.Субботник в Санкт-Петербурге, 3 декабря

	Я.Субботник в Санкт-Петербурге пройдет 3 декабря в [офисе Яндекса](http://company.yandex.ru/contacts/spb/).
	...

If the post contains comments, they will be included below.


## See also

* How to [export WordPress data](http://codex.wordpress.org/Tools_Export_Screen)
* How to [export Wordpress.com data](http://en.support.wordpress.com/export/)
* [Wordpress to Hugo exporter](https://github.com/SchumacherFM/wordpress-to-hugo-exporter)


## Copyright and licensing

Copyright &copy; 2013 by [Alex Musayev](http://alex.musayev.com).  
License: GNU (see [LICENSE](https://raw.github.com/dreikanter/wp2md/master/LICENSE)).

Project home: [https://github.com/dreikanter/wp2md](https://github.com/dreikanter/wp2md).
