# -*- coding: utf-8 -*-
import urllib
import constants


def detect_encoding(string):
    """ returns byte char string codification
    """
    for codec in constants.CODECS:
        try:
            string.decode(codec)
            return codec
        except:
            pass
    raise Exception("The string codec is unknown")


def to_string(string, dst_codec='utf-8'):
    """ returns a byte char string encoded with dst_codec
    """
    if isinstance(string, unicode):
        the_string = string.encode(dst_codec)
        return the_string
    if isinstance(string, str):
        src_codec = detect_encoding(string)
        if src_codec != dst_codec:
            the_string = unicode(string, src_codec).encode(dst_codec)
            return the_string
        else:
            return string
    raise Exception("the string is of type: " + str(type(string)))


def to_unicode(string):
    """ returns a wide char unicode string
    """
    if isinstance(string, str):
        src_codec = detect_encoding(string)
        return unicode(string, src_codec)
    if isinstance(string, unicode):
        return string
    raise Exception("the string is of type: " + str(type(string)))


def to_string_url(string):
    """ returns url encoding string in byte char
    """
    return urllib.quote_plus(to_string(string))


if __name__ == "__main__":
    print "hi!"
    string = u"你好表"
    print to_string(string)
    print to_string(to_unicode(to_string(string)))
    print "bye!"
