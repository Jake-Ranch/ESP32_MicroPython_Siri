from machine import Pin, ADC,I2S, SPI,SoftI2C,SoftSPI
from time import sleep
import time,network,socket, ssd1306,os,uos, utime,_thread
from sdcard import SDCard

SD_CS = Pin(5)
sck_sd=Pin(18)
mosi_sd=Pin(23)
miso_sd=Pin(19)

sd = SDCard(SoftSPI(-1,sck=sck_sd, mosi=mosi_sd,miso=miso_sd), SD_CS)
vfs = os.VfsFat(sd)# fat挂载卡到⽬录下
os.mount(sd,"/sd")# SD/sd

# 摇杆
ps2_y = ADC(Pin(27))
ps2_y.atten(ADC.ATTN_11DB)  # 这里配置测量量程为3.3V
ps2_x = ADC(Pin(4))
ps2_x.atten(ADC.ATTN_11DB)  # 这里配置测量量程为3.3V
ps_button=Pin(16,Pin.IN,Pin.PULL_UP)#摇杆按下
# 录音
#sound_analog = ADC(Pin(15))
#sound_analog.atten(ADC.ATTN_11DB)  # 这里配置测量量程为3.3V


#定义led控制对象
led1=Pin(2,Pin.OUT)
button=Pin(36,Pin.IN,Pin.PULL_DOWN)
# 设置 ESP32 的 WiFi 网络
ssid="CMCC-VKY5"
password="VECD5NJM"
ipv4='192.168.10.2'
port=8000
recvbuffer=1024
record_buffer=10240


answer_wav_path='/sd/answer.wav'
ques_wav_path='/sd/question.wav'

CHANNELS=1
SAMPLE=32
RATE=5000

file_duration=10

longer=RATE/file_duration/1000

# 数字量
#p15 = Pin(22, Pin.IN)
#p15.irq(trigger=Pin.IRQ_RISING, handler=sound_func)
#def sound_func(*argc):
#    print("有声音...")

# 创建i2c对象
i2c = SoftI2C(scl=Pin(17), sda=Pin(21))
# 宽度高度
oled_width = 128
oled_height = 64
# 创建oled屏幕对象
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

sck_pin_in = Pin(32)
ws_pin_in = Pin(33)
sd_pin_in = Pin(25)

#sck_pin_out=Pin(12)
#ws_pin_out=Pin(14)
#sd_pin_out=Pin(13)

px=0
py=0
pxold=-1
pyold=-1
reves=0
con=0
middle=1927
gate=800
fast=6
slow=2
fuhaolist=['0','1','2','3','4','5','6','7','8','9','+','*','-','_','=','/','.','@']
show=1
butime=0
SHIFT=1
YES=0
ssid_flag=0
password_flag=0
ipv4_flag=0
port_flag=0
successful=0

global printword
printword=''
    
def clear(printword,show=1):
    global YES
    oled.fill(0)
    if show:
        keyborad_show()#清场后补充一个键盘
    if YES==0:
        info_show()
    else:
        #print(printword)
        message_show(printword)
        printword=''
    return printword
        
def info_show():
    global ssid,password,ipv4,port,ssid_flag,password_flag,ipv4_flag,port_flag
    
    oled.text(str(ipv4),8,0)
    oled.text(str(port),8,8)
    oled.text(str(ssid),8,16)
    oled.text(str(password),8,24)
    
    if ssid_flag:
        loj=16
    elif password_flag:
        loj=24
    elif ipv4_flag:
        loj=0
    elif port_flag:
        loj=8
    if ssid_flag or password_flag or ipv4_flag or port_flag:
        oled.text('>',0,loj)
    
def message_show(printword,showtime=5):
    oled.text(printword,0,0)
    oled.show()
    time.sleep(showtime)
    
def keyborad_show():
    global SHIFT
    addshift=0
    if SHIFT:
        addshift=32
    for i in range(13):
        oled.text(chr(65+addshift+i),i*8,49)
    for i in range(13):
        oled.text(chr(78+addshift+i),i*8,57)
    for i in range(len(fuhaolist)):
        oled.text(fuhaolist[i],104+((i%3)*8),57-8*(i//3))
        
    oled.text('YES',8,36)
    oled.text('DEL',40,36)
    oled.text('SHF',72,36)
    
    
def mouse_reg(px,py):
    global SHIFT,YES,ssid_flag,password_flag,ipv4_flag,port_flag,ssid,password,ipv4,port
    word=''
    py1=py+6
    px1=px+2
        
    if px1<104:#message或者是字母，或者是按键YSD
        if py1<=32:
            if py1<=8:
                #print('ipv4')
                ipv4_flag=1
                ssid_flag=0
                password_flag=0
                port_flag=0
            elif 8<py1<=16:
                #print('port')
                port_flag=1
                ssid_flag=0
                password_flag=0
                ipv4_flag=0
                
            elif 16<py1<=24:
                #print('ssid')
                ssid_flag=1
                password_flag=0
                ipv4_flag=0
                port_flag=0
            elif 24<py1<=32:
                #print('password')
                password_flag=1
                ssid_flag=0
                ipv4_flag=0
                port_flag=0
        else:
            if 36<py1<=42:
                if 8<px1<36:#word='YES'
                    YES=1
                    ssid_flag=0
                    password_flag=0
                    ipv4_flag=0
                    port_flag=0
                elif 40<px1<64:#删除键
                    if ssid_flag:
                        if len(ssid)>0:
                            ssid=ssid[:-1]
                    elif password_flag:
                        if len(password)>0:
                            password=password[:-1]
                    elif ipv4_flag:
                        if len(ipv4)>0:
                            ipv4=ipv4[:-1]
                    elif port_flag:
                        if len(str(port))>0:
                            port=int(str(port)[:-1])
                elif 72<px1<96:#word='SHIFT'
                    if SHIFT==1:
                        SHIFT=0
                    else:
                        SHIFT=1 
            addshift=0
            if SHIFT==1:
                addshift=32
            if 57>py1>49 :
                word=chr(65+addshift+px1//8)
            if py1>=57:
                word=chr(78+addshift+px1//8)
    else:#数字和特殊字符
        word=fuhaolist[min(len(fuhaolist)-1,((66-py1)//8)*3+(px1-104)//8)]

    if ssid_flag:
        ssid+=word
    elif password_flag:
        password+=word
    elif ipv4_flag:
        ipv4+=word
    elif port_flag:
        if word in fuhaolist[:10]:#确保是数字
            port=int(str(port)+word)    
    #print(px1,py1,px,py,word)
    
    
def UI(delay):
    global px,py,con,reves,show,butime,SHIFT,YES,ssid_flag,password_flag,ipv4_flag,port_flag,ssid,password,ipv4,port,printword
    while True:
        #print('UI',printword)
        if reves:#闪烁效果
            reves=0
        else:
            reves=1
        if ps_button.value()==0:
            #print(ssid_flag,password_flag,ipv4_flag,port_flag,ssid,password,ipv4,port)
            butime+=1
            if show==1 and pxold != px and pyold != py:
                mouse_reg(px,py)#显示键盘才允许识别键盘
            pxold=px
            pyold=py
        else:
            pxold=-1
            pyold=-1
            butime=0
        if butime>20 and show==1:#两秒长按关闭键盘
            show=0
            butime=0
        elif butime>20 and show==0:
            show=1
            butime=0
        printword=clear(printword,show=show)
        
        speed=slow
        try:
            psx=ps2_x.read()
            psy=ps2_y.read()
        except:
            psx=middle
            psy=middle
        if psx<middle-gate or psx>middle+gate or psy<middle-gate or psy>middle+gate:
            con+=1
            
            if con>10:
                speed=fast
            if psx>middle+gate:
                px-=speed
                px=max(px,0)
            elif psx<middle-gate:
                px+=speed
                px=min(px,120)
            if psy>middle+gate:
                py+=speed
                py=min(py,58)#54
            elif psy<middle-gate:
                py-=speed
                py=max(py,-6)   
        else:
            con=0
            
        if reves or speed==fast:
            oled.text('.',px,py)
        oled.show()
        time.sleep(delay)
        
        
     

# 建立 WiFi 连接
def wifi_connect():
    wlan=network.WLAN(network.STA_IF)#STA模式
    wlan.active(False)#先进行wlan的清除
    wlan.active(True)#再激活
    start_time=time.time()#记录时间做超时判断
    successful=1
    if not wlan.isconnected():
        print("connecting to network…")
        wlan.connect(ssid,password)#输入WiFi账号和密码
        while not wlan.isconnected():
            led1.value(1)
            time.sleep_ms(300)
            led1.value(0)
            time.sleep_ms(300)
            #超时判断，30s未连接成功判定为超时
            if time.time()-start_time>30:
                print("WiFi Connect TimeOut!")
                successful=0
                break
    if wlan.isconnected():
        led1.value(1)
        print("network information:",wlan.ifconfig())
    return successful



def createWavHeader(sampleRate, bitsPerSample, num_channels, datasize):    
    o = bytes("RIFF",'ascii')                                                   # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4,'little')                                   # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE",'ascii')                                                  # (4byte) File type
    o += bytes("fmt ",'ascii')                                                  # (4byte) Format Chunk Marker
    o += (16).to_bytes(4,'little')                                              # (4byte) Length of above format data
    o += (1).to_bytes(2,'little')                                               # (2byte) Format type (1 - PCM)
    o += (num_channels).to_bytes(2,'little')                                    # (2byte)
    o += (sampleRate).to_bytes(4,'little')                                      # (4byte)
    o += (sampleRate * num_channels * bitsPerSample // 8).to_bytes(4,'little')  # (4byte)
    o += (num_channels * bitsPerSample // 8).to_bytes(2,'little')               # (2byte)
    o += (bitsPerSample).to_bytes(2,'little')                                   # (2byte)
    o += bytes("data",'ascii')                                                  # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4,'little')                                        # (4byte) Data size in bytes
    return o
 
def send_wav(ques_wav_path=ques_wav_path):
    lendata=0
    with open(ques_wav_path, 'rb') as f:
        client.settimeout(10)
        print('begin send')
        printword='send begin'
        try:
            while True:
                file_data = f.read(2048)
                lendata+=len(file_data)
                if file_data:
                    client.sendall(file_data) # 发送文件
                else:
                    print("empty")
                    break
        except:
            print('send fail')
    printword='send finished'+str(lendata)
    print('send finished',lendata)
        
def recv_wav(answer_wav_path=answer_wav_path):
    lendata=0
    start=time.time()
    client.settimeout(5)
    print('recv begin')
    printword='recv begin'
    with open(answer_wav_path, 'wb') as f:
        try:
            while True:
                data = client.recv(1024)
                lendata+=len(data)
                f.write(data)
        except:
            #printword='recv overtime'
            print('recv overtime')
    printword='recv finished'+str(lendata)
    print('recv finished',lendata)
        
def send_str():
    client.send('finish_record'.encode('utf-8'))
    
def recv_str():
    client.settimeout(600)
    data = client.recv(1024)  # 客户端发送的数据存储在recv里，1024指最大接受数据的量
    try:
        #print(data.decode('utf-8'))  # 接收的数据必须进行解码显示
        return data.decode('utf-8')
    except:
        print(data)
        return data
    
def record_in(sfile=ques_wav_path, sampleRate=RATE, bitsPerSample=SAMPLE,bufSize=record_buffer,file_duration=file_duration):
    # 连接端口:3.3V SD->G21  WS->G22 SCK->G23  L/R-> 低电频
    audioInI2S = I2S(0,
                     sck=sck_pin_in, ws=ws_pin_in, sd=sd_pin_in,
                     mode=I2S.RX,#mode=I2S.RX,
                     bits=bitsPerSample,
                     format=I2S.MONO,#STEREO
                     rate=sampleRate,
                     ibuf=bufSize)
    #音频数据读取缓冲
    readBuf = bytearray(bufSize)
    #休眠一点时间
    time.sleep(1.0)
    # 检查文件是否存在
    if sfile in uos.listdir():
        # 删除文件
        #print('del', sfile)
        uos.remove(sfile)
        time.sleep(0.5)
    fin = open(sfile, 'wb')
    start_time = time.time()
    head = createWavHeader(sampleRate, bitsPerSample, CHANNELS, int(bufSize*file_duration*8*longer))
    fin.write(head)
    #message=''
    printword='record ready'
    print("record ready.......")
    start=time.time()
    while True:
        # 读取音频数据
        currByteCount = audioInI2S.readinto(readBuf)
        audio_data = bytearray()
        audio_data.extend(readBuf)
        print('record...',time.time()-start)
        fin.write(audio_data)
        if time.time() - start_time >= file_duration:
            break  
    fin.close()
    audioInI2S.deinit()
    printword='record end'
    print('record end')
    
    #sampleRate=RATE, bitsPerSample=SAMPLE,bufSize=record_buffer,file_duration
def play_out(answer_wav_path=answer_wav_path, sampleRate=int(RATE/2), bitsPerSample=SAMPLE,bufSize=record_buffer):#txt2audio.wav
    sck_pin = Pin(12) # 串行时钟输出
    ws_pin = Pin(14)  # 字时钟
    sd_pin = Pin(13)  # 串行数据输出

    # 初始化i2s
    audio_out = I2S(1, sck=sck_pin, ws=ws_pin, sd=sd_pin, mode=I2S.TX, bits=SAMPLE, format=I2S.MONO, rate=10000, ibuf=20000)
     
     
    #wavtempfile = "test.wav"
    with open(answer_wav_path,'rb') as f:
     
        # 跳过文件的开头的44个字节，直到数据段的第1个字节
        pos = f.seek(44) 
     
        # 用于减少while循环中堆分配的内存视图
        wav_samples = bytearray(1024)
        wav_samples_mv = memoryview(wav_samples)
         
        print("start...")
        printword='play out'
        
        #并将其写入I2S DAC
        while True:
            try:
                num_read = f.readinto(wav_samples_mv)
                
                # WAV文件结束
                if num_read == 0: 
                    break
     
                # 直到所有样本都写入I2S外围设备
                num_written = 0
                while num_written < num_read:
                    num_written += audio_out.write(wav_samples_mv[num_written:num_read])
                    
            except Exception as ret:
                print("play fail", ret)
                break
            
    audio_out.deinit()
    printword='play end'
    print('play end')
   
   
   
   

print('init success')

# 创建两个线程
try:
   _thread.start_new_thread(UI,(0.1,))
   print('thread:success')
except:
   print ("Error:thread dail")


while True:
    if YES==1:
        try:
            successful=wifi_connect()#连接wifi
        except:
            YES=0
            print('no wifi work')
        if successful:
            try:
                client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                client.connect((ipv4,port))
                state=0
                print('run main...')
                printword='main running'
                while True:
                    #print('???',printword)
                    if button.value() == 1 and state==0:
                        time.sleep_ms(100)                         # 消抖处理
                        if button.value() == 1:
                            print('push')
                            time.sleep(2)
                            record_in()
                            time.sleep(2)
                            state=1
                            while button.value() == 1:
                                time.sleep_ms(10)
                    elif button.value() == 0 and state==1:
                        state=0
                        time.sleep(1)
                        send_str()
                        time.sleep(1)
                        send_wav()
                        time.sleep(20)
                        message=recv_str()
                        if message=='finish_answer':
                            recv_wav()
                            time.sleep(1)
                            play_out()
                            time.sleep(2)
                            print('I am ready')
                        else:
                            print('say again')
            except:
                YES=0
                print('connect fail')
        
        
            

