from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import math
import sqlite3 as db
import os
PathToDatabase = "/home/system/DeerDetector/static/main.db"

class MainModel():
	def __init__(self):
		self.whatver = ""

	def Paginate(sef,perpage,qry):
		con = db.connect(PathToDatabase)
		con.row_factory = db.Row
		cur = con.cursor() 
		con.row_factory = db.Row
		cur = con.cursor() 
		cur.execute(qry)
		lines = cur.fetchall()
		#print(lines)
		con.commit()
		total = len(lines)
		return math.ceil(int(total)/int(perpage)),total
	
	def Get_logs_motion(self,start,end):
		try: 
			con = db.connect(PathToDatabase)
			con.row_factory = db.Row
			cur = con.cursor() 
			con.row_factory = db.Row
			cur = con.cursor()
			query = "SELECT * FROM logs_motion ORDER BY date DESC LIMIT "+str(start)+","+str(end)
			cur.execute(query)
			lines = cur.fetchall()
			#print(lines)
			con.commit()
			if con:
				con.close()
				if len(lines) > 0:
					return lines
				else:
					return False
		except Exception as e:
			print("logs_motion Error %s:" % e.args[0])
			return False	
	
	def Clear_logs_motion(self):
		try: 
			con = db.connect(PathToDatabase)
			con.row_factory = db.Row
			cur = con.cursor() 
			con.row_factory = db.Row
			cur = con.cursor()
			query = "DELETE FROM logs_motion"
			cur.execute(query)
			#print(lines)
			con.commit()
			if con:
				con.close()
				return True
			else:
				return False
		except Exception as e:
			print("Clear_logs_motion Error %s:" % e.args[0])
			return False
				
	def Get_logs_detection(self,start,end):
		try: 
			con = db.connect(PathToDatabase)
			con.row_factory = db.Row
			cur = con.cursor() 
			con.row_factory = db.Row
			cur = con.cursor()
			query = "SELECT * FROM logs_detection ORDER BY date DESC LIMIT "+str(start)+","+str(end)
			cur.execute(query)
			lines = cur.fetchall()
			#print(lines)
			con.commit()
			if con:
				con.close()
				if len(lines) > 0:
					return lines
				else:
					return False
		except Exception as e:
			print("logs_detection Error %s:" % e.args[0])
			return False	
				
	def Clear_logs_detection(self):
		try: 
			con = db.connect(PathToDatabase)
			con.row_factory = db.Row
			cur = con.cursor() 
			con.row_factory = db.Row
			cur = con.cursor()
			query = "DELETE FROM logs_detection"
			cur.execute(query)
			#print(lines)
			con.commit()
			if con:
				con.close()
				return True
			else:
				return False
		except Exception as e:
			print("Clear_logs_detection Error %s:" % e.args[0])
			return False
		
	def Get_files(self,start,end):
		try: 
			con = db.connect(PathToDatabase)
			con.row_factory = db.Row
			cur = con.cursor() 
			query = "SELECT * FROM files ORDER BY date DESC LIMIT "+str(start)+","+str(end)
			cur.execute(query)
			lines = cur.fetchall()
			#print(lines)
			con.commit()
			if con:
				con.close()
				if len(lines) > 0:
					return lines
				else:
					return False
		except Exception as e:
			print("logs_detection Error %s:" % e.args[0])
			return False	
	
	def GetFile(id):
			try:
				print(id)
				con = db.connect(PathToDatabase)
				con.row_factory = db.Row
				cur = con.cursor()
				query = "SELECT * FROM files WHERE id="+str(id)
				cur.execute(query)
				lines = cur.fetchall()
				#print(lines)
				con.commit()
				con.close()
				if len(lines) > 0:
					return lines
				else:
					return False
			except Exception as e:
				print("Get_File Error %s:" % e.args[0])
				return False
			
	def Update_Image(self,data):
		try:
			con = db.connect(PathToDatabase)
			con.row_factory = db.Row
			cur = con.cursor() 
			con.row_factory = db.Row
			cur = con.cursor()
			cur.execute("UPDATE files SET comments=? WHERE id=?",(data[0],data[1]))
			con.commit()
			return True
		except db.Error as error:
			print("Update_Image Error: ",str(error))
			return False
		except Exception as e:
			print("Update_Image Exception: ",str(e))
			return False
													
	def Delete_Image(self,id,filename):
		try:
			con = db.connect(PathToDatabase)
			con.row_factory = db.Row
			cur = con.cursor() 
			con.row_factory = db.Row
			cur = con.cursor()
			cur.execute("DELETE FROM files WHERE id="+str(id))
			con.commit()
			#Delete the image file
			os.remove("/home/system/DeerDetector/static/captures/"+filename)
			return True
		except db.Error as error:
			print("Delete_Image Error: ",str(error))
			return error
		except Exception as e:
			print("Delete_Image Exception: ",str(e))
			return str(e)
				
	def Insert_log_detection(self,data):
		try:
			import datetime
			from datetime import datetime
			cdt = datetime.today()
			currentdate = cdt.date()
			current_time = cdt.strftime("%H:%M:%S")
			print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",data)
			#data = self.Cleaninput(self,data)
			query = "INSERT INTO logs_detection (date,time,probability,image,duration) VALUES('"+str(currentdate)+"','"+str(current_time)+"','"+str(data[0])+"','"+str(data[1])+"','"+str(data[2])+"')"
			con = db.connect(PathToDatabase)
			con.row_factory = db.Row
			cur = con.cursor()
			cur.execute(query)
			con.commit()
			ID = cur.lastrowid
			cur.close()
			return ID
		except db.Error as error:
			print("Insert_log_detection Error: ",str(error))
			return False
		except Exception as e:
			print("Insert_log_detection Error %s:" % e.args[0])
			return False

	def Insert_log_motion(self,data):
		import datetime
		from datetime import datetime
		try:
			cdt = datetime.today()
			currentdate = cdt.date()
			current_time = cdt.strftime("%H:%M:%S")
			query = "INSERT INTO logs_motion (date,time,sensor) VALUES('"+str(currentdate)+"','"+str(current_time)+"','"+str(data)+"')"
			con = db.connect(PathToDatabase)
			con.row_factory = db.Row
			cur = con.cursor()
			cur.execute(query)
			con.commit()
			ID = cur.lastrowid
			cur.close()
			return ID
		except db.Error as error:
			print("Insert_log_detection Error: ",str(error))
			return False
		except Exception as e:
			print("Insert_log_detection Error %s:" % e.args[0])
			return False
		
	def Cleaninput(self,data):
		data = data.replace("'","\\'")
		data = data.replace('\"','\\"')
		data = data.replace('^',' ')
		data = data.replace('&','amp;')
		data = data.replace('^',' ')
		return data