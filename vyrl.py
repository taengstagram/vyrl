# -*- coding: utf-8 -*-
import cmd
from Crypto.Random.random import randint
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_v1_5
import base64
import hashlib
import urllib
import urllib2
import json
import datetime
import re
import os
import codecs
import sys
import webbrowser

__version__ = 0.1
__author__ = 'thegoguma'


FRNZ_PUB_KEY = \
"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2ZdL8NRV1phe61uvYWPR
yQypKbIXO9v/NeAYCWjZ29rawJIeHDdajKArVt7acaA+J0CR5eNt+PaGMwjsOC93
As1FZRQj73rO8zZbOBm9UMiaMK8ZF33ygYyxzsiML2jO1FUSqt4q85wxmfVGxv4F
I85/B8ZagSnqSZqC83lxxUYFjWgbNGooHgIzFAM2BF/4czkjr7cSzI6Qf+uuAKfS
Utdykrum26hyHP8nip3066YHPFHdeVrY22hCEQjyZF9Rs9sApvq51zkkxJtpCZgB
Giwj9BPuUtmkgn3+2H59ASIykVVkdNa9vZbfOQOsmg04EbQctOlcso2lImBsWFyO
DwIDAQAB
-----END PUBLIC KEY-----"""

BASE_URL = 'http://api.vyrl.com:8082/ko/'
HEADERS = {'User-Agent': 'Dalvik/1.6.0 (Linux; U; Android 4.2.2)'}
RANDOM_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
SHORTCUT_ACCOUNTS = [
    {'user_id': 54807, 'nickname': 'SMTOWN'},
    {'user_id': 54808, 'nickname': 'SMTOWN_JP'},
    {'user_id': 54809, 'nickname': 'SMTOWN_CN'},
    {'user_id': 54810, 'nickname': 'SMTOWN_EN'},
    {'user_id': 54782, 'nickname': 'BoA'},
    {'user_id': 54783, 'nickname': 'BoA_JP'},
    {'user_id': 54784, 'nickname': 'BoA_CN'},
    {'user_id': 54785, 'nickname': 'BoA_EN'},
    {'user_id': 54799, 'nickname': '동방신기'},
    {'user_id': 54800, 'nickname': '東方神起'},
    {'user_id': 54801, 'nickname': '东方神起'},
    {'user_id': 54802, 'nickname': 'TVXQ'},
    {'user_id': 54774, 'nickname': 'SUPERJUNIOR'},
    {'user_id': 54775, 'nickname': 'SUPERJUNIOR_JP'},
    {'user_id': 54776, 'nickname': 'SUPERJUNIOR_CN'},
    {'user_id': 54777, 'nickname': 'SUPERJUNIOR_EN'},
    {'user_id': 54803, 'nickname': '소녀시대'},
    {'user_id': 54804, 'nickname': '少女時代'},
    {'user_id': 54805, 'nickname': '少女时代'},
    {'user_id': 54806, 'nickname': 'GirlsGeneration'},
    {'user_id': 54786, 'nickname': 'SHINee'},
    {'user_id': 54787, 'nickname': 'SHINee_JP'},
    {'user_id': 54788, 'nickname': 'SHINee_CN'},
    {'user_id': 54789, 'nickname': 'SHINee_EN'},
    {'user_id': 54790, 'nickname': 'fx'},
    {'user_id': 54791, 'nickname': 'fx_JP'},
    {'user_id': 54792, 'nickname': 'fx_CN'},
    {'user_id': 54793, 'nickname': 'fx_EN'},
    {'user_id': 54794, 'nickname': 'EXO'},
    {'user_id': 54795, 'nickname': 'EXO_JP'},
    {'user_id': 54796, 'nickname': 'EXO_CN'},
    {'user_id': 54797, 'nickname': 'EXO_EN'},
    {'user_id': 54778, 'nickname': 'RedVelvet'},
    {'user_id': 54789, 'nickname': 'RedVelvet_JP'},
    {'user_id': 54780, 'nickname': 'RedVelvet_CN'},
    {'user_id': 54781, 'nickname': 'RedVelvet_EN'}]

HORIZONTAL_LINE = '------------------------------------------------------------------------'
TEMP_FOLDER = 'vyrl_temp'
INTRO = """
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
This is a simple command line app to view Vyrl updates.
At the prompt, enter "?" or "help" to see the commands available.

To quit, enter "quit" or simply press control+D at the prompt.

Have fun!
-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""

PAGE_TEMPLATE = """
<html>
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/bootstrap/3.3.5/css/bootstrap.min.css">
<style>img { max-width: 100%% } body { padding-top: 2em; }</style>
</head>
<body><div class=container><div class=col-md-8>
%(content)s
</div></div>
</body></html>
"""
MAGAZINE_POST_TYPE = 3
PER_PAGE = 20   # doesn't seem to be followed, fixed at 20 on server side?


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Vyrl(cmd.Cmd):
    """A simple console application to view Vyrl posts"""

    intro = INTRO

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = bcolors.BOLD + '✌️ Vyrl > ' + bcolors.ENDC
        self.users = SHORTCUT_ACCOUNTS

    @staticmethod
    def _generate_random_string(string_len):
        output = ''
        for i in range(0, string_len):
            output += RANDOM_ALPHABET[randint(0, len(RANDOM_ALPHABET) - 1)]
        return output

    @staticmethod
    def _pkcs5_pad(s):
        return s + (AES.block_size - len(s) % AES.block_size) * chr(AES.block_size - len(s) % AES.block_size)

    @staticmethod
    def _clean_html(content):
        content = re.sub(r'\sstyle="[^"]+"', '', content)
        content = re.sub(r'<a[^<>]*\shref="javascript[^"]+"[^<>]*>([^<>]+)</a>', '\g<1>', content)
        content = re.sub(r'<html[^<>]*>.+<body[^<>]*>(.+)</body></html>', '\g<1>', content,
                         flags=re.MULTILINE|re.DOTALL)
        content = re.sub(r'(</?span>)', '', content)
        return content

    @staticmethod
    def _color_term(text, color, reset_color=bcolors.ENDC):
        return color + text + reset_color

    @staticmethod
    def cleanup():
        if not os.path.exists(TEMP_FOLDER):
            return
        for root, dirs, files in os.walk(TEMP_FOLDER, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(TEMP_FOLDER)

    def _call_api(self, endpoint, params):
        m = hashlib.md5()
        m.update(json.dumps(params, sort_keys=True))

        iv = self._generate_random_string(AES.block_size)
        pwk = self._generate_random_string(32)

        pub_key = RSA.importKey(FRNZ_PUB_KEY)
        pkcs115_cipher = PKCS1_v1_5.new(pub_key)
        aes_cipher = AES.new(pwk, AES.MODE_CBC, iv)

        url = BASE_URL + endpoint
        encrypted_params = aes_cipher.encrypt(self._pkcs5_pad(json.dumps(params)))
        encrypted_text = base64.b64encode(encrypted_params)

        post_params = {
            'encrypt_text': encrypted_text,
            'password': base64.b64encode(pkcs115_cipher.encrypt(pwk)),
            'iv': base64.b64encode(pkcs115_cipher.encrypt(iv)),
        }
        data = urllib.urlencode(post_params)
        req = urllib2.Request(url, data, headers=HEADERS)
        response = urllib2.urlopen(req, timeout=15)
        json_response = json.load(response)
        return json_response

    def preloop(self):
        print 'Initialising. Please wait...'
        r = self._call_api(
            'statuses/popular',
            {'user_id': '54844', 'page': 1, 'limit': PER_PAGE, 'my_user_id': '1'})
        users = r.get('result_set', {}).get('users')
        self.users.extend([{'user_id': u['user_id'], 'nickname': u['nickname']} for u in users])
        if not os.path.exists(TEMP_FOLDER):
            os.makedirs(TEMP_FOLDER)

    def postloop(self):
        self.cleanup()
        print '\n--- ✌ Bye! ✌ ---\n'

    def do_exit(self, line):
        """Quit this program"""
        return True

    def do_accounts(self, line):
        """View the list of channels and popular accounts"""
        for u in self.users:
            print '%(user_id)s \t %(nickname)s' % {
                'user_id': self._color_term(str(u['user_id']), bcolors.HEADER), 'nickname': u['nickname']}
        print '\nTo view account, use the "user" command, e.g. user %s' % self.users[-2]['user_id']

    def do_user(self, params):
        """View account [user_id]
        Displays the 20 latest posts from the user_id given.
        Example:
            user 54807"""
        args = params.split(' ')
        selected_user_id = args[0]
        if not selected_user_id:
            print 'Please include a user ID, e.g. user ' + self._color_term('54807', bcolors.UNDERLINE)
            return

        params = {'user_id': selected_user_id, 'page': 1, 'limit': PER_PAGE, 'my_user_id': '1'}

        try:
            if len(args) >= 2:
                min_post_id = args[1]
                if min_post_id:
                    params['min_post_id'] = min_post_id
            r = self._call_api('statuses/user_timeline', params)
            posts = r.get('result_set', [])

            if not posts:
                print 'No posts found.'
                return

            for p in reversed(posts):
                dt = datetime.datetime.strptime(p.get('created_at'), "%Y-%m-%dT%H:%M:%S+0900")
                print '\n', 'PostID:', bcolors.HEADER + p['post_id'] + bcolors.ENDC, '\t\t', dt
                print HORIZONTAL_LINE
                if p['post_type'] == MAGAZINE_POST_TYPE:
                    print p['title']
                else:
                    print p['content']
                print self._color_term(p['medias'][0]['image']['url'], bcolors.OKGREEN)

            print bcolors.ENDC
            print 'Viewing %s posts.' % len(posts)
            print '\nTo view a post in the browser, use the "open" command, e.g. open %s' % posts[0]['post_id']
            print 'To view a post here, use the "post" command, e.g. post %s' % posts[0]['post_id']
            if len(posts) >= PER_PAGE:
                print '\nTo view the next page of posts, enter: user %s %s' % (selected_user_id, posts[-1]['post_id'])

        except urllib2.HTTPError as http_ex:
            print 'Error retrieving user posts: %s' % self._color_term(str(http_ex), bcolors.WARNING)

    def do_post(self, params):
        """View post [post_id]
        Displays the post.
        Example:
            post 567a72024624733a048b4589"""
        args = params.split(' ')
        selected_post_id = args[0]
        if not selected_post_id:
            print 'Please include a post ID, e.g. post ' + self._color_term(
                '567a72024624733a048b4589', bcolors.UNDERLINE)
            return

        try:
            r = self._call_api(
                'statuses/detail',
                {'post_id': selected_post_id, 'my_user_id': '1', 'language': 'en'})
            post = r.get('result_set', {})

            if not post:
                print 'Unable to retrieve post: %s' % selected_post_id
                return

            dt = datetime.datetime.strptime(post.get('created_at'), "%Y-%m-%dT%H:%M:%S+0900")
            # strip html to make it marginally readable in console
            content = re.sub('<[^<]+?>', '', post.get('content'))
            user_id = post.get('user', {}).get('user_id')
            nickname = post.get('user', {}).get('nickname')

            inline_medias = re.findall(
                r'(https?://[^\s]+?\.(?:gif|jpg|mp4|png))', post.get('content', ''),
                flags=re.MULTILINE)

            print self._color_term('Date: %s \t\t From: %s (%s)' % (dt, nickname, user_id), bcolors.HEADER)
            print self._color_term('Post ID: %s' % selected_post_id, bcolors.HEADER)
            print HORIZONTAL_LINE
            print content
            print '\n' + self._color_term('Image Links:', bcolors.OKGREEN)
            if inline_medias:
                for m in inline_medias:
                    print self._color_term('  * ' + m, bcolors.OKGREEN)
            else:
                for m in post.get('medias', []):
                    print self._color_term('  * ' + m.get('image', {}).get('url'), bcolors.OKGREEN)

            if post.get('post_type') == MAGAZINE_POST_TYPE:
                print 'To view this post in the browser, enter "open %s"' % selected_post_id
        except urllib2.HTTPError as http_ex:
            print 'Error retrieving post: %s' % self._color_term(str(http_ex), bcolors.WARNING)

    def do_open(self, params):
        """Open post [post_id]
        Opens the post in default browser.
        Example:
            open 567a72024624733a048b4589"""

        args = params.split(' ')
        selected_post_id = args[0]
        if not selected_post_id:
            print 'Please include a post ID, e.g. open ' + self._color_term(
                '567a72024624733a048b4589', bcolors.UNDERLINE)
            return

        try:
            r = self._call_api(
                'statuses/detail',
                {'post_id': selected_post_id, 'my_user_id': '1', 'language': 'en'})
            post = r.get('result_set', {})

            if not post:
                print 'Unable to retrieve post: %s' % selected_post_id
                return

            if post.get('post_type') == MAGAZINE_POST_TYPE:
                # Strip superfluous tags for "Magazine" type post
                contents = self._clean_html(post.get('content'))
            else:
                contents = '<p>%(content)s</p><img src="%(img)s">' % {
                    'img': post.get('medias', [])[0].get('image', {}).get('url'),
                    'content': post.get('content')}
            html = PAGE_TEMPLATE % {'content': contents}
            output_filename = os.path.join(TEMP_FOLDER, '%s.html' % selected_post_id)
            with codecs.open(output_filename, 'wb', 'utf-8') as output:
                output.write(html)

            webbrowser.open('file://' + os.path.abspath(output_filename), new=2)
        except urllib2.HTTPError as http_ex:
            print 'Error retrieving post: %s' % self._color_term(str(http_ex), bcolors.WARNING)

    do_a = do_accounts
    do_u = do_user
    do_p = do_post
    do_o = do_open
    do_q = do_exit
    do_quit = do_exit
    do_EOF = do_exit

if __name__ == '__main__':
    try:
        Vyrl().cmdloop()
    except (KeyboardInterrupt):
        Vyrl.cleanup()
        print ''
        sys.exit(0)
    except Exception as e:
        Vyrl.cleanup()
        print 'Unexpected error:', self._color_term(str(e), bcolors.FAIL)
