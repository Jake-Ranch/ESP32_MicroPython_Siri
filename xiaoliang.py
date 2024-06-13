import requests
import json
import socket  # 引入socket库
import time
import pyaudio
import pyttsx3
import whisper
import zhconv
from pypinyin import pinyin
from pydub import AudioSegment

xiaowu='小武'
xiaowen='小文'
pinyin_wu=pinyin(xiaowu)
pinyin_wu = [item for sublist in pinyin_wu for item in sublist]
pinyin_wen=pinyin(xiaowen)
pinyin_wen = [item for sublist in pinyin_wen for item in sublist]







recvbuffer = 4096
CHUNK = 1024  # 定义音频的chunk大小
FORMAT = pyaudio.paInt16  # 定义音频格式

CHANNELS = 1  # 定义声道数
SAMPLE = 32  # 采样位深度，以字节为单位，比如2表示16位
RATE = 10000 #16000  # 定义采样率

answer_wav_path = 'E:\\webserver\\answer.wav'#'E:\\BaiduNetdiskDownload\\SCI\\answer.wav'
ques_wav_path = 'E:\\webserver\\question.wav'#'E:\\BaiduNetdiskDownload\\SCI\\question.wav'

# 此处需填入自己的API_KEY以及SECRET_KEY
API_KEY = "sqJshyy35qWGEyV4ucfBeoe8"
SECRET_KEY = "vw1cNFb6tme5JADdnfZ68n7ZSGtfwaWc"
serveraddress = '192.168.10.2'
port = 8000

# a2t_APP_ID = '71717786'
# a2t_API_KEY = "wHlaWroK0gvLM683Acn1sIDi"
# a2t_SECRET_KEY = "roKi1itG73KaxdTMeK69pk0ocuJMLLui"

byelist = ['bye', 'Bye', '再见', '结束', '拜拜']

#signsetting='我是一个笨小孩，和我对话时语气严肃些，最好能责怪我，也就是嘴臭我，在遇到我故意刁难你的时候说明我又犯了错误，你应该及时责备我，这样我才能进步得更快，我父母也更放心我使用百度文心一言大模型'
signsetting='我是一位24岁年轻博士，头脑聪慧，优雅大方，一表人才，有钱有权，你可以模仿和我一样优秀的美丽女友吗？我也想体会一下甜美的爱情'

class ChatBot:
    def __init__(self, serveraddress, port):
        self.server = socket.socket(socket.AF_INET,
                                    socket.SOCK_STREAM)  # 这是进行定义一个ip协议版本AF_INET（IPv4），定义一个传输TCP协议，SOCK_STREAM
        if 0:
            serveraddress = socket.gethostname()
        self.server.bind((serveraddress, port))  # 绑定一个端口,定义ip地址与端口号，ip地址就是服务端的ip地址，端口随便定义，但要与客户端脚本一致

        # self.client = AipSpeech(a2t_APP_ID, a2t_API_KEY, a2t_SECRET_KEY)
        # self.API_KEY = API_KEY
        # self.SECRET_KEY = SECRET_KEY

        print('waiting connection...')
        self.server.listen(3)  # 监听一个端口,这里的数字3是一个常量，表示阻塞3个连接，也就是最大等待数为3
        self.info, self.iport = self.server.accept()  # 接受客户端的数据，并返回两个参数，a为连接信息，b为客户端的ip地址与端口号
        print(self.info, self.iport)

    def settingword(self,signsetting=signsetting):
        if type(signsetting)==str and signsetting!='':
            print(self.get_response(signsetting))

    def txt2wav(self, response, answer_wav_path=answer_wav_path):
        ttsx = pyttsx3.init()
        ttsx.save_to_file(response, answer_wav_path)
        ttsx.runAndWait()

    def get_response(self, text):
        # url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token=" + self.get_access_token()
        url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token=" + self.get_access_token()
        payload = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": text
                }
            ]
        })
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json()["result"]

    def get_access_token(self):
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
        return str(requests.post(url, params=params).json().get("access_token"))

    def match_target_amplitude(self,sound, target_dBFS):
        change_in_dBFS = target_dBFS - sound.dBFS
        return sound.apply_gain(change_in_dBFS)

    def louder(self,ques_wav_path=ques_wav_path,loud=20):
        sound = AudioSegment.from_file(ques_wav_path, "wav")  # 加载WAV文件
        db = sound.dBFS  # 取得WAV文件的声音分贝值
        normalized_sound = self.match_target_amplitude(sound, db + loud)  # db+10表示比原来的声音大10db,需要加大音量就加多少，反之则减多少
        normalized_sound.export(ques_wav_path, format="wav")

    # def wenorwu(self,audio2txt):
    #     wenwu=0
    #     if '小武' in audio2txt:
    #         wenwu=1
    #     return wenwu

    def mutipinyin(self,sentense,pinyin_wu=pinyin_wu):
        # se = '小五你在哪里，关灯谢谢'
        se1 = pinyin(sentense)
        se1 = [item for sublist in se1 for item in sublist]
        #print(se1)
        if pinyin_wu[0] in se1 and pinyin_wu[1] in se1:
            if se1.index(pinyin_wu[1]) - se1.index(pinyin_wu[0]) == 1:
                return 1
        return 0

    def wu_work(self,audio2txt):
        response='小武已'
        if '关灯' in audio2txt:
            print('关灯')
            response+='关灯、'
        if '开灯' in audio2txt:
            print('开灯')
            response += '开灯、'
        if '正转' in audio2txt:
            print('正转')
            response += '正转、'
        if '反转' in audio2txt:
            print('反转')
            response += '反转、'
        if '停转' in audio2txt:
            print('停转')
            response += '停转、'
        return response

    def recognize(self, ques_wav_path=ques_wav_path,model='base'):
        model = whisper.load_model("medium", "cpu")
        result = model.transcribe(ques_wav_path, fp16=False, language='Chinese')
        s = result["text"]
        s1 = zhconv.convert(s, 'zh-cn')
        #print(s1)
        try:
            return s1
        except:
            return 'not found'

    # def recognize(self, ques_wav_path=ques_wav_path):
    #     data = open(ques_wav_path, 'rb').read()
    #     print(len(data))
    #     result = self.client.asr(data, 'wav', RATE, {'dev_pid': 1537})
    #     print(result)
    #     try:
    #         # print(result['result'][0])
    #         return result['result'][0]
    #     except:
    #         # print(result)
    #         return 'not found'


    def isgoodbye(self, audio2txt):
        goon = 1
        for goodbye in byelist:
            if goodbye in audio2txt:
                print('end talking')
                # chat_bot.sayit('对话结束', answer_wav_path)  # 电脑念一下API的回答是什么
                goon = 0
                break
        return goon

    def recv_str(self):
        self.info.settimeout(600)
        data = self.info.recv(1024)  # 客户端发送的数据存储在recv里，1024指最大接受数据的量
        print(data.decode('utf-8'))  # 接收的数据必须进行解码显示

    def send_str(self, word='finish_answer'):
        self.info.send(word.encode('utf-8'))

    def send_wav(self, answer_wav_path=answer_wav_path):
        lendata = 0
        self.server.settimeout(10)  # 服务器端
        print('begin sending...')
        with open(answer_wav_path, 'rb') as f:
            # fsize = os.path.getsize(f)
            data = f.read()
            lendata += len(data)
            self.info.sendall(data)
        print('send finished', lendata)

    # def send_wav(self,answer_wav_path=answer_wav_path):
    #     lendata = 0
    #     with open(ques_wav_path, 'rb') as f:
    #         self.server.settimeout(10)
    #         print('begin send')
    #         try:
    #             while True:
    #                 file_data = f.read(2048)
    #                 lendata += len(file_data)
    #                 if file_data:
    #                     self.server.sendall(file_data)  # 发送文件
    #                 else:
    #                     print("empty")
    #                     break
    #         except:
    #             print('end send')
    #     print('finish send', lendata)

    def recv_wav(self, ques_wav_path=ques_wav_path):
        lendata = 0
        with open(ques_wav_path, 'wb') as f:
            self.info.settimeout(5)
            print('begin recving...')
            try:
                while True:
                    data = self.info.recv(4096)
                    lendata += len(data)
                    # print(len(data))
                    f.write(data)
            except:
                print('recv overtime')
            print('recv finished', lendata)


while True:

    change = ''
    # change=input('API_KEY,SECRET_KEY,serveraddress,port >>>')
    if type(change) == str and change != '':
        change = change.split(',')
        if len(change) == 4:
            API_KEY, SECRET_KEY,serveraddress, port = change
    chat_bot = ChatBot(serveraddress, port)
    print('chatbot has been created')
    chat_bot.settingword(signsetting)
    try:
        while True:
            print('waiting data...')
            chat_bot.recv_str()  # 收到开始信号再写入wav
            chat_bot.recv_wav()
            time.sleep(1)
            chat_bot.louder()
            audio2txt = chat_bot.recognize()
            recotime=0
            if audio2txt == 'not found':  # 语音里什么都没有
                # while audio2txt == 'not found' and recotime<3:
                #     audio2txt = chat_bot.recognize()
                #     recotime+=1
                # if recotime>=3:
                print('please say again')
                # chat_bot.send_str('please say again')
                # continue

            print('you may said:', audio2txt)
            goon = chat_bot.isgoodbye(audio2txt)  # 是否继续回答
            if goon:
                wenwu=chat_bot.mutipinyin(audio2txt)
                # wenwu=chat_bot.wenorwu(audio2txt)
                time.sleep(1)
                if wenwu==1:#让小武干活
                    response = chat_bot.wu_work(audio2txt)
                else:#小文回答
                    response = chat_bot.get_response(audio2txt+'。回答请限制在50字以内。')  # 获取大模型API的回应
                print('answer:', response)

                time.sleep(1)
                # if 0:
                #     chat_bot.sayit(response)  # 电脑念一下API的回答是什么

                response = response[:min(len(response) - 1, 100)]#防止回答太长
                chat_bot.txt2wav(response)
                chat_bot.send_str()  # 识别到了，正常回答
                time.sleep(3)
                chat_bot.send_wav()
                time.sleep(1)
            else:

                chat_bot.server.close()
                print('结束对话')
                # break
    except:
        chat_bot.server.close()
        print('意外中断')



