import uuid

class AppData:
    KEY_USER_TOKEN = 'USER_TOKEN'
    KEY_DEVICE_ID = 'DEVICE_TOKEN'
    KEY_FIRE_TOKEN = 'FIREBASE_TOKEN'

    device_id = ''
    user_token = ''
    fire_token = ''
    location = (0.0, 0.0)

    def setDeviceID(self, d_id=None):
        if d_id == None:
            self.device_id = str(uuid.uuid4().hex)
        else:
            self.device_id = d_id
        return

    def getDeviceID(self):
        return self.device_id

    def setFireToken(self, token):
        self.fire_token = token
        return

    def getFireToken(self):
        return self.fire_token

    def getLocation(self):
        return self.location

    def setLocation(self, loc):
        self.location = loc
        return
