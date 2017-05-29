import json
import base64
import logging
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPRequest

import sys
import tornado.gen

from modules.message import MessageStatus

__UPLOADS__ = "uploads/"

class ViberSender:

    db = None

    __scenarios = {}
    __login = ""
    __password = ""

    bulk_id = None
    abon_number = None
    name_bulk = None
    username = None
    number_list = None
    viber_alpha = None
    viber_message = None
    viber_validity_time = None
    sms_alpha = None
    sms_message = None
    sms_validity_time = None
    viber_photo = None
    viber_btn_text = None
    viber_btn_ancour = None


    def __init__(self, login , password , db ):

        self.db = db
        self.__login = login
        self.__password = password

    @tornado.gen.coroutine
    def getScenarios(self):

        self.__scenarios[ "Pharmacy_www.add.ua" ] = "73612FD297F130F5F364791F16486022"
        self.__scenarios[ "EconomApt_EkonomAptek" ] = "0823B1F604D2C82341015F7C35682F91"
        self.__scenarios[ "Apteka#1_Apteka 1" ] = "9A0C81155BC1739EF8EC50696F1378FD"
        self.__scenarios[ "alutech_Alutech" ] = "CB0DDFFC823F8B7C591343819505DEAD"
        self.__scenarios[ "OLL.TV_OLL.TV" ] = "3A27A4F42A364E781BC149F741D43076"
        self.__scenarios[ "Xtra_TV_Xtra" ] = "A32A3F311F54E8F4ECCE26DB4F473233"
        self.__scenarios[ "MassMart_MassMart" ] = "E16B89AA89F885F6FA7B4EB3E114C28E"
        self.__scenarios[ "LTBjeans_LTBjnsCLUB" ] = "DDD58F0C4895E8E44EE4907DC72D8F97"

        return None

    def __getScenariosKey(self, message ) :
        token = message.viber_alpha + "_" + message.sms_alpha
        if token in self.__scenarios.keys() :
            return self.__scenarios[ token ]

        return None

    def send( self, message ):
        # отправка сообщения
        def sent( response ) :
            response_data = json.loads(response.body)
            print(response_data)
            sys.stdout.write(".")
            message.infobip_id = response_data['messages'][0]['messageId']
            message.infobip_status = response_data['messages'][0]['status']['groupName']
            if message.infobip_status == "UNDELIVERABLE":
                message.status = MessageStatus.UNDELIVERABLE
            elif message.infobip_status == "EXPIRED":
                message.status = MessageStatus.EXPIRED
            elif message.infobip_status == "REJECTED":
                message.status = MessageStatus.REJECT
            elif message.infobip_status == "DELIVERED":
                message.status = MessageStatus.DELIVERED
            else:
                message.status = MessageStatus.ACCEPT
            logging.info("Message with #ID: " + str(message.id()) + " - " + str(message.infobip_status) + " by " + str(message.channel))
            self.db.setMessages( message )

        if self.__getScenariosKey( message ) is None :
            message.status = MessageStatus.REJECT
            logging.warning("Message with #ID: " + str(message.id()) + " - REJECTED. Reason - ScenariosKey mismatch!" )
            self.db.setMessages(message)
            return None

        http_client = AsyncHTTPClient()

        obj = {
            "scenarioKey": self.__getScenariosKey(message),
            "destinations": [ {
                "to": { "phoneNumber": message.abon_number }
            } ],
            "viber": {
                "text": message.viber_message,
                "validityPeriod": int(message.viber_validity_time/60)
            },
            "sms": {
                "text": message.sms_message,
                "validityPeriod": int(message.sms_validity_time/60)
            }
        }

        if message.viber_photo and message.viber_btn_text and message.viber_btn_ancour :
            obj["viber"]["imageURL"] = message.viber_photo
            obj["viber"]["buttonText"] = message.viber_btn_text
            obj["viber"]["buttonURL"] = message.viber_btn_ancour
            obj["viber"]["isPromotional"] = True
        body = json.dumps(obj)
        logging.info(body)

        request_sent = HTTPRequest(
                url="https://api.infobip.com/omni/1/advanced",
                method="POST",
                headers={
                    'accept': "application/json",
                    'authorization': "Basic c3RhcnRtb2JpbGU6QTAxN0Jr",
                    'content-type': "application/json"
                },
                body=body
        )

        return http_client.fetch(request_sent, callback=sent)


    def getReports(self) :

        @tornado.gen.coroutine
        def responceCallback(responce):
            responce_data = json.loads(responce.body)
            logging.info('Responce reports recived: ')
            logging.info(responce_data)
            print( 'Responce recived: ' + json.dumps(responce_data) )
            for report in responce_data[ "results" ] :
                sys.stdout.write("..")
                message = yield self.db.getReportsByInfobipID( report['messageId'] )
                message.infobip_status = report['status']['groupName']
                message.channel = report['channel']

                if message.infobip_status == "UNDELIVERABLE":
                    message.status = MessageStatus.UNDELIVERABLE
                elif message.infobip_status == "EXPIRED":
                    message.status = MessageStatus.EXPIRED
                elif message.infobip_status == "REJECTED":
                    message.status = MessageStatus.REJECT
                elif message.infobip_status == "DELIVERED":
                    message.status = MessageStatus.DELIVERED
                else:
                    message.status = MessageStatus.ACCEPT

                logging.info("Responce for Message with #ID: " + str(message.id()) + " - " + str(message.infobip_status) + " by " + str(message.channel))
                yield self.db.setMessages( message )
                logging.info('Save message: #ID' + str(message.id()) + ' Status: ' + message.infobip_status + ' Channel: ' + message.channel)

        http_client = AsyncHTTPClient()
        request_sent = HTTPRequest(
                url="https://api.infobip.com/omni/1/reports",
                method="GET",
                headers={
                  'authorization': "Basic c3RhcnRtb2JpbGU6QTAxN0Jr",
                  'accept': "application/json"
                }
        )

        return http_client.fetch(request_sent, responceCallback)


    def __genAuthorizationBase64(self) :
        if self.__login and self.__password :
            return base64.b64encode(self.__login + ":" + self.__password)
        else :
            return None
