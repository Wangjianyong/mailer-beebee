#!/usr/bin/python
import re
import sys
import time
import mailer

MailHost = {"gmail": "smtp.gmail.com",
			"163": "smtp.163.com",
			"126": "smtp.126.com",
			"sina": "smtp.sina.com",
			"sohu": "smtp.sohu.com"}
MailPort = {"gmail": 587,
			"163": 25,
			"126": 25,
			"sina": 587,
			"sohu": 25}

if __name__ == '__main__':
    host = MailHost['sina']
    port = MailPort['sina']
    
    #FIXME TLS or SSL
    con = mailer.Mailer(host, port, use_tls=False, usr="wjy5095844@sina.com", pwd="wjy15051870608")
    if con.connect(debug=True) is False:
        print "Login failed."
    else:
        print "Login succeed."
