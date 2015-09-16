from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.schema import Column
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import String, DateTime, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Mail(Base):
	__tablename__ = 'mails'
	_id = Column(Integer, primary_key = True)
	_To = Column(String(50))
	_From = Column(String(50))
	_Content = Column(String(200))
	_Datetime = Column(DateTime)
	_Status = Column(Boolean)

	def __init__(self, To, From, Content, Datetime, Status):
		self._To = To
		self._From = From
		self._Content = Content
		self._Datetime = Datetime
		self._Status = Status
		
	def __repr__(self):
		return "<Mail(_To = '%s', _From = '%s', _Content = '%s', _Datetime = '%r', _Status = '%r')>"\
					% (self._To, self._From, self._Content, self._Datetime, self._Status)


class SQLAlchemyUtils(object):
	def __init__(self, dialect = "mysql", driver = "mysqldb", username = "root",\
					   password = "wjy", host = "localhost", dbName = "mailDB"):
		self._dbName = dbName
		self._url = '%s+%s://%s:%s@%s/' % (dialect, driver, username, password, host)

	def database_exists(self):
		engine = create_engine(self._url)
		text = ("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
                "WHERE SCHEMA_NAME = '%s'" % self._dbName)
		return bool(engine.execute(text).scalar())

	def init_database(self):
		if self.database_exists() is False:
			query = "CREATE DATABASE " + self._dbName
			create_engine(self._url, echo = False).execute(query)
		url = self._url + self._dbName
		engine = create_engine(url, echo = False)
		Base.metadata.create_all(engine)
		Session = sessionmaker(bind = engine)
		self._session = Session()
	
	def insert_database(self, entry):
		self._session.add(entry)
		self._session.commit()


################
# USAGE EXAMPLE#
################

if __name__ == '__main__':
	db = SQLAlchemyUtils(dbName = "Maildb")
	db.init_database()
	entry = Mail(To = 'jianywan@126.com', From = 'jianywan@gmail.com',
				 Content = 'http://docs.sqlalchemy.org/en/rel_1_0/_modules/examples/adjacency_list/adjacency_list.html', Datetime = datetime.today(), Status = True)
	db.insert_database(entry)
