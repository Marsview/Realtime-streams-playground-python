# Realtime-streams-playground-python
Marsview Realtime Speech Analytics API
Client end code for Marsview Speech Analytics APIs

⚠️ Audio should be of format LINEAR16 at 16000hz for best performance

## Step 1:
Installing the dependencies for the python application
  ```
  $ pip install pyaudio==0.2.11
  $ pip install "python-socketio[client]"=5.3.0
  ```

## Step 2:
Signup on [Marsview portal](app.marsview.ai) and fetch API Key and API Token
Update these values in py-client.py
![IM-1](https://gblobscdn.gitbook.com/assets%2F-MaxSab-_c4clZreM9ft%2F-McUJSnRlslrM7wCcAdb%2F-McUJx4lF7WPJBxCsk4o%2FScreenshot%202021-06-18%20at%207.02.35%20PM.png?alt=media&token=c466bae4-6b04-4b85-b1eb-4ed02a169538)

## Step 3:
Paste the  API key, secret and user_id in the space provided for these keys and run the python script (py-client.py)

It will take some time to authenticate the user, generate Transaction and initiate stream. You can start speaking when you see the following logs in the console

```
Token is valid
* recording
```


## Handling response:

You will get the response in the following function inside the code. 
```
@sio.event
def output(data):
    data = json.loads(data)
    print(data)
    print('Trascript : ', data.get('sentence'))
    print('Sentiment : ', data.get('sentiment'))
    print('Intent : ', data.get('intent'))
    print('Tone : ', data.get('tone'))
    print('Statement Tag : ', data.get('dialog_tag'))
    print('Emotion : ', data.get('emotion'))
```

⚠️ Audio should be of format LINEAR16 at 16000hz for best performance
