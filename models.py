import json
import sysparam
import uuid

class CampaignModel:
    def __init__(self, c_id, name, lat, lon, distance, duration, advertiser, content_left, content_right, content_logo,
                 ppm, priority):
        self.campaign_id = c_id
        self.name = name
        self.latitude = lat
        self.longitude = lon
        self.distance = distance
        self.duration = duration
        self.advertiser = advertiser
        self.image_left = content_left
        self.image_right = content_right
        self.logo_link = content_logo
        self.price = ppm
        self.priority = priority


class DisplayedModel:
    def __init__(self, t, lat, lon, strt_lat, strt_lon, stop_lat, stop_lon, camp_id, dur, spd, rti):
        self.time_run = t
        self.latitude = lat
        self.longitude = lon
        self.start_lat = strt_lat
        self.start_lon = strt_lon
        self.stop_lat = stop_lat
        self.stop_lon = stop_lon
        self.camp_id = camp_id
        self.duration = dur
        self.speed = spd
        self.RT_impressions = rti


class BaseRequestModel:
    def __init__(self, user, code, API_KEY, data):
        self.user = user
        self.code = code
        self.api_key = API_KEY
        self.data = data


class BaseResponseModel:
    def __init__(self, result, message, code, data):
        self.result = result
        self.message = message
        self.code = code
        self.data = data


class GetContentModel:
    def __init__(self, stats, lat, lon, cur_campaign, cur_campaign_started, device_id):
        self.logs = stats
        self.latitude = lat
        self.longitude = lon
        self.cur_campaign = cur_campaign
        self.cur_campaign_started = cur_campaign_started
        self.device_id = device_id


class GetTokenModel:
    def __init__(self, device_id, lat, lon, fire_token):
        self.device_id = device_id
        self.latitude = lat
        self.longitude = lon
        self.firebase_token = fire_token


class LogRecordModel:
    def __init__(self, time_stamp, start_lat, start_lon, stop_lat, stop_lon, campaign_id, duration):
        self.log_time = time_stamp
        self.start_lat = start_lat
        self.start_lon = start_lon
        self.stop_lat = stop_lat
        self.stop_lon = stop_lon
        self.campaign_id = campaign_id
        self.duration = duration


class LogStatModel:
    def __init__(self, time_stamp, start_lat, start_lon, stop_lat, stop_lon, campaign_id, duration):
        self.log_time = time_stamp
        self.start_lat = start_lat
        self.start_lon = start_lon
        self.stop_lat = stop_lat
        self.stop_lon = stop_lon
        self.campaign_id = campaign_id
        self.duration = duration


class ResponseModel:
    def __init__(self, title, link, thumb):
        self.title = title
        self.link = link
        self.thum_link = link


class TokenModel:
    def __init__(self, token):
        self.token = token