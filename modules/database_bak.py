class DataBaseAsync():

    __thread_pool_select = None
    __thread_pool_insert = None

    __data_base_connector = None

    def __init__(self):
        self.getCurrentConnector()

        self.__thread_pool_insert = ThreadPoolExecutor(1)
        self.__thread_pool_insert.submit( self.__checkSchema )
        self.__thread_pool_select = ThreadPoolExecutor(15)


    def __checkSchema(self) :
        try:
            connect = self.getCurrentConnector(mode="rw")
            connect.cursor().execute('''CREATE TABLE bulks_wait
                                    (id INTEGER PRIMARY KEY,
                                    infobip_id TEXT NULL,
                                    user TEXT NOT NULL,
                                    bulk_name TEXT NOT NULL,
                                    insert_time INT NOT NULL,
                                    send_time INT NOT NULL,
                                    abon_number TEXT NOT NULL,
                                    viber_alpha TEXT NOT NULL,
                                    viber_message TEXT NOT NULL,
                                    viber_validity_time INT NOT NULL,
                                    viber_photo TEXT NULL,
                                    viber_btn_text TEXT NULL,
                                    viber_btn_ancour TEXT NULL,
                                    sms_alpha TEXT NOT NULL,
                                    sms_message TEXT NOT NULL,
                                    sms_validity_time INT NOT NULL,
                                    infobip_status TEXT NULL,
                                    channel TEXT NULL,
                                    status INT NOT NULL
                                    )''')
            connect.cursor().execute('''CREATE INDEX send_time ON bulks_wait(send_time)''')
            connect.cursor().execute('''CREATE INDEX status ON bulks_wait(status)''')
            connect.cursor().execute('''CREATE INDEX infobip_id ON bulks_wait(infobip_id)''')
            connect.cursor().execute('''CREATE TABLE users
                                    (id INTEGER PRIMARY KEY,
                                    login TEXT NOT NULL,
                                    pass TEXT NOT NULL,
                                    name TEXT NULL
                                    )''')
            connect.commit()
        except sqlite3.OperationalError:
            pass

    def messageFactory(self, cursor, row) :
        id = None
        message = Message( row[0] )
        for iField, field in enumerate( cursor.description ):
            if field[0] == 'id' : id = row[ iField ]
            if field[0] == 'infobip_id' : message.infobip_id = row[ iField ]
            if field[0] == 'user' : message.user = row[ iField ]
            if field[0] == 'bulk_name' : message.bulk_name = row[ iField ]
            if field[0] == 'insert_time' : message.insert_time = row[ iField ]
            if field[0] == 'send_time' : message.send_time = row[ iField ]
            if field[0] == 'abon_number' : message.abon_number = row[ iField ]
            if field[0] == 'viber_alpha' : message.viber_alpha = row[ iField ]
            if field[0] == 'viber_message' : message.viber_message = row[ iField ]
            if field[0] == 'viber_validity_time' : message.viber_validity_time = row[ iField ]
            if field[0] == 'viber_photo' : message.viber_photo = row[ iField ]
            if field[0] == 'viber_btn_text' : message.viber_btn_text = row[ iField ]
            if field[0] == 'viber_btn_ancour' : message.viber_btn_ancour = row[ iField ]
            if field[0] == 'sms_alpha' : message.sms_alpha = row[ iField ]
            if field[0] == 'sms_message' : message.sms_message = row[ iField ]
            if field[0] == 'sms_validity_time' : message.sms_validity_time = row[ iField ]
            if field[0] == 'infobip_status' : message.infobip_status = row[ iField ]
            if field[0] == 'channel' : message.channel = row [ iField ]
            if field[0] == 'status' : message.status = row[ iField ]
        return message

    def getCurrentConnector(self, mode="ro") :
        """
        getCurrentConnector()

        Opens a connection to the SQLite database file *database*. You can use
        ":memory:" to open a database connection to a database that resides in
        RAM instead of on disk.

        :rtype: sqlite3.Connection
        """

        if self.__data_base_connector is None :
            self.__data_base_connector = sqlite3.connect('file:viber.db?mode=rw', uri=True, timeout=10, isolation_level = None, check_same_thread = False)
            #self.__data_base_connector.row_factory = self.dictFactory
        return self.__data_base_connector

    def exec( self, sql, params =() ):

        start = time.time()
        #print(sql)
        connect = self.getCurrentConnector()
        curs = connect.cursor()
        print("Start exec " + sql[0:6])
        if len(params) > 0 and sql[0:6] != "SELECT":
            curs.execute("begin")
            curs.executemany( sql, params )
            curs.execute("commit")
        else :
            curs.execute( sql , params )
        data = curs.fetchall()
        print( "Finish exec " + sql[0:6] + " " + str(time.time()-start) )
        return data

    def authenticate(self, login, password) :
        return self.__thread_pool_select.submit(self.__authenticateSync, login, password)

    def __authenticateSync(self, login, password):
        curs = self.getCurrentConnector().cursor()
        curs.execute("SELECT * FROM users WHERE login = (?) ", (login,))
        row = curs.fetchall()
        if not row :
            return print("No such user in system!!!")
        pass_from_base = row[0][2].encode('utf8')
        if bcrypt.hashpw(password.encode('utf8'), pass_from_base) == pass_from_base :
            return True
        else :
            return None


    def __getMessagesSync(self, limit=500) :
        try:
            curs = self.getCurrentConnector().cursor()
            curs.row_factory = self.messageFactory
            curs.execute(
                """SELECT
                      id,
                      infobip_id,
                      user,
                      bulk_name,
                      insert_time,
                      send_time,
                      abon_number,
                      viber_alpha,
                      viber_message,
                      viber_validity_time,
                      viber_photo,
                      viber_btn_text,
                      viber_btn_ancour,
                      sms_alpha,
                      sms_message,
                      sms_validity_time,
                      infobip_status,
                      channel,
                      status
                    FROM bulks_wait
                    LIMIT """ + str(limit) + " OFFSET 0;"
            )
            #time.sleep( 10 )
            return curs.fetchall()
        except Exception as ex:
            print(ex)

    def __getMessagesWaitSendSync(self, limit=500):
        try:
            curs = self.getCurrentConnector().cursor()
            curs.row_factory = self.messageFactory
            curs.execute(
                    """SELECT
                          id,
                          infobip_id,
                          user,
                          bulk_name,
                          insert_time,
                          send_time,
                          abon_number,
                          viber_alpha,
                          viber_message,
                          viber_validity_time,
                          viber_photo,
                          viber_btn_text,
                          viber_btn_ancour,
                          sms_alpha,
                          sms_message,
                          sms_validity_time,
                          infobip_status,
                          channel,
                          status
                        FROM bulks_wait
                        WHERE send_time <= strftime('%s','now') AND status = 0
                        ORDER BY id ASC
                        LIMIT """ + str(limit) + " OFFSET 0;"
            )
            return curs.fetchall()
        except Exception as ex:
            print(ex)

    def __getReportsByInfobipIDSync(self, id ):
        try:
            curs = self.getCurrentConnector().cursor()
            curs.row_factory = self.messageFactory
            curs.execute(
                    """SELECT
                          id,
                          infobip_id,
                          user,
                          bulk_name,
                          insert_time,
                          send_time,
                          abon_number,
                          viber_alpha,
                          viber_message,
                          viber_validity_time,
                          viber_photo,
                          viber_btn_text,
                          viber_btn_ancour,
                          sms_alpha,
                          sms_message,
                          sms_validity_time,
                          infobip_status,
                          channel,
                          status
                        FROM bulks_wait
                        WHERE infobip_id = :infobip_id ;""",
                    { "infobip_id" : id }
            )
            return curs.fetchone()
        except Exception as ex:
            print(ex)

    def __getMessagesReports(self, limit):
        try:
            curs = self.getCurrentConnector().cursor()
            curs.row_factory = self.messageFactory
            curs.execute(
                    """SELECT
                          id,
                          infobip_id,
                          user,
                          bulk_name,
                          insert_time,
                          send_time,
                          abon_number,
                          viber_alpha,
                          viber_message,
                          viber_validity_time,
                          viber_photo,
                          viber_btn_text,
                          viber_btn_ancour,
                          sms_alpha,
                          sms_message,
                          sms_validity_time,
                          infobip_status,
                          channel,
                          status
                        FROM bulks_wait
                        WHERE status = 2
                        ORDER BY id ASC
                        LIMIT """ + str(limit) + " OFFSET 0;"
            )
            return curs.fetchall()
        except Exception as ex:
            print(ex)

    def getMessagesReports(self, limit=500):
        return self.__thread_pool_select.submit( self.__getMessagesReports, limit )

    def getMessagesWaitSend(self, limit=500 ):
        return self.__thread_pool_select.submit( self.__getMessagesWaitSendSync, limit )

    def getMessages(self, limit=500 ):
        return self.__thread_pool_select.submit( self.__getMessagesSync, limit )

    def getReportsByInfobipID(self, id ):
        return self.__thread_pool_select.submit(self.__getReportsByInfobipIDSync, id )

    def getUserBulks(self, user):
        return self.__thread_pool_select.submit(self.__getUserBulks, user)

    def getBulkItem(self, bulk, time):
        return self.__thread_pool_select.submit(self.__getBulkItem, bulk, time)

    def __setMessagesSync(self, messages ) :
        try:
            if type(messages) is not list:
                messages = [ messages ]
            logging.info("Start INSERT " + str(len(messages)))
            insert_template = "INSERT OR REPLACE INTO bulks_wait ( id, infobip_id, user, bulk_name, insert_time, send_time, abon_number, viber_alpha, viber_message, viber_validity_time, viber_photo, viber_btn_text, viber_btn_ancour, sms_alpha, sms_message, sms_validity_time, infobip_status, channel, status ) VALUES "
            values_templayte = "INSERT OR REPLACE INTO bulks_wait VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            values_templayte_params = "( :id, :infobip_id, :user, :bulk_name, :insert_time, :send_time, :abon_number, :viber_alpha, :viber_message, :viber_validity_time, :viber_photo, :viber_btn_text, :viber_btn_ancour, :sms_alpha, :sms_message, :sms_validity_time, :infobip_status, :channel, :status );"

            list_val = []
            for message in messages:
                if message.abon_number:
                    list_val.append(message.getList())
                    #print(list_val[0])
            return self.exec(values_templayte, list_val)

        except Exception as ex :
            print( ex )

    def setMessages( self , messages ) :
        return self.__thread_pool_insert.submit( self.__setMessagesSync , messages )

    def __getCountSendSync(self):
        """Вернет количество отправленных сообщений"""
        return self.exec( "SELECT COUNT(id) FROM bulks_wait WHERE status = 1" )[0][0]

    def __getUserBulks(self, user):
        """Вернет количество рассылок юзера"""
        return self.exec( "SELECT bulk_name, send_time, COUNT(id) as count_bulks, CASE WHEN status = 0 THEN 'wait' WHEN status = 3 or status = 4 or status = 5 or status = 6 THEN 'complete' WHEN status = 1 or status = 2 THEN 'now' END FROM bulks_wait WHERE user = '%s' GROUP BY bulk_name, send_time ORDER BY send_time ASC" % user)

    def __getBulkItem(self, bulk, time):
        """Вернет рассылку по названию и времени старта"""
        return self.exec('''SELECT bulk_name,
                              COUNT(id) AS AllMessages,
                              SUM(CASE WHEN status = 4 THEN 1 ELSE 0 END) AS Delivered,
                              SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) AS InProcess,
                              SUM(CASE WHEN status = 3 THEN 1 ELSE 0 END) + SUM(CASE WHEN status = 5 THEN 1 ELSE 0 END) + SUM(CASE WHEN status = 6 THEN 1 ELSE 0 END) AS Undelivered,
                              CASE WHEN status = 1 or status = 2 THEN 'Выполняется доставка' WHEN status = 0 THEN 'Рассылка запланирована' WHEN status = 3 or status = 4 or status = 6 or status = 5 THEN 'Рассылка завершена' END AS state,
                              send_time,
                              insert_time,
                              CASE WHEN viber_photo IS NOT NULL THEN 'С картинкой' ELSE 'Без картинки' END AS Image,
                              viber_alpha,
                              viber_message,
                              CASE WHEN viber_photo IS NOT NULL THEN viber_photo ELSE NULL END AS ImagePath,
                              CASE WHEN viber_btn_ancour IS NOT NULL THEN viber_btn_ancour ELSE 'Без картинки' END AS ImageUrl,
                              viber_validity_time,
                              sms_alpha,
                              sms_message,
                              sms_validity_time,
                              SUM(CASE WHEN status = 4 AND channel = 'VIBER' THEN 1 ELSE 0 END) AS count_viber,
                              SUM(CASE WHEN status = 4 AND channel = 'SMS' THEN 1 ELSE 0 END) AS count_sms
                        FROM bulks_wait
                        WHERE bulk_name =? AND send_time=?''', (bulk, time))

    def getCountSend(self):
        """Вернет количество отправленных сообщений"""
        return self.__thread_pool_select.submit(self.__getCountSendSync)