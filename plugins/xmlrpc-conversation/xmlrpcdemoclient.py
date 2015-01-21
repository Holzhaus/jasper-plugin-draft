#!/usr/bin/env python2
import xmlrpclib

s = xmlrpclib.ServerProxy('http://localhost:8765')
print("Available Methods: %r" % s.system.listMethods())
print("Available Commands: %r" % s.get_command_phrases())
for answer in s.get_answers():
    print("JASPER: %s", answer)
while True:
    phrase = raw_input("YOU: ")
    s.handle(phrase)
    for answer in s.get_answers():
        print("JASPER: %s" % answer)
