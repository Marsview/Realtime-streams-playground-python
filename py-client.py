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

@sio.event
def messages(sid, data):
    print(data)

@sio.event
def output(data):
    data = json.loads(data)
    print(data)
    # print('Trascript : ', data.get('sentence'))
    # print('Sentiment : ', data.get('sentiment_stream'))
    # print('Intent : ', data.get('intent_stream'))
    # print('Tone : ', data.get('tone_stream'))

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

    

    data = {'channels':1}
    headers = {'Authorization': f'Bearer {token}'}
    # sending post request and saving response as response object
    r = requests.post(url = API_ENDPOINT, data = data, headers = headers)
    
    pastebin_url = json.loads(r.text)['data']
    txnId = pastebin_url['txnId']
    channelId = pastebin_url['channels'][0]['channelId']


    sio.connect('https://streams.marsview.ai/', auth={'txnId': txnId, 'channelId': channelId, 'token':token, "modelConfigs":model_configs})
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
    model_configs  = {
            'intent_analysis':{
                'intents':
                    ["intent-bxllq2f7hpkrvtyzi3-1627981197627",
                            "intent-bxllq2f7hpkrvtzlkf-1627981226223"]
                            }
          }
    token = get_token(api_key, api_secret, user_id)
    initiate_transaction(token, model_configs)
