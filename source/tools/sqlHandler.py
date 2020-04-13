##@package sqlHandler
#MySQL database python helper package
# 
#a collection of functions to allow easy ascess to the MySQL database.

import numpy as np
import mysql.connector as sql
from mysql.connector.errors import ProgrammingError
import logging

from collections.abc import Iterable



##SqlDatabaseHandler
#
#Collection of methods to help manage the MySQL database
class SqlDatabaseHandler():

    _logname = 'SqlDatabaseHandler'
    _log = logging.getLogger(f'{_logname}')

    ##SqlDatabaseHandler constructor
    #
    #Log in to the database and create connection
    #@param LOGIN The login details of the MySQL database.   
    def __init__(self, LOGIN: list):
        self.db = sql.connect(
            host=LOGIN[0],
            user=LOGIN[1],
            passwd=LOGIN[2]
        )

        self.cursor = self.db.cursor()

    ##Create a database user
    #
    #create a user for the brewing database
    #@param host The host that the databse will be acessed from.
    #@param user The username.
    #@param passwd The password.
    def createUser(self, host: str, user: str, passwd: str):
        self.cursor.execute(f"GRANT INSERT, SELECT, DELETE, UPDATE ON Brewing.* TO '{user}'@'{host}' IDENTIFIED BY '{passwd}'")
        self.cursor.execute("FLUSH PRIVILEGES")
        self._log.info(f"New user: {user} created on: {host}")

    ##Create a database super user
    #
    #create a super user for the all databases, privilaged acess.
    #@param host The host that the databse will be acessed from.
    #@param user The username.
    #@param passwd The password.
    def createSuperUser(self, host: str, user: str, passwd: str):
        self.cursor.execute(f"GRANT ALL PRIVILEGES ON *.* TO '{user}'@'{host}' IDENTIFIED BY '{passwd}' WITH GRANT OPTION")
        self.cursor.execute("FLUSH PRIVILEGES")
        self._log.info(f"New super user: {user} created on: {host}")
        
    ##Show all the databses present.
    def showAllDatabases(self):
        self.cursor.execute("SHOW DATABASES")
        if not any(True for _ in self.cursor):
            self._log.info(f"No databases!")
        else:
            self._log.info(f"Databases present:")
            s = ""
            for x in self.cursor:
                s += f" {x[0]}"
            self._log.info(f"{s}")

    ##check if a database exists
    #
    #@param databaseName name of database to check if exists
    #@return bool if database exists
    def checkDatabaseExists(self, databaseName: str) -> bool:
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.schemata
            WHERE SCHEMA_NAME = '{0}'
            """.format(databaseName.replace('\'','\'\'')))
        if self.cursor.fetchone()[0] == 1:
            return True
        return False

    ##Create a new Database
    def createDatabase(self, databaseName: str):
        if self.checkDatabaseExists(databaseName):
            self._log.info(f"Database \"{databaseName}\" already exists")
            return
        self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {databaseName}")
        self._log.info(f"Database \"{databaseName}\" added")

    ##Delete a databse
    def deleteDatabase(self, databaseName: str):
        self.cursor.execute(f"DROP DATABASE IF EXISTS {databaseName}")
        self._log.info(f"Database \"{databaseName}\" droped")

##LoginError exception
#
#If user fails to login, return exception
class LoginError(Exception):
    "Exception for login Errors"
    pass

##SqlTableHandler
#
#Collection of methods to help manage a table in the database
class SqlTableHandler():

    _logname = 'SqlTableHandler'
    _log = logging.getLogger(f'{_logname}')

    ##SqlTableHandler constructor
    #
    #Log in to the database and create connection
    #@param LOGIN The login details of the MySQL connection. 
    #@param databaseName The database to acess
    def __init__(self, LOGIN, databaseName):
        try:
            # self.sql = sql
            self.db= sql.connect(
                host=LOGIN[0],
                user=LOGIN[1],
                passwd=LOGIN[2],
                database=databaseName)

            self.databaseName = databaseName
            self._log.debug(f"Opening \"{databaseName}\"")
            self.cursor = self.db.cursor()

        except ProgrammingError:
            raise LoginError("Invalid Login details ")

    ##Update the tables for all users
    def flushTables(self):
        self.cursor.execute("FLUSH TABLES")

    ##Perform custom SQL command
    #
    #@param sql The SQL string to execute
    #@return the returned query results
    def custom(self, sql: str, val=None ):
        if val is None:
            self.cursor.execute(sql)
        elif val is not None:
            self.cursor.executemany(sql,val)
        return self.cursor.fetchall()

    ##Create a table in the database
    def createTable(self, tableName: str, columns: list):
        if self.checkTableExists(tableName):
            self._log.info(f"Table \"{tableName}\" already exists")
            return

        string = "(id INT AUTO_INCREMENT PRIMARY KEY"
        for i in columns:
            string += ", " +i
        string+= ")"

        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {tableName} {string}")
        self._log.info(f"Table \"{tableName}\" added")

    ##Check if a table exists
    def checkTableExists(self, tableName: str) -> bool:
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = '{0}'
            """.format(tableName.replace('\'','\'\'')))
        if self.cursor.fetchone()[0] == 1:
            return True
        return False
    
    ##Delete a table from the database
    def deleteTable(self, tableName: str): 
        if not self.checkTableExists(tableName):
            self._log.info(f"Table \"{tableName}\" dosen't exist")
            return
        self.cursor.execute(f"DROP TABLE IF EXISTS {tableName}")
        self._log.info(f"Table \"{tableName}\" droped")

    ##Find information regarding a table
    def describeTable(self, tableName: str):
        self._log.info(f"Table: {tableName}")
        self.cursor.execute(f"DESCRIBE {tableName}")
        for x in self.cursor:
            self._log.info(f"{x}")

    ##SQL field genorator
    #
    #Helper method to check validity of a field and return an SQL command to create a field of a given type
    def createField(self, name: str, datatype: str, length=None, decimal=None):
        try:
            if (length is None) and (decimal is None):
                assert datatype in ["TINYTEXT","TEXT","MEDIUMTEXT",
                                "LONGTEXT","FLOAT","DATE",
                                "DATETIME","TIMESTAMP","TIME",
                                "SET","ENUM"]
                return name + " "+ datatype
            elif (length is not None) and (decimal is None):
                assert datatype in ["CHAR","VARCHAR","TINYINT",
                                "SMALLINT","MEDIUMINT","INT",
                                "BIGINT"]
                return name +" "+ datatype + f"({length})"
            elif (length is not None) and (decimal is not None):
                assert datatype in ["DOUBLE","DECIMAL"]
                return name +" "+ datatype + f"({length},{decimal})"
            else:
                raise AssertionError

        except AssertionError:
            self._log.error(f"invalid table field of name: {name}, type: {datatype}, length: {length}, decimal: {decimal}")
            
    ##Show all the tablse in a database
    def showAllTables(self):
        self.cursor.execute("SHOW TABLES")
        if not any(True for _ in self.cursor):
            self._log.info(f"No tables in \"{self.databaseName}\"")
        else:
            self._log.info(f"Tables in \"{self.databaseName}\"")
            for x in self.cursor:
                self._log.info(x)

    ##View all the contents of a table
    def viewTable(self, tableName:str):
        self.cursor.execute(f"SELECT * FROM {tableName}")
        for x in self.cursor.fetchall():
            self._log.info(x)

    ##Delete an entry from a tbale
    def deleteFromTable(self, tableName: str, field: str, value:str):
        sql = f"DELETE FROM {tableName} WHERE {field} = %s "
        val = (f"{value}",)
        self.cursor.execute(sql,val)
        self.db.commit()
        self._log.info("Table record deleted")

    ##insert data into a given table
    def insertToTable(self, tableName: str, data: list):
        fields = data[0][0]
        values = "%s"
        for i in range(1,len(data[0]),1):
            fields += ", " +data[0][i]
            values += ", %s"
        sql = f"INSERT INTO {tableName} ({fields}) VALUES ({values})"
        self.cursor.executemany(sql,data[1:])

        self.db.commit()
        self._log.debug(f"Record inserted to {tableName}: {fields}")

    ##Read fields forom a table
    def readFromTable(self, tableName: str, fields: str):
        sql = f"SELECT {fields} FROM {tableName}"
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    
    ##Return the maximum primary key from table
    def maxIdFromTable(self, tableName: str):
        self.cursor.execute(f"SELECT max(id) FROM {tableName}")
        return self.cursor.fetchone()[0]

    ##Return the maximum value froma  given table
    def maxValueFromTable(self, value, tableName: str):
        self.cursor.execute(f"SELECT max({value}) FROM {tableName}")
        return self.cursor.fetchone()[0]

    ##Perform an Inner Join
    def innerJoin(self, primaryTable: str, fieldSelect: str, secondaryTable: str, fieldSelect2: str, fieldMatch: str):

        sql = f"SELECT {secondaryTable}.{fieldSelect2}, {primaryTable}.{fieldSelect} "
        sql += f"FROM {secondaryTable} INNER JOIN {primaryTable} "
        sql += f"ON {secondaryTable}.{fieldMatch}={primaryTable}.id"

        self.cursor.execute(sql)
        return self.cursor.fetchall()


if __name__ == "__main__":

    import logging
    from getpass import getpass
    _logname = 'SqlHandlerMain'
    _log = logging.getLogger(f'{_logname}')
    
    
    HOST = "localhost"
    USER = "Test"
    PASSWORD = "BirraMosfeti"

    HOST = "192.168.10.223"
    USER = "jamie"
    PASSWORD = "beer"

    # HOST = input("Host ID: ")
    # USER = input("User: ")
    # PASSWORD = getpass()
    if HOST == "Pi": 
        HOST = "192.168.10.223"
        HOST = "192.168.0.17"

    LOGIN = [HOST,USER,PASSWORD]

    s = SqlDatabaseHandler(LOGIN)
    s.createDatabase("Brewing")
    s.showAllDatabases()


    t = SqlTableHandler(LOGIN, "Brewing")
    t.showAllTables()

    t.deleteTable("Brews")
    t.deleteTable("Boil")
    t.deleteTable("BoilMonitor")
    t.deleteTable("Ferment")
    t.deleteTable("Mash")

    fileds = []
    fileds.append(t.createField("Recipe","VARCHAR", 225))
    fileds.append(t.createField("Date","DATE"))
    fileds.append(t.createField("MashTemp","DOUBLE",255, 1))
    fileds.append(t.createField("MashTime","INT", 225))
    fileds.append(t.createField("BoilTemp","DOUBLE",255,1))
    fileds.append(t.createField("BoilTime","INT",255))
    fileds.append(t.createField("Hop1Name","VARCHAR", 225))
    fileds.append(t.createField("Hop1Time","INT", 225))
    fileds.append(t.createField("Hop2Name","VARCHAR", 225))
    fileds.append(t.createField("Hop2Time","INT", 225))
    fileds.append(t.createField("Hop3Name","VARCHAR", 225))
    fileds.append(t.createField("Hop3Time","INT", 225))
    fileds.append(t.createField("Hop4Name","VARCHAR", 225))
    fileds.append(t.createField("Hop4Time","INT", 225))
    fileds.append(t.createField("FermentTemp","DOUBLE",255, 1))

    t.createTable("Brews", fileds)

    #BatchID matches primary key of Brew Table
    fileds = []
    fileds.append(t.createField("BatchID","INT", 225))
    fileds.append(t.createField("TimeStamp","DATETIME"))
    fileds.append(t.createField("Temp","DOUBLE", 225, 2))
    fileds.append(t.createField("pH","DOUBLE",255,2))
    fileds.append(t.createField("SG","DOUBLE",255,3))
    fileds.append(t.createField("Volume","DOUBLE",255,4))
    t.createTable("Mash", fileds)

    fileds = []
    fileds.append(t.createField("BatchID","INT", 225))
    fileds.append(t.createField("BoilStart","DATETIME"))
    fileds.append(t.createField("Hop1","TIME"))
    fileds.append(t.createField("Hop2","TIME"))
    fileds.append(t.createField("Hop3","TIME"))
    fileds.append(t.createField("Hop4","TIME"))
    fileds.append(t.createField("BoilFinish","DATETIME"))
    t.createTable("Boil", fileds)

    fileds = []
    fileds.append(t.createField("BatchID","INT", 225))
    fileds.append(t.createField("TimeStamp","DATETIME"))
    fileds.append(t.createField("Temp","DOUBLE", 225, 2))
    fileds.append(t.createField("Volume","DOUBLE", 225, 4))
    t.createTable("BoilMonitor", fileds)

    fileds = []
    fileds.append(t.createField("BatchID","INT", 225))
    fileds.append(t.createField("TimeStamp","DATETIME"))
    fileds.append(t.createField("Fermenter","INT", 225))
    fileds.append(t.createField("Sg","DOUBLE", 225, 3))
    fileds.append(t.createField("Temp","DOUBLE", 225, 2))
    fileds.append(t.createField("Volume","DOUBLE", 225, 4))
    t.createTable("Ferment", fileds)

    # t.describeTable("Mash")
    # t.describeTable("Boil")
    # t.describeTable("BoilMonitor")
    # t.describeTable("Ferment")

    insert = []
    insert.append(("Recipe", "Date", "MashTime", "MashTemp","BoilTime",\
        "BoilTemp","Hop1Time", "Hop1Name","Hop2Time", "Hop2Name",\
        "Hop3Time", "Hop3Name","Hop4Time", "Hop4Name", "FermentTemp"))
    insert.append(("BirraMosfetti", "2020-02-14", "60","57","60","96",\
        "0","Simcoe","15","Simcoe","45","Simcoe","59","Simcoe","20"))

    #insert.append(("TenAmps", "2020-02-10"))
    # t.insertToTable("Brews", insert)

    insert = []
    insert.append(("BatchID", "TimeStamp","Fermenter","Sg", "Temp","Volume"))
    insert.append(("1", "2020-02-14 12:45:00","1", "1.005", "20.52","10.56"))
    insert.append(("1", "2020-02-14 13:45:00","1", "1.004", "20.51","10.52"))
    insert.append(("1", "2020-02-14 14:45:00","1", "1.003", "20.56","10.51"))
    insert.append(("1", "2020-02-14 15:45:00","1", "1.000", "20.59","10.50"))
    # insert.append(("2", "2020-02-14 16:45:00","2", "1.105", "20.52","10.56"))
    # insert.append(("2", "2020-02-14 17:45:00","2", "1.104", "20.51","10.52"))
    # insert.append(("2", "2020-02-14 18:45:00","2", "1.103", "20.56","10.51"))
    # insert.append(("2", "2020-02-14 19:45:00","2", "1.100", "20.59","10.50"))
    # t.insertToTable("Ferment", insert)


    for x in t.readFromTable("Brews", "Recipe, Date"):
        print(x)

    for x in t.readFromTable("Ferment", "BatchID, TimeStamp, Fermenter, Sg,Temp,Volume"):
        print(x)

    for x in t.innerJoin("Brews","Recipe","Ferment","Sg", "BatchID"):
        print(x)

    print("current BrewID: {}".format(t.maxIdFromTable("Brews")))
    print("database reset")

    #t.deleteTable("people")
    # t.createTable("people", columns)
    # #t.describeTable("people")
    # #t.deleteTable("people")

    # insert = []
    # insert.append(("name", "age", "date"))
    # insert.append(("jamie", "22", "1997-03-18"))
    # insert.append(("mat", "23", "1996-03-18"))

    # t.insertToTable("people", insert)

    # for x in t.readFromTable("people", "name, age"):
    #     print(x)

    # t.deleteFromTable("people","name","mat")
    # t.viewTable("people")
    
    
