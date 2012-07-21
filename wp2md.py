#!/usr/bin/env python
"""Export Wordpress XML dump to markdown files"""

import argparse
import codecs
import datetime
import html2text
import logging
import markdown
import os.path
import re
import sys
import time
import traceback
from xml.etree.ElementTree import XMLParser


# XML elements to save (starred ones are additional fields generated during
# export data processing)
WHAT2SAVE = {
    'channel': [
        'title',
        'description',
        'author_display_name',
        'author_login',
        'author_email',
        'base_site_url',
        'base_blog_url',
        'export_date',          # Generated: data export timestamp
        'content',              # Generated: items list
        # 'link',
        # 'language',
    ],
    'item': [
        'title',
        'link',
        'creator',
        'description',
        'post_id',
        'post_date',
        'post_date_gmt',
        'comment_status',
        'post_name',
        'status',
        'excerpt',
        'content',              # Generated: item content
        'comments',             # Generated: comments lis
        # 'guid',
        # 'is_sticky',
        # 'menu_order',
        # 'ping_status',
        # 'post_parent',
        # 'post_password',
        # 'post_type',
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
        # 'comment_parent',
        # 'comment_user_id',
    ],
}

log = logging.getLogger(__name__)
conf = {}
stats = {
    'pages': 0,
    'posts': 0,
    'comments': 0,
}


# Configuration and logging

def init():
    global conf
    args = parse_args()
    init_logging(args.l, args.v)
    conf = {
        'source_file': args.source,
        'dump_path': args.d,
        'verbose': args.v,
        'parse_date_fmt': args.u,
        'post_date_fmt': args.o,
        'date_fmt': args.f,
        'file_date_fmt': args.p,
        'log_file': args.l,
        'md_input': args.m,
        'max_name_len': args.n
    }

    limit = conf['max_name_len']
    if limit < 0 or limit > 100:
        log.warn('Bad post name length limitation value. Using default.')


def init_logging(log_file, verbose):
    try:
        global log
        log.setLevel(logging.DEBUG)
        log_level = logging.DEBUG if verbose else logging.INFO

        channel = logging.StreamHandler()
        channel.setLevel(log_level)
        fmt = '%(message)s'
        channel.setFormatter(logging.Formatter(fmt, '%H:%M:%S'))
        log.addHandler(channel)

        if log_file:
            channel = logging.FileHandler(log_file)
            channel.setLevel(logging.DEBUG)
            fmt = '%(asctime)s %(levelname)s: %(message)s'
            channel.setFormatter(logging.Formatter(fmt, '%H:%M:%S'))
            log.addHandler(channel)

    except Exception as e:
        log.debug(traceback.format_exc())
        raise Exception(getxm('Logging initialization failed', e))


def parse_args():
    desc = __doc__.split('\n\n')[0]
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        '-v',
        action='store_true',
        default=False,
        help='verbose logging')
    parser.add_argument(
        '-l',
        action='store',
        metavar='FILE',
        default=None,
        help='log to file')
    parser.add_argument(
        '-d',
        action='store',
        metavar='PATH',
        default=None,
        help='destination path for generated files')
    parser.add_argument(
        '-u',
        action='store',
        metavar='FMT',
        default="%a, %d %b %Y %H:%M:%S +0000",
        help='<pubDate> date/time parsing format')
    parser.add_argument(
        '-o',
        action='store',
        metavar='FMT',
        default="%Y %H:%M:%S",
        help='<wp:post_date> and <wp:post_date_gmt> parsing format')
    parser.add_argument(
        '-f',
        action='store',
        metavar='FMT',
        default="%Y-%m-%d %H:%M:%S",
        help='date/time fields format for exported data')
    parser.add_argument(
        '-p',
        action='store',
        metavar='FMT',
        default="%Y%m%d",
        help='date prefix format for generated files')
    parser.add_argument(
        '-m',
        action='store_true',
        default=False,
        help='preprocess content with Markdown (helpful for MD input)')
    parser.add_argument(
        '-n',
        action='store',
        metavar='LEN',
        default=32,
        help='post name (slug) length limit for file naming')
    parser.add_argument(
        'source',
        action='store',
        help='source XML dump exported from Wordpress')
    return parser.parse_args(sys.argv[1:])


# Helpers

def getxm(message, exception):
    """Returns annotated exception messge."""
    return ("%s: %s" % (message, str(exception))) if exception else message


def tag_name(name):
    """Removes expanded namespace from tag name."""
    result = name[name.find('}') + 1:]
    if result == 'encoded':
        if name.find('/content/') > -1:
            result = 'content'
        elif name.find('/excerpt/') > -1:
            result = 'excerpt'
    return result


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
    max_name_len = 20
    if len(name) > max_name_len:
        name = name[:max_name_len] + '_'

    try:
        pub_date = time.strftime(conf['file_date_fmt'], data['post_date'])
    except:
        pub_date = None

    return '_'.join(filter(bool, [pub_date, pid, name])) + '.md'


def html2md(html):
    h2t = html2text.HTML2Text()
    h2t.unicode_snob = True
    return h2t.handle(html).strip()


def stopwatch_set():
    """Starts stopwatch timer."""
    globals()['_stopwatch_start_time'] = datetime.datetime.now()


def stopwatch_get():
    """Returns string representation for elapsed time since last
    stopwatch_set() call."""
    delta = datetime.datetime.now() - globals().get('_stopwatch_start_time', 0)
    delta = str(delta).strip('0:')
    return ('0' + delta) if delta[0] == '.' else delta


def statplusplus(field, value=1):
    global stats
    if field in stats:
        stats[field] += value
    else:
        raise ValueError("Illegal name for stats field")


# Data dumping

def dump(file_name, data, order):
    """Dumps a dictionary to YAML-like text file."""
    try:
        dir_path = os.path.dirname(os.path.abspath(file_name))
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        with codecs.open(file_name, 'w', 'utf-8') as f:
            extras = {}
            for field in filter(lambda x: x in data, [item for item in order]):
                if field in ['content', 'comments', 'excerpt']:
                    # Fields for non-standard processing
                    extras[field] = data[field]
                else:
                    if type(data[field]) == time.struct_time:
                        value = time.strftime(conf['date_fmt'], data[field])
                    else:
                        value = data[field] or ''
                    f.write(u"%s: %s\n" % (unicode(field), unicode(value)))

            if extras:
                excerpt = extras.get('excerpt', '')
                excerpt = excerpt and '<!--%s-->' % excerpt

                content = extras.get('content', '')
                if conf['md_input']:
                    # Using new MD instance works 3x faster than
                    # reusing existing one for some reason
                    md = markdown.Markdown(extensions=[])
                    content = md.convert(content)
                content = html2md(content)

                comments = html2md(gen_comments(extras.get('comments', [])))
                extras = filter(None, [excerpt, content, comments])
                f.write('\n' + '\n\n'.join(extras))

    except Exception as e:
        log.error("Error saving data to '%s'" % (file_name))
        log.debug(e)


def gen_comments(comments):
    """Generates a MD-formatted plain-text comments from parsed data."""
    result = u''
    for comment in comments:
        try:
            approved = comment['comment_approved'] == '1'
            pingback = comment.get('comment_type', '').lower() == 'pingback'
            if approved and not pingback:
                cmfmt = u"**[{author}](#{id} \"{timestamp}\"):** {content}\n\n"
                content = html2md(comment['comment_content'])
                result += cmfmt.format(
                        id=comment['comment_id'],
                        timestamp=comment['comment_date'],
                        author=comment['comment_author'],
                        content=content
                    )

        except:
            # Ignore malformed data
            pass

    return result and (u"## Comments\n\n" + result)


def dump_channel(meta, items):
    """Dumps RSS channel metadata and items index."""
    file_name = get_dump_path('index.txt')
    log.info("Dumping the index to '%s'" % file_name)
    fields = WHAT2SAVE['channel']
    meta = {field: meta.get(field, None) for field in fields}

    # Append export_date
    pub_date = meta.get('pubDate', None)
    format = conf['parse_date_fmt']
    meta['export_date'] = parse_date(pub_date, format, time.gmtime())

    # Append table of contents
    meta['content'] = generate_toc(meta, items)

    dump(file_name, meta, fields)


def dump_item(data):
    """Dumps RSS channel item."""
    global stats
    item_type = data.get('post_type', None)
    item_type = {'post': 'posts', 'page': 'pages'}.get(item_type, None)
    if not item_type:
        return

    fields = WHAT2SAVE['item']
    meta = {}
    for field in fields:
        meta[field] = data.get(field, '')

    # Post date
    format = conf['date_fmt']
    value = meta.get('post_date', None)
    meta['post_date'] = value and parse_date(value, format, None)

    # Post date GMT
    value = meta.get('post_date_gmt', None)
    meta['post_date_gmt'] = value and parse_date(value, format, None)

    file_name = get_post_filename(meta)
    log.info("Dumping '%s\%s'" % (item_type, file_name))
    dump(get_dump_path(file_name, item_type), meta, fields)

    statplusplus(item_type)
    if 'comments' in data:
        statplusplus('comments', len(data['comments']))


def get_toc_sect(item):
    if item['post_type'] == 'page':
        return 'page'

    pub_date = parse_date(item.get('post_date', None), conf['date_fmt'])
    if type(pub_date) == time.struct_time:
        return pub_date[0]

    return None


def generate_toc(meta, items):
    content = u"# {title}\n\n{description}\n\n".format(**meta)
    for item in items:
        content += u"* [{title}]({link} \"{post_date}\")\n".format(**item)
    return content


# The Parser

class CustomParser:
    def __init__(self):
        self.section_stack = []
        self.channel = {}
        self.items = []
        self.item = None
        self.cmnt = None
        self.subj = None

    def start(self, tag, attrib):
        tag = tag_name(tag)
        if tag == 'channel':
            self.start_section('channel')

        elif tag == 'item':
            self.item = {'comments': []}
            self.start_section('item')

        elif self.item and tag == 'comment':
            self.cmnt = {}
            self.start_section('comment')

        elif self.cur_section():
            self.subj = tag

        else:
            self.subj = None

    def end(self, tag):
        tag = tag_name(tag)
        if tag == 'comment' and self.cur_section() == 'comment':
            self.end_section()
            self.item['comments'].append(self.cmnt)
            self.cmnt = None

        elif tag == 'item' and self.cur_section() == 'item':
            self.end_section()
            dump_item(self.item)
            self.store_item_info()
            self.item = None

        elif tag == 'channel':
            self.end_section()
            dump_channel(self.channel, self.items)

        elif self.cur_section():
            self.subj = None

    def data(self, data):
        if self.subj:
            if self.cur_section() == 'comment':
                self.cmnt[self.subj] = data

            elif self.cur_section() == 'item':
                self.item[self.subj] = data

            elif self.cur_section() == 'channel':
                self.channel[self.subj] = data
            self.subj = None

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

    def store_item_info(self):
        # TODO: Drop unused
        post_type = self.item.get('post_type', '').lower()
        if not post_type in ['post', 'page']:
            return

        info_fields = [
            'title',
            'link',
            'creator',
            'description',
            'post_id',
            'post_date',
            'post_type',
            'post_date_gmt',
            'comment_status',
            'post_name',
            'status',
        ]

        self.items.append({})
        for field in info_fields:
            self.items[-1][field] = self.item.get(field, None)


if __name__ == '__main__':
    init()
    log.info("Parsing '%s'..." % os.path.basename(conf['source_file']))

    stopwatch_set()
    target = CustomParser()
    parser = XMLParser(target=target)
    parser.feed(open(conf['source_file']).read())

    log.info('')
    totals = ', '.join([("%s: %d" % (s, stats[s])) for s in stats])
    log.info('Totals: ' + totals)
    log.info('Elapsed time: ' + stopwatch_get())
