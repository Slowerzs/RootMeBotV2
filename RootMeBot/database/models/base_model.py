from peewee import Model, Proxy, SqliteDatabase

database = Proxy()
 
class BaseModel(Model):
	class Meta:
		database = database
