import json

class MessageStatus() :
    WAIT_SEND = 0
    SEND = 1
    ACCEPT = 2
    REJECT = 3
    DELIVERED = 4
    EXPIRED = 5
    UNDELIVERABLE = 6


class Message:

    __id = None

    username = None
    infobip_id = None
    bulk_name = None
    insert_time = None
    send_time = None
    abon_number = None

    viber_alpha = None
    viber_message = None
    viber_validity_time = None

    viber_photo = None
    viber_btn_text = None
    viber_btn_ancour = None

    sms_alpha = None
    sms_message = None
    sms_validity_time = None

    infobip_status = None
    channel = None
    status = None

    def __init__(self , id = None ) :
        self.__id = id
        pass

    def id(self) : return self.__id

    def getDict(self):
        return {
            "id" : self.__id,
            "infobip_id": self.infobip_id,
            "username": self.username,
            "bulk_name": self.bulk_name,
            "abon_number": self.abon_number,
            "viber_alpha": self.viber_alpha,
            "viber_message": self.viber_message,
            "viber_validity_time": self.viber_validity_time,
            "viber_photo": self.viber_photo,
            "viber_btn_text": self.viber_btn_text,
            "viber_btn_ancour": self.viber_btn_ancour,
            "sms_alpha": self.sms_alpha,
            "sms_message": self.sms_message,
            "sms_validity_time": self.sms_validity_time,
            "send_time": self.send_time,
            "insert_time": self.insert_time,
            "infobip_status": self.infobip_status,
            "channel": self.channel,
            "status": self.status
        }

    def getList(self):
        return (
            self.__id,
            self.infobip_id,
            self.username,
            self.bulk_name,
            self.insert_time,
            self.send_time,
            self.abon_number,
            self.viber_alpha,
            self.viber_message,
            self.viber_validity_time,
            self.viber_photo,
            self.viber_btn_text,
            self.viber_btn_ancour,
            self.sms_alpha,
            self.sms_message,
            self.sms_validity_time,
            self.infobip_status,
            self.channel,
            self.status,
        )

class CreateBulk:
    name_bulk = "",
    file_param = "",
    viber_alpha = "",
    viber_message = "",
    media_param = None,
    sms_alpha = "",
    sms_message = "",
    send_time = ""

    def __init__(self, name_bulk, file_param, viber_alpha, viber_message, media_param, sms_alpha, sms_message, send_time):
        self.name_bulk = name_bulk
        self.file_param = file_param
        self.viber_alpha = viber_alpha
        self.viber_message = viber_message
        self.media_param = media_param
        self.sms_alpha = sms_alpha
        self.sms_message = sms_message
        self.send_time = send_time

    def __repr__(self):
       return "<ViberBulk:\n name_bulk:%s,\n file_param:%s,\n viber_alpha:%s,\n viber_message:%s,\n media_param: [ %s, %s, %s ]\n sms_alpha:%s,\n sms_message:%s,\n send_time:%s\n >" % (self.name_bulk, self.file_param, self.viber_alpha, self.viber_message, self.media_param[0], self.media_param[1], self.media_param[2], self.sms_alpha, self.sms_message, self.send_time)


    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False, indent=4, ensure_ascii=False)