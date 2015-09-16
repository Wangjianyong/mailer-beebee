# mailer-beebee
a braodcast mailer implemented by python, using threadpool, mailer and sqlalchemy.

Usage: python mailer.py [options] arg

Options:
  -h, --help            show this help message and exit
  -l MAILLINK, --link=MAILLINK
                        mail content, a web link or a local file
  -n THREADNUM, --num=THREADNUM
                        threadpool size, default is 10
  -t TOLIST, --to=TOLIST
                        to list file location, a local file, default is
                        ../src/fromlist.txt
  -f FROMLIST, --from=FROMLIST
                        from list file location, a local file, default is
                        ../src/fromlist.txt
  -s MAILSUBJECT, --subject=MAILSUBJECT
                        mail subject
  -m MAXSIZE, --max=MAXSIZE
                        mail upper limit of a account, default is 10000
  -a ATTACHMENT, --attachment=ATTACHMENT
                        attachment in the mail
  -u SQLUSER, --username=SQLUSER
                        username of mysql database
  -p SQLPWD, --password=SQLPWD
                        password of mysql database
  -i SQLHOST, --ip=SQLHOST
                        host of mysql database, default is localhost
  -d SQLDBNAME, --database=SQLDBNAME
                        name of mysql database, default is MailDB
