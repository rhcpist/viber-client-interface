import time
import os
import datetime
import json
import tornado.template
import logging
import re
import csv

from modules.db import MomokoDB
from modules.message import Message, MessageStatus
from modules.viber_sender import ViberSender
from tornado import web, ioloop, gen, escape

__DOWNLOADS__ = "downloads/"

logging.basicConfig(format = u'%(levelname)-8s [%(asctime)s] %(message)s', level = logging.DEBUG, filename = u'logs/app.log')

db = MomokoDB()

sender = ViberSender( "startmobile" , "A017Bk" , db )

@gen.engine
def sender_reports():
    while True:
        try:
            yield sender.getReports()
        except Exception as ex:
            print(ex)
        finally:
            yield gen.sleep( 1 )

@gen.engine
def sender_message():
    max_sent = 50
    logging.info("Start server loop. The maximum count of messages in Infobip: " + str(max_sent) )
    yield sender.getScenarios()

    while True:
        try:
            count_send = yield db.getCountSend()
            print('Count of messages to Infobip send: ' + str(count_send))
            if count_send > max_sent : continue
            logging.info("Count of messages to send: " + str(max_sent - count_send))
            messages = yield db.getMessagesWaitSend( max_sent - count_send )
            for message in messages :
                message.status = MessageStatus.SEND
                yield db.setMessages(message)
                logging.info("Message with id " + str(message.id()) + " was sended to Infobip. Status " + str(message.status))
                sender.send( message )
        except Exception as ex:
            print( ex )
        finally:
            yield gen.sleep( 1 )


class Saver(web.RequestHandler):
    def post(self, *args, **kwargs):
        time_start = time.time()
        self.preperedData(
             json_data=self.get_argument('json_data'),
             bulk_name=self.get_argument('name-bulk'),
             viber_alpha=self.get_argument('viber-alpha'),
             viber_message=self.get_argument('viber-message'),
             viber_validity_time=int(self.get_argument('viber_validity_time')) * 3600,
             viber_photo=None if self.get_argument('viber-photo', False) == False else self.get_argument('viber-photo'),
             viber_btn_text=None if self.get_argument('viber-button-text', False) == False else self.get_argument('viber-button-text'),
             viber_btn_ancour=None if self.get_argument('viber-button-ancour', False) == False else self.get_argument('viber-button-ancour'),
             sms_alpha=self.get_argument('sms-alpha'),
             sms_message=self.get_argument('sms-message'),
             sms_validity_time=int(self.get_argument('sms_validity_time')) * 3600,
             send_time=int(time.mktime(datetime.datetime.strptime(self.get_argument('send_time'), "%d.%m.%Y %H:%M").timetuple())),
             user=tornado.escape.json_decode(self.get_secure_cookie("user"))
        )
        #self.finish(" Data is uploaded!! ")
        self.redirect("/")

    @gen.coroutine
    def preperedData(self, json_data, bulk_name, viber_alpha, viber_message, viber_validity_time, viber_photo, viber_btn_text, viber_btn_ancour, sms_alpha, sms_message, sms_validity_time, send_time, user):

        messeges = []
        start = time.time()
        print('Start reating array data to POST' )
        for item in json.loads( json_data ):
            params_json = re.split(r";|,", item)

            messege = Message()
            messege.username = user
            messege.infobip_id = None
            messege.bulk_name = bulk_name

            if len(params_json) > 1:
                messege.abon_number = params_json[0]
                pattern1 = re.sub(r"Row_", '', str(viber_message))
                messege.viber_message = pattern1.format(*params_json)
                pattern2 = re.sub(r"Row_", '', str(sms_message))
                messege.sms_message = pattern2.format(*params_json)
            else:
                messege.abon_number = item
                messege.viber_message = viber_message
                messege.sms_message = sms_message

            messege.viber_alpha = viber_alpha
            messege.viber_validity_time = viber_validity_time
            messege.viber_photo = viber_photo
            messege.viber_btn_text = viber_btn_text
            messege.viber_btn_ancour = viber_btn_ancour
            messege.sms_alpha = sms_alpha
            messege.sms_validity_time = sms_validity_time
            messege.send_time = send_time
            messege.insert_time = int(time.time())
            messege.infobip_status = None
            messege.channel = None
            messege.status = 0

            messeges.append( messege )
        print('Finish create data to post' + str(time.time()-start))
        start = time.time()
        print('Start INSERT ' + str(len(messeges)) + ' row')
        db.setMessages( messeges )
        print('Finish INSERT ' + str(time.time() - start))

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def get_login_url(self):
        return self.redirect("/login")

    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if user_json:
            return tornado.escape.json_decode(user_json)
        else:
            return None

    def write_error(self, status_code, **kwargs):
        self.render("error.html", status_code=status_code)

class MainHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        self.render("create.html")

class LoginHandler(BaseHandler):
    def get(self):
        self.render("login.html", next=self.get_argument("next", "/"))

    @gen.coroutine
    def post(self):
        username = self.get_argument("login")
        password = self.get_argument("password")

        auth = yield db.authenticate(username, password)
        if auth:
            self.set_current_user(username)
            self.redirect(self.get_argument("next", u"/"))
        else:
            #error_msg = u"?error=" + tornado.escape.url_escape("login or pass incorrect")
            self.redirect(u"/login")

    def set_current_user(self, user):
        if user:
            self.set_secure_cookie("user", tornado.escape.json_encode(user), expires_days=0.0125)
        else:
            self.clear_cookie("user")
            self.redirect("/login")

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/login")

class ShowAll(LoginHandler):
    @gen.coroutine
    def get(self):
        if not self.get_current_user() :
            self.redirect("/login")
            return
        self.set_current_user(self.get_current_user())
        list_of_bulks = []
        bulks = yield db.getUserBulks(self.get_current_user())
        for bulk in bulks:
            list_of_bulks.append( [bulk[0], datetime.datetime.fromtimestamp(int(bulk[1])).strftime('%Y-%m-%d %H:%M:%S'), bulk[2], bulk[3] ] )
        self.render("index.html", title="My_text", mess=list_of_bulks)

class BulkItem(LoginHandler):
    @gen.coroutine
    def get(self):
        if not self.get_current_user() :
            self.redirect("/login")
            return
        self.set_current_user(self.get_current_user())
        bulkName = self.get_arguments("name")[0]
        bulkTime = self.get_arguments("time")[0]
        bulk = yield db.getBulkItem(bulkName, bulkTime)

        statistic = {
            'Название рассылки': bulk[0][0],
            'Колличество сообщений': bulk[0][1],
            'Доставлено сообщений': bulk[0][2],
            'В процессе доставки': bulk[0][3],
            'Не доставлено': bulk[0][4],
            'Статус рассылки': bulk[0][5],
            'Время начала рассылки': datetime.datetime.fromtimestamp(int(bulk[0][6])).strftime('%Y-%m-%d %H:%M:%S'),
            'Время создания рассылки': datetime.datetime.fromtimestamp(int(bulk[0][7])).strftime('%Y-%m-%d %H:%M:%S'),
            'Тип рассылки': bulk[0][8]
        }
        progressbar = [ bulk[0][1], bulk[0][2] + bulk[0][3] + bulk[0][4] ]
        viberstat = [ bulk[0][9], bulk[0][10], bulk[0][11], bulk[0][12], bulk[0][13] ]
        smsstat = [ bulk[0][14], bulk[0][15], bulk[0][16] ]
        chart1 = [ bulk[0][2], bulk[0][3], bulk[0][4] ]
        chart2 = [ bulk[0][17], bulk[0][18] ]

        btn_prev = self.request.headers.get('Referer')
        self.render("omni.html", bulkinfo = statistic, progress = progressbar, viber_info = viberstat, sms_info = smsstat, chart1 = chart1, chart2 = chart2, btn_prev = btn_prev, bulk_name = bulkName, bulk_time = bulkTime )

class Downloads(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        filename = "stats.csv"
        if os.path.isfile(__DOWNLOADS__ + filename):
            os.remove(__DOWNLOADS__ + filename)
        bulkName = self.get_arguments("name")[0]
        bulkTime = self.get_arguments("time")[0]

        data = yield db.exportCSV(bulkName, bulkTime)
        with open(__DOWNLOADS__ + filename, "w") as csv_file:
            writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for line in data:
                writer.writerow(line)

        hfile = open(__DOWNLOADS__ + filename, "r")
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s' % filename)
        self.write(hfile.read())

settings = dict(
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    cookie_secret="gjkelge93l3436kl346hl36h3k4612k",
    debug=True
)

if __name__ == "__main__":
    application = web.Application([
        (r"/create", MainHandler),
        (r"/login", LoginHandler),
        (r"/logout", LogoutHandler),
        (r"/save", Saver),
        (r"/", ShowAll),
        (r"/omni", BulkItem),
        (r"/export", Downloads)
    ], **settings)

    application.listen(8889)
    main_loop = ioloop.IOLoop.instance()
    main_loop.add_callback( sender_message )
    main_loop.add_callback( sender_reports )
    main_loop.start()