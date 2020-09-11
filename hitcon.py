import requests
import bs4
import re
import json

def download(force=False):
    try:
        if not force:
            with open('hitcon-agenda.html', 'rb') as fp:
                return fp.read()
    except OSError:
        pass

    ret = requests.get('https://hitcon.org/2020/agenda/').content
    with open('hitcon-agenda.html', 'wb') as fp:
        fp.write(ret)
    return ret

def get_doc(force=False):
    return bs4.BeautifulSoup(download(force), 'html5lib')

def get_sessions(force=False):
    doc = get_doc(force)

    times = {
        re.search(r'grid-row-start:\s*([\w-]+)', tag.get('style', ''))[1]: tag.text.strip().split(' - ')[0]
        for tag in
        doc.select('.ccip-app.ccip-session-block.time-block')
        if tag.text.strip() and 'grid-row-start:' in tag.get('style', '')
    }

    times['T173000'] = '17:30'
    times['T181000'] = '18:10'

    aio = {
        'sessions': [],
        'speakers': [],
        'session_types': [],
        'rooms': [],
        'tags': [],
    }

    idx = 0

    atags = {}
    arooms = {}
    asession_types = {}
    aspeakers = {}

    '''
    special keys:
        - speakers
            - avatar
        - sessions
            - type: id
            - room: id
            - start: date
            - end: date
            - language: str
            - zh: dict
                - title: str
                - description: str
            - en: dict
                - title: str
                - description: str
            - speakers: list[id]
            - tags: list[id]
            - co_write: link or null
            - slide: link or null
            - record: link or null
    '''

    def inject(val, lst, dct, defaults={}):
        nonlocal idx
        if val in dct:
            return dct[val]['id']

        dct[val] = {
            'id': 'obj%d' % idx,
            'zh': {'name': val},
            'en': {'name': val},
        }
        dct[val].update(defaults)
        lst.append(dct[val])
        idx += 1
        return dct[val]['id']

    def fmtdate(day, time):
        m, d = day.split('/')
        M, S = time.split(':')
        return '2020-%.2d-%.2dT%.2d:%.2d:00+08:00' % (
                int(m, 10), int(d, 10),
                int(M, 10), int(S, 10)
                )

    for h2 in doc.select('.content__default div .tabs .tab-pane > h2'):
        container = h2.parent
        day = h2.text.strip()

        for session in container.select('.ccip-app.ccip-session-block.session-block'):
            title = session.select_one('.ccip-session-title').text.strip()
            tags = [ i.text.strip() for i in session.select('.ccip-session-tags span') ]
            speakers = [ i.text.strip() for i in session.select('.ccip-session-speakers span') ]
            time = re.search(r'grid-row-start:\s*(?P<begin>T\w+);.*grid-row-end:\s*(?P<end>T\w+)', session.get('style', ''))
            room = re.search(r'grid-column-start:\s*(\w+)', session.get('style', ''))[1]
            link = [i.get('href') for i in session.select('a') if i.get('href')]

            if time:
                begin_at, end_at = times[time['begin']], times[time['end']]

            # blob = {'title': title,
            #         'room': room,
            #         'tags': tags,
            #         'speakers': speakers,
            #         'time': '%s %s - %s' % (day, begin_at, end_at),
            #         'links': link
            #         }

            session_blob = {
                'id': link[0] or ('%s--%s' % (room, blob['time'])),
                'type': inject('Talk', aio['session_types'], asession_types),
                'room': inject(room, aio['rooms'], arooms),
                'start': fmtdate(day, begin_at),
                'end': fmtdate(day, end_at),
                'language': 'Unknown', # FIXME: value?
                'zh': {
                    'title': title,
                    'description': '-',
                },
                'en': {
                    'title': title,
                    'description': '-',
                },
                'speakers': [
                    inject(speaker, aio['speakers'], aspeakers, {
                        'en': {
                            'name': speaker,
                            'bio': ''
                            },
                        'zh': {
                            'name': speaker,
                            'bio': ''
                            }
                        })
                    for speaker in speakers
                ],
                'tags': [
                    inject(tag, aio['tags'], atags, {
                        'zh': {'name': tag},
                        'en': {'name': tag},
                        })
                    for tag in tags
                ],
                'co_write': None, # FIXME: nullable?
                'slide': None,
                'record': None,
                }

            aio['sessions'].append(session_blob)

    return aio

if __name__ == '__main__':
    print(json.dumps(get_sessions(True)))
