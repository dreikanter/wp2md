# Wordpress to Markdown Exporter

A python script to convert Wordpress XML dump to a set of plain text/[markdown](http://daringfireball.net/projects/markdown) files. Intended to be used for migration from Wordpress to [public-static](http://github.com/dreikanter/public-static) website generator but could also be helpful as general purpose content processor.

Requirements:

* Python 2.7
* Python-Markdown

## Processing

Common blog metadata:

* Collect rss/channel element data
* Save it in key:value format to 'blog.txt'

Posts and pages:

* Collect rss/channel/item elements data where post_type is 'page' or 'post'
* Store the data in separate file for each post
* File names should be '{date:YYYY.MM.DD}_{post_id}_{post_name}.txt'
* Posts and pages should be kept in 'posts' and 'pages' directories respectively.
* Comments [TBD]

Images:

* Extract all src values from img-elements inside posts
* Extend all relative URLs to absolute using root URL from RSS header
* Map URL to new image names: {post date}_{post title}_{#}.{ext}
* Download images and save them locally using new file names (saving path is conf param)
* Replace src attribute values for all img elements during .md files generation

Attachments:

* Collect all relative and ansolute URLs from a-elements poining to the site
* Do the same thing as for images

Comments file format:

	[comment header]
	[comment body]
	--
	[next comment header]
	[next comment body]
	--
	...

Comment header includes all exported fields:

* id
* author
* author_email
* author_url
* author_IP
* date
* date_gmt
* content
* approved
* type
* parent
* user_id
