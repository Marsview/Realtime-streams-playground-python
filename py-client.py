import pyaudio
import socketio
import json 
import requests
from six.moves import queue
sio = socketio.Client()

@sio.event
def connect():
    print("I'm connected!")
@sio.event
def connect_error(data):
    print("The connection failed!")

@sio.event
def disconnect():
    print("I'm disconnected!")

# @sio.event
# def messages(sid, data):
#     print(data)

@sio.event
def output(data):
    data = json.loads(data)
    print(data)
    print('Trascript : ', data.get('sentence'))
    print('Sentiment : ', data.get('sentiment'))
    print('Intent : ', data.get('intent'))
    print('intent Phrase', data.get('intentPhrase'))
    print('Tone : ', data.get('tone'))
    print('Emotion : ', data.get('emotion'))
    print('Statement-Question-Command : ', data.get('sqc'))
    print('Preset Statement Tag : ', data.get('presetStatementTag'))
    print('Custom Statement Tag : ', data.get('customStatementTag'))

    print("=============================================================================")

@sio.event
def valid_token(data):
    print('Token is valid')
    send_binary_data()
@sio.event
def invalid_token(data):
    print('Token is Invalid')



class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)

def get_token(apiKey, apiSecret, userId):
    API_ENDPOINT =  "https://api.marsview.ai/cb/v1/auth/create_access_token"
    payload = {
            "apiKey": apiKey,
            "apiSecret": apiSecret,
            "userId": userId
            }

    r = requests.post(url = API_ENDPOINT, data = payload)
    token = json.loads(r.text)['data']['accessToken']
    print(token)
    return token

def initiate_transaction(token, model_configs):
    # importing the requests library
    
    # defining the api-endpoint 
    API_ENDPOINT = "https://streams.marsview.ai/rb/v1/streams/setup_realtime_stream"

    

    data = {
        "channels":2,
        "modelConfigs" : model_configs}

    headers = {'Authorization': f'Bearer {token}'}
    # sending post request and saving response as response object
    r = requests.post(url = API_ENDPOINT, json = data, headers = headers)
    
    pastebin_url = json.loads(r.text)['data']
    txnId = pastebin_url['txnId']
    channelId = pastebin_url['channels'][0]['channelId']

    print("txnId : ", txnId)
    print("channelId : ", channelId)

    sio.connect('https://streams.marsview.ai', auth={'txnId': txnId, 'channelId': channelId, 'token':token})
    sio.emit('startStream', '')

def send_binary_data():
    
    
    RATE = 16000
    CHUNK = int(RATE / 10)

    print("* recording")
    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        for content in audio_generator:
            sio.emit('binaryData', content)
        

if __name__ == '__main__':
    api_secret = '<API_SECRET>'
    api_key = '<API_KEY>'
    user_id = '<USER_ID>'

    # config data for intents and statement tag models had to be created and the ids are given here, for which apis are available
    model_configs = {
        "intent_analysis":{
            "intents":[
                        # "intent-1c6q62hzkxj2farq-1640270029382",
                        # "intent-1c6q62hzkxj4gm3m-1640273449953"
                        ]},
        "custom_statement_tag_analysis":{
            "statement_tag_ids":[
                # "statement-bxllq5imjkx68e6tb-1639493995007",
                # "statement-bxllq1zsuzkvuj44go-1636609624728",
                ],
            "use_tag_level_threshold":True
            },

        }
    token = get_token(api_key, api_secret, user_id)
    initiate_transaction(token, model_configs)