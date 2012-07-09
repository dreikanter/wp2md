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


log = logging.getLogger(__name__)
conf = {}


def init_conf():
    # TODO: Get it from args
    global conf
    conf['source_file'] = 'wordpress.xml'
    conf['dump_path'] = None
    conf['verbose'] = True
    conf['parse_date_fmt'] = "%a, %d %b %Y %H:%M:%S +0000"
    conf['date_fmt'] = "%Y/%m/%d %H:%M:%S"


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


def getxm(message, exception):
    """Returns annotated exception messge."""
    return ("%s: %s" % (message, str(exception))) if exception else message


def tag_name(name):
    return name[name.find('}') + 1:]


def dump(file_name, data):
    """Dumps a dictionary to YAML-like text file."""
    try:
        dir_path = os.path.dirname(os.path.abspath(file_name))
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        with codecs.open(file_name, 'w', 'utf-8') as f:
            content = None
            for field in data:
                if field == 'content':
                    content = data[field]
                else:
                    f.write(u"%s: %s\n" % (unicode(field), unicode(data[field])))
            if content:
                f.write('\n' + content)
    except Exception as e:
        log.error("Error saving data to '%s'" % file_name)
        log.debug(e)


def get_dump_path(file_name, subdir=''):
    """Generates dump directory absolute path."""
    explicit = conf['dump_path']
    result = explicit or '{date}_{source}'
    result = result.format(date=time.strftime('%Y-%m-%d'),
                           source=os.path.basename(conf['source_file']))
    return os.path.join(os.path.abspath(result), subdir, file_name)


def parse_date(date_str, default=None):
    """Parses date string according to parse_date_fmt configuration parameter.
    Returns parsed value in date_fmt format or default if parsing was filed."""
    try:
        result = time.strptime(date_str, conf['parse_date_fmt'])
    except:
        msg = "Error parsing date string '%s'. Using default value." % date_str
        log.debug(msg)
        result = default

    return time.strftime(conf['date_fmt'], result) if result else ''


def dump_channel(data):
    file_name = get_dump_path('blog.txt')
    log.info("Dumping channel data to '%s'..." % file_name)

    fields = WHAT2SAVE['channel']
    processed = {field: data.get(field, None) for field in fields}

    pub_date = data.get('pubDate', None)
    processed['export_date'] = parse_date(pub_date, time.gmtime())

    dump(file_name, processed)


def dump_item(data):
    log.info("Dumping item...")
    # TODO: ...


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
