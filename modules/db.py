import tornado.gen
import bcrypt
import momoko
import psycopg2
import time
from modules.message import Message
import logging

logging.basicConfig(format = u'%(levelname)-8s [%(asctime)s] %(message)s', level = logging.DEBUG, filename = u'logs/app.log')

class MomokoDB:
    db = None
    def __init__(self):
        if self.db is None:
            # self.createSchema()
            self.db = momoko.Pool(
                dsn='dbname=%s '
                    'user=%s '
                    'password=%s '
                    'host=%s '
                    'port=%s' % ('viberdb',
                                 'admin',
                                 '',
                                 'localhost',
                                 '5432'),
                size=1,
                max_size=50,
                auto_shrink=True
            )
            self.db.connect()

    @tornado.gen.coroutine
    def createSchema(self):
        self.db.execute("CREATE SEQUENCE item_id")
        self.db.execute(
            '''CREATE TABLE bulks_wait
            (id INTEGER PRIMARY KEY DEFAULT NEXTVAL('item_id'),
            infobip_id varchar(80) NULL,
            username varchar(80) NOT NULL,
            bulk_name varchar(120) NOT NULL,
            insert_time INTEGER NOT NULL,
            send_time INTEGER NOT NULL,
            abon_number varchar(80) NOT NULL,
            viber_alpha varchar(80) NOT NULL,
            viber_message varchar(1000) NOT NULL,
            viber_validity_time INTEGER NOT NULL,
            viber_photo varchar(512) NULL,
            viber_btn_text varchar(45) NULL,
            viber_btn_ancour varchar(512) NULL,
            sms_alpha varchar(80) NOT NULL,
            sms_message varchar(1000) NOT NULL,
            sms_validity_time INTEGER NOT NULL,
            infobip_status varchar(80) NULL,
            channel varchar(80) NULL,
            status INTEGER NOT NULL)'''
        )
        self.db.execute("CREATE INDEX send_time ON bulks_wait(send_time)")
        self.db.execute("CREATE INDEX status ON bulks_wait(status)")
        self.db.execute("CREATE INDEX infobip_id ON bulks_wait(infobip_id)")
        self.db.execute("CREATE SEQUENCE user_id")
        self.db.execute('''
            CREATE TABLE users
                (id INTEGER PRIMARY KEY DEFAULT NEXTVAL('user_id'),
                login varchar(120) NOT NULL,
                pass varchar(512) NOT NULL,
                name varchar(120) NULL)
        ''')
        # self.db.execute('''
        #     CREATE OR REPLACE FUNCTION update_id()
        #     RETURNS trigger AS
        #     $BODY$
        #         BEGIN
        #             IF (NEW.id IS NULL) THEN
        #                 NEW.id := nextval('item_id');
        #                 RETURN NEW;
        #             END IF;
        #         END;
        #     $BODY$
        #     LANGUAGE plpgsql;
        # ''')
        # self.db.execute('''
        #     CREATE TRIGGER update_id_trigger BEFORE INSERT ON bulks_wait
	     #    FOR EACH ROW EXECUTE PROCEDURE update_id();
        # ''')

    @tornado.gen.coroutine
    def getCountSend(self):
        cursor = yield self.db.execute( "SELECT COUNT(id) FROM bulks_wait WHERE status = 1" )
        return cursor.fetchall()[0][0]

    @tornado.gen.coroutine
    def getMessagesWaitSend(self, limit=500):
        """Выбирает сообщения с базы на отправку"""
        try:
            cursor = yield self.db.execute(
                '''SELECT
                      id,
                      infobip_id,
                      username,
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
                WHERE send_time <= EXTRACT(EPOCH FROM NOW())::INT AND status = 0
                ORDER BY id ASC
                LIMIT ''' + str(limit) + " OFFSET 0;"
            )
            msgs = self.messageFactory(cursor)
            return msgs
        except Exception as ex:
            print(ex)

    @tornado.gen.coroutine
    def setMessages(self, messages):
        """Кладем сообщения в базу"""
        try:
            if type(messages) is list:
                data = []
                logging.info("Start INSERT " + str(len(messages)) + " messages!")
                for message in messages:
                    if message.abon_number:
                        if message.id() is None :
                            query = yield self.db.mogrify("( nextval('item_id'),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", message.getList()[1:])
                        else:
                            query = yield self.db.mogrify("( %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", message.getList())
                        data.append(query.decode("utf8"))
                args_str = ','.join(data)
                logging.info("Start INSERT " + str(len(data)) + " messages!")
                start = time.time()
                print(data[:3])
                print("Execution start")
                yield self.db.execute("INSERT INTO bulks_wait VALUES " + args_str + " ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status, infobip_id = EXCLUDED.infobip_id, infobip_status = EXCLUDED.infobip_status, channel = EXCLUDED.channel")
                print("Execution End "+ str(time.time() - start ))

            else:
                new_str = messages.getList()
                logging.info("Start INSERT report from Infobip for Message with #ID: " + str(messages.getList()[0]))
                print(new_str)
                yield self.db.execute("INSERT INTO bulks_wait VALUES %s ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status, infobip_id = EXCLUDED.infobip_id, infobip_status = EXCLUDED.infobip_status, channel = EXCLUDED.channel", (new_str,))

        except psycopg2.Error as ex:
            print(ex)

    @tornado.gen.coroutine
    def getReportsByInfobipID(self, id):
        """Вернет отчет по доставленному сообщению на Infobip"""
        try:
            cursor = yield self.db.execute(
                """SELECT
                      id,
                      infobip_id,
                      username,
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
                    WHERE infobip_id = %s""", (id,)
            )
            message = self.messageFactory(cursor)
            logging.info('getReportsByInfobipID: ' + str(message[0].infobip_id))
            return message[0]
        except psycopg2.Error as ex:
            print(ex)

    @tornado.gen.coroutine
    def getUserBulks(self, user):
        """Вернет количество рассылок юзера"""
        try:
            cursor = yield self.db.execute(
                """SELECT
                      bulk_name,
                      send_time,
                      COUNT(id) as count_bulks,
                      (CASE
                          WHEN (COUNT(*) FILTER (WHERE status = 0)) != 0 THEN 'wait'
                          WHEN (COUNT(*) FILTER (WHERE status = 1 or status = 2)) != 0 THEN 'now'
                          WHEN (COUNT(*) FILTER (WHERE status = 3 or status = 4 or status = 5 or status = 6)) != 0 THEN 'complete'
                      END) as state
                    FROM bulks_wait
                    WHERE username = %s
                    GROUP BY bulk_name, send_time
                    ORDER BY send_time;""", (user,))
            return cursor.fetchall()
        except Exception as ex:
            print(ex)

    @tornado.gen.coroutine
    def getBulkItem(self, bulk, time):
        """Вернет рассылку по названию и времени старта"""
        try:
            cursor = yield self.db.execute(
                """SELECT
                     bulk_name,
                     COUNT(id) AS AllMessages,
                     SUM(CASE WHEN status = 4 THEN 1 ELSE 0 END) AS Delivered,
                     SUM(CASE WHEN status = 2 THEN 1 ELSE 0 END) AS InProcess,
                     SUM(CASE WHEN status = 3 THEN 1 ELSE 0 END) + SUM(CASE WHEN status = 5 THEN 1 ELSE 0 END) + SUM(CASE WHEN status = 6 THEN 1 ELSE 0 END) AS Undelivered,
                     (CASE
                       WHEN (COUNT(*) FILTER (WHERE status = 0)) != 0 THEN 'Рассылка запланирована'
                       WHEN (COUNT(*) FILTER (WHERE status = 1 or status = 2)) != 0 THEN 'Выполняется доставка'
                       WHEN (COUNT(*) FILTER (WHERE status = 3 or status = 4 or status = 5 or status = 6)) != 0 THEN 'Рассылка завершена'
                     END) AS state,
                     send_time,
                     MAX(insert_time),
                     CASE
                       WHEN viber_photo IS NOT NULL THEN 'С картинкой' ELSE 'Без картинки'
                     END AS Image,
                     viber_alpha,
                     (SELECT viber_message FROM bulks_wait WHERE bulk_name = %s LIMIT 1) as viber_mess,
                     CASE
                       WHEN viber_photo IS NOT NULL THEN viber_photo ELSE NULL
                     END AS ImagePath,
                     CASE
                       WHEN viber_btn_ancour IS NOT NULL THEN viber_btn_ancour ELSE 'Без картинки'
                     END AS ImageUrl,
                     viber_validity_time,
                     sms_alpha,
                     (SELECT sms_message FROM bulks_wait  WHERE bulk_name = %s LIMIT 1) as sms_mess,
                     sms_validity_time,
                     SUM(CASE WHEN status = 4 AND channel = 'VIBER' THEN 1 ELSE 0 END) AS count_viber,
                     SUM(CASE WHEN status = 4 AND channel = 'SMS' THEN 1 ELSE 0 END) AS count_sms
                   FROM bulks_wait
                   WHERE bulk_name = %s AND send_time= %s
                   GROUP BY bulk_name,
                     send_time,
                     Image,
                     viber_alpha,
                     ImagePath,
                     ImageUrl,
                     viber_validity_time,
                     sms_alpha,
                     sms_validity_time""", (bulk, bulk, bulk, time,)
            )
            return cursor.fetchall()
        except Exception as ex:
            print(ex)

    def messageFactory(self, cursor):
        msgs_lst = []
        for row in cursor.fetchall():
            id = None
            message = Message(row[0])
            for iField, field in enumerate(cursor.description):
                if field[0] == 'id': id = row[iField]
                if field[0] == 'infobip_id': message.infobip_id = row[iField]
                if field[0] == 'username': message.username = row[iField]
                if field[0] == 'bulk_name': message.bulk_name = row[iField]
                if field[0] == 'insert_time': message.insert_time = row[iField]
                if field[0] == 'send_time': message.send_time = row[iField]
                if field[0] == 'abon_number': message.abon_number = row[iField]
                if field[0] == 'viber_alpha': message.viber_alpha = row[iField]
                if field[0] == 'viber_message': message.viber_message = row[iField]
                if field[0] == 'viber_validity_time': message.viber_validity_time = row[iField]
                if field[0] == 'viber_photo': message.viber_photo = row[iField]
                if field[0] == 'viber_btn_text': message.viber_btn_text = row[iField]
                if field[0] == 'viber_btn_ancour': message.viber_btn_ancour = row[iField]
                if field[0] == 'sms_alpha': message.sms_alpha = row[iField]
                if field[0] == 'sms_message': message.sms_message = row[iField]
                if field[0] == 'sms_validity_time': message.sms_validity_time = row[iField]
                if field[0] == 'infobip_status': message.infobip_status = row[iField]
                if field[0] == 'channel': message.channel = row[iField]
                if field[0] == 'status': message.status = row[iField]
            msgs_lst.append(message)
        return msgs_lst

    @tornado.gen.coroutine
    def getFinishReports(self):
        try:
            cursor = yield self.db.execute("SELECT infobip_id FROM bulks_wait WHERE status = 2 AND (viber_validity_time + sms_validity_time) + insert_time < EXTRACT(EPOCH FROM NOW())::INT")
            row = cursor.fetchall()[0]
            print(row)
            return row
        except psycopg2.Error as ex:
            print(ex)

    @tornado.gen.coroutine
    def authenticate(self, login, password):
        try:
            cursor = yield self.db.execute("SELECT * FROM users WHERE login = %s", (login,))
            row = cursor.fetchall()
            if not row:
                print("No such user in system!!!")
                logging.warning("No such user in system!!!")
                return None
            pass_from_base = row[0][2].encode('utf8')
            if bcrypt.hashpw(password.encode('utf8'), pass_from_base) == pass_from_base:
                logging.info("User " + str(row[0][1]) + ' enter in system!!!')
                return True
            else:
                logging.warning('Not correct password for user: ' + str(row[0][1]))
                return None
        except Exception as ex:
            print(ex)