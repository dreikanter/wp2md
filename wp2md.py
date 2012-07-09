#!/usr/bin/env python
"""[TBD]"""

import os.path
import codecs
import time
import logging
import traceback
from xml.etree.ElementTree import XMLParser


# XML elements to save
WHAT2SAVE = {
    'channel': [
        'title',
        'description',
        'author_display_name',
        'author_login',
        'author_email',
        'base_site_url',
        'base_blog_url',
        'language',
    ],
    'item': [
        'title',
        'link',
        'creator',
        'guid',
        'description',
        'content:encoded',
        'excerpt:encoded',
        'post_id',
        'post_date',
        'post_date_gmt',
        'comment_status',
        'ping_status',
        'post_name',
        'status',
        'post_parent',
        'menu_order',
        'post_type',
        'post_password',
        'is_sticky',
        'content:encoded',
        'excerpt:encoded',
        'excerpt:encoded',
    ],
    'comment': [
        'comment_id',
        'comment_author',
        'comment_author_email',
        'comment_author_url',
        'comment_author_IP',
        'comment_date',
        'comment_date_gmt',
        'comment_content',
        'comment_approved',
        'comment_type',
        'comment_parent',
        'comment_user_id',
    ],
}

MAX_POST_NAME_LEN = 20

log = logging.getLogger(__name__)
conf = {}


def init_conf():
    # TODO: Get it from args
    global conf
    conf['source_file'] = 'wordpress.xml'
    conf['dump_path'] = None
    conf['verbose'] = True

    # <pubDate> format
    conf['parse_date_fmt'] = "%a, %d %b %Y %H:%M:%S +0000"

    # <wp:post_date> format
    conf['post_date_fmt'] = "%Y %H:%M:%S"

    # Date/time fields format for exported data
    conf['date_fmt'] = "%Y-%m-%d %H:%M:%S"

    # File date prefix format
    conf['file_date_fmt'] = '%Y-%m-%d'


def init_logging(verbose=False):
    try:
        global log
        log.setLevel(logging.DEBUG)
        channel = logging.StreamHandler()
        channel.setLevel(logging.DEBUG if verbose else logging.INFO)
        log_fmt = '%(asctime)s %(levelname)s: %(message)s'
        channel.setFormatter(logging.Formatter(log_fmt, '%H:%M:%S'))
        log.addHandler(channel)
    except Exception as e:
        log.debug(traceback.format_exc())
        raise Exception(getxm('Logging initialization failed', e))


# Helpers

def getxm(message, exception):
    """Returns annotated exception messge."""
    return ("%s: %s" % (message, str(exception))) if exception else message


def tag_name(name):
    """Removes expanded namespace from tag name."""
    return name[name.find('}') + 1:]


def parse_date(date_str, format, default=None):
    """Parses date string according to parse_date_fmt configuration param."""
    try:
        result = time.strptime(date_str, format)
    except:
        msg = "Error parsing date string '%s'. Using default value." % date_str
        log.debug(msg)
        result = default

    return result


def get_dump_path(file_name, subdir=''):
    """Generates dump directory absolute path."""
    explicit = conf['dump_path']
    result = explicit or '{date}_{source}'
    result = result.format(date=time.strftime(conf['file_date_fmt']),
                           source=os.path.basename(conf['source_file']))
    return os.path.join(os.path.abspath(result), subdir, file_name)


def get_post_filename(data):
    """Generates file name from item processed data."""
    pid = data.get('post_id', None)
    name = str(data.get('post_name', None))
    if len(name) > MAX_POST_NAME_LEN:
        name = name[:MAX_POST_NAME_LEN] + '_'

    try:
        pub_date = time.strftime(conf['file_date_fmt'], data['post_date'])
    except:
        pub_date = None

    return '_'.join(filter(bool, [pub_date, pid, name])) + '.txt'


# Data dumping

def dump(file_name, data, order):
    """Dumps a dictionary to YAML-like text file."""
    try:
        dir_path = os.path.dirname(os.path.abspath(file_name))
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        with codecs.open(file_name, 'w', 'utf-8') as f:
            content = None
            for field in filter(lambda x: x in data, [item for item in order]):
                if field == 'content:encoded':
                    content = data[field]
                else:
                    if type(data[field]) == time.struct_time:
                        value = time.strftime(conf['date_fmt'], data[field])
                    else:
                        value = data[field]
                    f.write(u"%s: %s\n" % (unicode(field), unicode(value)))
            if content:
                f.write('\n' + content)
    except Exception as e:
        log.error("Error saving data to '%s'" % (file_name))
        log.debug(e)


def dump_channel(data):
    """Dumps RSS channel metadata."""
    file_name = get_dump_path('blog.txt')
    log.info("Dumping blog metadata to '%s'..." % file_name)
    fields = WHAT2SAVE['channel']
    processed = {field: data.get(field, None) for field in fields}

    pub_date = data.get('pubDate', None)
    format = conf['parse_date_fmt']
    processed['export_date'] = parse_date(pub_date, format, time.gmtime())

    dump(file_name, processed, fields)


def dump_item(data):
    """Dumps RSS chnale item."""
    item_type = data.get('post_type', 'other')
    if not item_type in ['post', 'page']:
        return

    fields = WHAT2SAVE['item']
    processed = {field: data.get(field, None) for field in fields}

    # Post date
    format = conf['date_fmt']
    value = processed.get('post_date', None)
    processed['post_date'] = value and parse_date(value, format, None)

    # Post date GMT
    value = processed.get('post_date_gmt', None)
    processed['post_date_gmt'] = value and parse_date(value, format, None)

    # Post content
    value = data.get('content:encoded', None)
    processed['content'] = value and parse_date(value, format, None)

    # Post excerpt
    value = data.get('excerpt:encoded', None)
    processed['excerpt'] = value and parse_date(value, format, None)

    file_name = get_post_filename(processed)
    log.info("Dumping %s\%s..." % (item_type, file_name))
    dump(get_dump_path(file_name, item_type), processed, fields)


# The Parser

class CustomParser:
    def __init__(self):
        self.section_stack = []
        self.channel = {}
        self.items = []
        self.item = None
        self.cmnt = None
        self.field = None
        self.subj = None

    def start(self, tag, attrib):
        tag = tag_name(tag)
        if tag == 'channel':
            self.start_section('channel')
            log.debug('<channel>')

        elif tag == 'item':
            self.item = {'comments': []}
            self.start_section('item')
            log.debug('<item>')

        elif self.item and tag == 'comment':
            self.cmnt = {}
            self.start_section('comment')
            log.debug('<comment>')

        elif self.cur_section():
            self.subj = tag

        else:
            self.subj = None

    def end(self, tag):
        tag = tag_name(tag)
        if tag == 'comment' and self.cur_section() == 'comment':
            self.item['comments'].append(self.cmnt)
            self.cmnt = None
            self.end_section()
            log.debug('</comment>')

        elif tag == 'item' and self.cur_section() == 'item':
            dump_item(self.item)
            self.item = None
            self.end_section()
            log.debug('</item>')

        elif tag == 'channel':
            self.end_section()
            log.debug('</channel>')
            dump_channel(self.channel)

        elif self.cur_section():
            self.subj = None

    def data(self, data):
        if self.subj:
            log.debug("%s.%s" % ('.'.join(self.section_stack), self.subj))
            if self.cur_section() == 'comment':
                self.cmnt[self.subj] = data

            elif self.cur_section() == 'item':
                self.item[self.subj] = data

            elif self.cur_section() == 'channel':
                self.channel[self.subj] = data
            self.subj = None

    def close(self):
        return self.channel, self.items

    def start_section(self, what):
        self.section_stack.append(what)

    def end_section(self):
        if len(self.section_stack):
            self.section_stack.pop()

    def cur_section(self):
        try:
            return self.section_stack[-1]
        except:
            return None


if __name__ == '__main__':
    init_conf()
    init_logging(conf['verbose'])

    log.info("Parsing '%s'..." % os.path.basename(conf['source_file']))

    target = CustomParser()
    parser = XMLParser(target=target)
    parser.feed(open(conf['source_file']).read())

    log.info('Done')
