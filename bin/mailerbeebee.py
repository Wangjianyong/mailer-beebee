#!/usr/bin/python

########################################################################
# File Name: mailerbeebee.py                                           #
#    > Author: Jianyong Wang                                           #
#    > Mail: jianywan@gmail.com                                        #
#    > Created Time: Wes sep 16 14:56:55 2015                          #
# a braodcast mailer implemented by python, using threadpool, mailer   # 
# and sqlalchemy.                                                      #
#                                                                      #
#Usage: python mailer.py [options] arg                                 #
#                                                                      #
#Options:                                                              #
#  -h, --help            show this help message and exit               #
#  -l MAILLINK, --link=MAILLINK                                        #
#                        mail content, a web link or a local file      #
#  -n THREADNUM, --num=THREADNUM                                       #
#                        threadpool size, default is 10                #
#  -t TOLIST, --to=TOLIST                                              #
#                        to list file location, a local file, default  #
#                        is ../src/fromlist.txt                        #
#  -f FROMLIST, --from=FROMLIST                                        #
#                        from list file location, a local file,        #
#                        default is ../src/fromlist.txt                #
#  -s MAILSUBJECT, --subject=MAILSUBJECT                               #
#                        mail subject                                  #
#  -m MAXSIZE, --max=MAXSIZE                                           #
#                        mail upper limit of a account,                #
#                        default is 10000                              #
#  -a ATTACHMENT, --attachment=ATTACHMENT                              #
#                        attachment in the mail                        #
#  -u SQLUSER, --username=SQLUSER                                      #
#                        username of mysql database                    #
#  -p SQLPWD, --password=SQLPWD                                        #
#                        password of mysql database                    #
#  -i SQLHOST, --ip=SQLHOST                                            #
#                        host of mysql database, default is localhost  #
#  -d SQLDBNAME, --database=SQLDBNAME                                  #
#                        name of mysql database, default is MailDB     #
########################################################################

import re
import sys
import time
import Queue
import urllib2
import smtplib
import datetime
import threading

sys.path.append('../')
from lib import mysql
from lib import mailer
from lib import threadpool

MailHost = {"gmail": "smtp.gmail.com",
			"163": "smtp.163.com",
			"126": "smtp.126.com",
			"sina": "smtp.sina.com",
			"sohu": "smtp.sohu.com",
			"qq": "smtp.qq.com"}
MailPort = {"gmail": 587,
			"163": 587,
			"126": 587,
			"sina": 587,
			"sohu": 587,
			"qq": 587}


class Reader(threading.Thread):
	def __init__(self, readertype, sendpool, FilePos=""):
		threading.Thread.__init__(self)
		self._readertype = readertype
		self._sendpool = sendpool
		self._fp = open(FilePos)
		self._dismissed = threading.Event()
		self._rcount = 0

	def run(self):
		while True:
			if self._dismissed.isSet():
				break
			line = self._fp.readline()
			if len(line) == 0:
				break
			#initialize the sender
			line = line.strip('\n')
			if self._readertype == "SEND":
				if validateEmail(line) is False:
					continue
				#accumlate receiver count
				self._rcount += 1
				request =  threadpool.WorkRequest(callable_=do_sendwork,
												callback=do_keepwork,
											 	kwds={"To": line})
				self._sendpool.putRequest(request)
			elif self._readertype == "INIT":
				str_split = line.split(' ')
				usr = str_split[0]
				pwd = str_split[1]
				if validateEmail(usr) is False:
					continue
				initrequest = threadpool.InitRequest(kwds={"usr": usr, "pwd": pwd},
													callable_=do_initwork)
				self._sendpool.putInitRequest(initrequest)
			else:
				break
		self._fp.close()
			
	def dismiss(self):
		self._fp.close()
		self._dismissed.set()


def validateEmail(address):
	if len(address) > 7:
		if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", address) != None:
			return True
	return False


def initmsg(m_to, m_from, m_subject):
	global content
	message = mailer.Message()
	message.To = m_to
	message.From = m_from
	message.Subject = m_subject
	message.Html = content
	return message


def inred(s):
	return"%s[31;2m%s%s[0m" % (chr(27), s, chr(27))


def do_initwork(tid, args=[], kwds={}):
	usr = kwds["usr"]
	pwd = kwds["pwd"]
	m = re.match("\w+@(\w+)\.com", usr)
	if m != None:
		hostname = m.group(1)
	else:
		return {"status": False}
	host = MailHost[hostname]
	port = MailPort[hostname]
		
	#FIXME TLS or SSL
	print "Thread #%s: try to connect with %s..." % (tid, usr)
	con = mailer.Mailer(host, port, use_tls=True, usr=usr, pwd=pwd)
	res = con.connect(debug=False)
	if res['status'] is False:
		error =  "Thread #%s: connect with %s failed, error: %r." % (tid, usr, res['error'])
		print inred(error) 
		return {"Status": False}
	print "Thread #%s: connect with %s succeed" % (tid, usr)
	return {"Status": True, "Con": con, "From": usr}


def do_sendwork(tid, args=[], kwds={}):
	"""A function called by each working thread"""
	"""retcode 250: message send OK"""
	"""452: Too many recipients received this hour"""
	"""502: Conection unexpectedly closed"""
	"""800: Unkown exception"""
	global s_count
	global mailsubject

	con = kwds["Con"]
	From = kwds["From"]
	To = kwds["To"]
	Status = True
	retcode = 250
	try:
		msg = initmsg(m_to=To, m_from=From, m_subject=mailsubject)
		con._send(con.server, msg)
		s_count += 1
		print "Thread #%s: mail to %s" % (tid, To)
	except smtplib.SMTPServerDisconnected, e:
		Status = False
		retcode = 502
		error = "Thread#%s: error: %r, reseting..." % (tid, e)
		print inred(error)
	except Exception, e:
		Status = False
		retcode = 800 
		error = "Thread #%s: mail to %s error: %r, reconnecting..." % (tid, To, e)
		print inred(error)
	Datetime = datetime.datetime.today()
	#here returns a dictionary & will be used in function do_keepwork
	return {"Status": Status, "To": To, "From": From, "Datetime": Datetime, "Retcode": retcode}


def do_keepwork(request, result):
	global maillink
	try:
		if isinstance(result, dict):
			DBHandle = result["dbhandle"]
			To = result["To"]
			From = result["From"]
			Datetime = result["Datetime"].strftime("%Y-%m-%d %H:%M:%S")
			Status = result["Status"]
			entry = mysql.Mail(To=To, From=From, Content=maillink, Datetime=Datetime, Status=Status)
			DBHandle.insert_database(entry)
			print "Keep 'To %s, Datetime %r, Status %r' done." % (To, Datetime, Status)
	except Exception, e:
			error = "Keep 'To %s, Datetime %r, Status %r' error %r." % (To, Datetime, Status, e)
			print inred(error)


if __name__ == '__main__':
	start = time.time()
	#Command Line Parser
	from optparse import OptionParser
	USAGE = 'Usage: python %prog [options] arg'
	parser = OptionParser(usage=USAGE)
	parser.add_option('-l', '--link', action='store', type='string', dest='maillink', default='../src/mailer.html',
						help="mail content, a web link or a local file")
	parser.add_option('-n', '--num', action='store', type='int', dest='threadnum', default=10,
						help="threadpool size, default is 10")
	parser.add_option('-t', '--to', action='store', type='string', dest='tolist', default='../src/tolist.txt',
						help="to list file location, a local file, default is ../src/fromlist.txt")
	parser.add_option('-f', '--from', action='store', type='string', dest='fromlist', default='../src/fromlist.txt',
						help="from list file location, a local file, default is ../src/fromlist.txt")
	parser.add_option('-s', '--subject', action='store', type='string', dest='mailsubject',
						help="mail subject")
	parser.add_option('-m', '--max', action='store', type='int', dest='maxsize', default=10000,
						help="mail upper limit of a account, default is 10000")
	parser.add_option('-a', '--attachment', action='store', type='string', dest='attachment',
						help="attachment in the mail")
	parser.add_option('-u', '--username', action='store', type='string', dest='sqluser', default='root',
						help="username of mysql database")
	parser.add_option('-p', '--password', action='store', type='string', dest='sqlpwd', default='wjy',
						help="password of mysql database")
	parser.add_option('-i', '--ip', action='store', type='string', dest='sqlhost', default='localhost',
						help="host of mysql database, default is localhost")
	parser.add_option('-d', '--debug', action='store_true', dest='debug', default='false',
						help="debug flag, default is False")
	(options, args) = parser.parse_args(sys.argv)
	#here s_count represent counts of mails
	s_count = 0
	#link will be a local file or web link
	maillink = options.maillink
	mailsubject = options.mailsubject
	if re.match("^http:.+", maillink) != None:
		try:
			hdl = urllib2.urlopen(maillink)
		except urllib2.URLError, e:
			print e.reason
			sys.exit()
	else:
		try:
			hdl = open(maillink, "rb")
		except IOError, e:
			print e
			sys.exit()
	content = hdl.read()
	#init mysql db handle
	sqldbhandle = mysql.SQLAlchemyUtils(username="root", password="wjy", host="localhost", dbName="MailDB")
	sqldbhandle.init_database()
	#init threadpool
	SendThread = threadpool.ThreadPool(options.threadnum, dbhandle = sqldbhandle)
	rec_reader = Reader(readertype="SEND", sendpool=SendThread, FilePos=options.tolist)
	snd_reader = Reader(readertype="INIT", sendpool=SendThread, FilePos=options.fromlist)
	snd_reader.start()
	rec_reader.start()
	SendThread.setproducer(rec_reader, snd_reader)
	SendThread.start()
	time.sleep(0.2)
	while True:
		try:
			SendThread.poll(block=True)
		except KeyboardInterrupt:
			print "**** Keyboard interrupt!"
			break
		except threadpool.NoResultsPending:
			print "*** No pending results."
			break
		except threadpool.NoWorkersAvailable:
			print "*** No available threads."
			break
	print "Joining all dismissed worker threads..."
	if rec_reader.isAlive():
		rec_reader.dismiss()
	if snd_reader.isAlive():
		snd_reader.dismiss()
	if SendThread.workers:
		SendThread.dismissWorkers(num_workers=options.threadnum, do_join=True)
	if SendThread.dismissedWorkers:
		SendThread.joinAllDismissedWorkers()
	end = time.time()
	if rec_reader._rcount > s_count:
		print "Jobs unfinished! %d receivers, %d succeed, runtime: %.3f seconds."  % (rec_reader._rcount, s_count, end - start)
	else:
		print "All jobs done! %d receivers, %d succeed, runtime: %.3f seconds." % (rec_reader._rcount, s_count, end - start)
 
