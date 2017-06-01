# -*- coding: utf-8 -*-
import os
import re
import time
import boto3
import threading
import traceback
import json
import requests
import datetime
from fqueue import FileQueue


import logging
logger = logging.getLogger("uploader")

HUDL_URL = "https://www.hudl.com"
UPDATE_INTERVAL = 15
QUEUE_NAME = "fifo"
ISO_8601 = "%Y-%m-%dT%H:%M:%SZ"


class OperType:
    UPLOAD = 'upload'


class Uploader(object):
    def __init__(self):
        self.queue = FileQueue(QUEUE_NAME)
        self._process_queue()
        self.quit = False
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.start()

    def stop(self):
            logger.info('stopping')
            self.quit = True
            self.thread.join()
            logger.info('stopped')

    def run(self):
        logger.info("running")
        while not self.quit:
            try:
                while not self.quit:
                    self._process_queue()
                    # wait cadence
                    for i in range(UPDATE_INTERVAL):
                        if self.quit:
                            break
                        time.sleep(1)
            except Exception:
                logger.error(traceback.format_exc())
                for i in range(UPDATE_INTERVAL):
                    if self.quit:
                        break
                    time.sleep(1)
        logger.info("exiting")

    def push(self, upload_data):
        logger.debug('queque upload_data: {}'.format(upload_data))
        self.queue.push(json.dumps({'oper_type': OperType.UPLOAD, 'upload_data': upload_data}))

    def _process_queue(self):
        count = 0
        oper_str = self.queue.head()
        if not oper_str:
            return
        try:
            while oper_str:
                oper = json.loads(oper_str)
                logger.info('processing oper: {}'.format(oper))
                if oper['oper_type'] == OperType.UPLOAD:
                    self._upload_video(oper['upload_data'])
                self.queue.pop()
                count = count + 1
                oper_str = self.queue.head()
        except Exception:
            logger.error(traceback.format_exc())
        if count > 0:
            logger.info("processed {} queued opers".format(count))

    def _upload_video(self, data):
        logger.info('uploading video: {}'.format(data))
        # TODO: get from config file
        USERNAME = "mjaner@mediapro.es"
        PASSWORD = "123456"
        UPLOAD_SERVER = 149
        ##
        headers = {'content-type': 'application/json'}
        session = requests.Session()

        # do login
        logger.debug('login')
        payload = {'username': USERNAME, 'password': PASSWORD, 'rememberMe': False}
        response = session.post(HUDL_URL + '/login', data=json.dumps(payload), headers=headers)
        body = response.json()
        if 'success' not in body or not body['success']:
            logger.error('Error in login, status: {}, body: {}, cookies: {}'.format(response.status_code, response.text, session.cookies))
            raise Exception("Error in login to Hudl")
        # get user_id
        m = re.compile('u=([0-9]*)').search(session.cookies.get('ident'))
        user_id = m.groups()[0]
        logger.debug('user_id: {} '.format(user_id))

        # get the team
        # ASSUMPTION: there is only one
        logger.debug('get Team and Season')
        response = session.get(HUDL_URL + '/api/v2/teams', headers=headers)
        body = response.json()
        if not isinstance(body, list) or len(body) < 1:
            logger.error('Team not found, status: {}, body: {}'.format(response.status_code, response.text))
            raise Exception('No Team has been found in Huld')
        # get team id
        team_id = body[0]['teamId']
        team_name = body[0]['name']
        logger.debug('Team: {} ({})'.format(team_name, team_id))
        # get season
        current_seasons = [s for s in body[0]['seasons'] if s['isCurrentSeason']]
        if len(current_seasons) < 1:
            error_str = 'No Season has been found for team: {} ({})'.format(team_name, team_id)
            logger.error(error_str)
            raise Exception(error_str)
        season_id = current_seasons[0]['seasonId']
        season_name = current_seasons[0]['name']
        logger.debug('Season: {} ({})'.format(season_name, season_id))

        # create upload event
        logger.debug('get upload Event')
        event_date_played = data['date_played_utc']
        payload = {
            'teamId': team_id,
            'seasonId': season_id,
            'team1': {'teamId': team_id},
            'team2': {'name': data['team_away']},
            'type': data['event_type'],
            'dateUploaded': datetime.datetime.utcnow().strftime(ISO_8601),
            'datePlayed': event_date_played,
            'name': data['name']
        }
        response = session.post(HUDL_URL + '/api/v2/teams/' + team_id + '/events', data=json.dumps(payload), headers=headers)
        if response.status_code != 200:
            logger.error('Error creating upload event: ' + response.text)
            raise Exception('Error creating upload event')
        # get event_id
        body = response.json()
        event_id = body['eventId']
        logger.debug('upload eventId: ' + event_id)

        # get video segment info
        logger.debug('get video info')
        filepath = data['video']
        file_info = os.stat(filepath)
        logger.debug('video info: {}'.format(file_info))
        # video name
        # caveat: only works for paths that are in same os platform
        file_name = os.path.basename(filepath)
        file_extension = file_name.split('.')[-1]
        # video file size in bytes
        file_size = file_info.st_size
        media_time = event_date_played
        logger.debug('video name: {}, size: {}, time: {}'.format(file_name, file_size, media_time))

        # create video segment
        logger.debug('create video segment')
        upload_key = '{}/{}/{}/{}.{}'.format(user_id[::-1], team_id[::-1], event_id, data['_id'], file_extension)
        payload = {
            'segments': [{
                'sourceFileName': file_name,
                'sourceFileSize': file_size,
                'uploadFileName': file_name,
                'uploadFileSize': file_size,
                'status': 4,
                'mediaTime': media_time,
                'quality': 50,
                'order': 0,
                'contentServerId': UPLOAD_SERVER,
                'key': upload_key,
                'bucket': 'upload-only-hudlvid',
                'source': 'Hudl'
            }]
        }
        response = session.post(HUDL_URL + '/api/v2/teams/{}/events/{}/segments'.format(team_id, event_id), data=json.dumps(payload), headers=headers)
        logger.debug('response status: {}, body: {}'.format(response.status_code, response.text))
        body = response.json()
        segment_id = body['segmentIds'][0]
        logger.debug('segment_id: ' + segment_id)

        # start upload
        payload = {'numSegments': 1}
        response = session.post(HUDL_URL + '/api/v2/teams/{}/events/{}/start-upload'.format(team_id, event_id), data=json.dumps(payload), headers=headers)
        logger.debug('response status: {}, body: {}'.format(response.status_code, response.text))

        # get amazon upload credentials
        logger.debug('get amazon credentials')
        response = session.post(HUDL_URL + '/events/teams/{}/{}/upload-credentials?uploadServerId={}'.format(team_id, event_id, UPLOAD_SERVER), data='', headers=headers)
        logger.debug('response status: {}, body: {}'.format(response.status_code, response.text))
        body = response.json()
        s3_access_key = body['accessKey']
        s3_secret_key = body['secretKey']
        s3_session_token = body['sessionToken']
        logger.debug('s3_access_key: {}, s3_secret_key: {}, s3_session_token: {}'.format(s3_access_key, s3_secret_key, s3_session_token))

        # upload to s3
        logger.debug('connection to Amazon S3')
        s3_client = boto3.client('s3', aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key, aws_session_token=s3_session_token)
        logger.debug('uploading file')
        with open(filepath, 'rb') as data:
            s3_client.upload_fileobj(data, 'upload-only-hudlvid', upload_key)
        logger.debug('file uploaded')

        # complete segment
        logger.debug('complete segment')
        response = session.post(HUDL_URL + '/api/v2/teams/{}/events/{}/segments/{}/segment-complete'.format(team_id, event_id, segment_id), data='', headers=headers)
        logger.debug('response status: {}, body: {}'.format(response.status_code, response.text))

        # complete upload
        logger.debug('complete upload')
        payload = {'numberOfFiles': 1}
        response = session.post(HUDL_URL + '/api/v2/teams/{}/events/{}/web-upload-complete'.format(team_id, event_id), data=json.dumps(payload), headers=headers)
        logger.debug('response status: {}, body: {}'.format(response.status_code, response.text))
