#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    import http.client as httplib
    from urllib.parse import urlencode
except ImportError:
    import httplib
    from urllib import urlencode

import socket

from sets import Set

from .exceptions import (
    NERError,
)

from .utils import (
    tcpip4_socket,
    http_connection,
)


class NER(object):
    """Wrapper for server-based Stanford NER tagger."""

    def tag_text(self, text):
        pass

    def get_tagged_text(self, text):
        return self.tag_text(text)

    def get_entities(self, text):
        """

        """
        tagged_text = self.tag_text(text)
        result = {
            'PERS': [],
            'LOC': [],
            'ORG': []
        }
        for word in tagged_text.split():
            spilited = word.split('/')
            tag = spilited[-1]
            if tag != u'O':
                tag_base, tag_type = tag.split('-')
                text = "/".join(spilited[:-1])
                if tag_base == 'B':
                    result[tag_type].append(text)
                if tag_base == 'I':
                    result[tag_type][-1] += ' %s' % text
        for k in result:
            result[k] = list(Set(result[k]))

        return result


class SocketNER(NER):
    """Stanford NER over simple TCP/IP socket."""

    def __init__(self, host='localhost', port=1234, output_format='inlineXML'):
        if output_format not in ('slashTags', 'xml', 'inlineXML'):
            raise ValueError('Output format %s is invalid.' % output_format)
        self.host = host
        self.port = port
        self.oformat = output_format

    def tag_text(self, text):
        """Tag the text with proper named entities token-by-token.

        :param text: raw text string to tag
        :returns: tagged text in given output format
        """
        for s in ('\f', '\n', '\r', '\t', '\v'): #strip whitespaces
            text = text.replace(s, '')
        text += '\n' #ensure end-of-line
        with tcpip4_socket(self.host, self.port) as s:
            if not isinstance(text, bytes):
                text = text.encode('utf-8')
            s.sendall(text)
            tagged_text = s.recv(10*len(text))
        return tagged_text.decode('utf-8')


class HttpNER(NER):
    """Stanford NER using HTTP protocol."""

    def __init__(self, host='localhost', port=1234, location='/stanford-ner/ner',
            classifier=None, output_format='inlineXML', preserve_spacing=True):
        if output_format not in ('slashTags', 'xml', 'inlineXML'):
            raise ValueError('Output format %s is invalid.' % output_format)
        self.host = host
        self.port = port
        self.location = location
        self.oformat = output_format
        self.classifier = classifier
        self.spacing = preserve_spacing

    def tag_text(self, text):
        """Tag the text with proper named entities token-by-token.

        :param text: raw text strig to tag
        :returns: tagged text in given output format
        """
        for s in ('\f', '\n', '\r', '\t', '\v'): #strip whitespaces
            text = text.replace(s, '')
        text += '\n' #ensure end-of-line
        with http_connection(self.host, self.port) as c:
            headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept' : 'text/plain'}
            if self.classifier:
                params = urlencode(
                    {'input': text, 'outputFormat': self.oformat,
                    'preserveSpacing': self.spacing,
                    'classifier': self.classifier})
            else:
                params = urlencode(
                    {'input': text, 'outputFormat': self.oformat,
                    'preserveSpacing': self.spacing})
            try:
                c.request('POST', self.location, params, headers)
                response = c.getresponse()
                tagged_text = response.read()
            except httplib.HTTPException as e:
                print("Failed to post HTTP request.")
                raise e
        return tagged_text


