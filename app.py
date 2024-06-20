from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import requests
import xml.etree.ElementTree as ET
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, ping_interval=300, ping_timeout=1800)

# 로그인 요청 XML
soap_request_login = """
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:eds="http://tt.com.pl/eds/">
   <soap:Header/>
   <soap:Body>
      <eds:login>
         <eds:username>admin</eds:username>
         <eds:password>ovation1</eds:password>
         <eds:type>CLIENT-TYPE-DEFAULT</eds:type>
      </eds:login>
   </soap:Body>
</soap:Envelope>
"""

# 로그인 요청 보내기
response_login = requests.post(
    url="http://172.16.31.100:43080",
    headers={"Content-Type": "application/soap+xml"},
    data=soap_request_login,
    timeout=1800
)

# 로그인 응답 처리
root = ET.fromstring(response_login.text)
namespace = {'soap': 'http://www.w3.org/2003/05/soap-envelope', 'eds': 'http://tt.com.pl/eds/'}
auth_string_element = root.find('.//eds:authString', namespace)

if auth_string_element is not None:
    auth_string = auth_string_element.text
    print(f"Auth String: {auth_string}")
else:
    raise Exception('Auth-String을 추출하지 못했습니다. 로그인 요청에 문제가 있습니다.')

# 개별 포인트 데이터를 가져오는 함수
def get_point_value(point):
    soap_request_get_point = f"""
    <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:eds="http://tt.com.pl/eds/">
       <soap:Header/>
       <soap:Body>
          <eds:getPoints>
             <eds:authString>{auth_string}</eds:authString>
             <eds:filter>
                <eds:iessRe>{point}</eds:iessRe>
             </eds:filter>
             <eds:startIdx>0</eds:startIdx>
             <eds:maxCount>1</eds:maxCount>
          </eds:getPoints>
       </soap:Body>
    </soap:Envelope>
    """

    response_get_point = requests.post(
        url="http://172.16.31.100:43080",
        headers={"Content-Type": "application/soap+xml"},
        data=soap_request_get_point,
        timeout=180
    )

    root = ET.fromstring(response_get_point.text)
    namespace = {'soap': 'http://www.w3.org/2003/05/soap-envelope', 'eds': 'http://tt.com.pl/eds/'}
    point_element = root.find('.//eds:points', namespace)
    
    if point_element is not None:
        iess_element = point_element.find('.//eds:iess', namespace)
        av_element = point_element.find('.//eds:av', namespace)
        
        if iess_element is not None and av_element is not None:
            iess = iess_element.text
            value = av_element.text
            print(f"Point: {iess}, Value: {value}")  # 각 포인트와 값을 출력
            return {iess: value}
    return {point: "N/A"}

def background_thread():
    points_list = [
        'TOTAL-MW.UNIT0@OVATION', 'G1-DWATT.UNIT0@OVATION', 'G2-DWATT.UNIT0@OVATION', 'GEN-W.UNIT0@OVATION',
        'TOTAL-HEAT.UNIT0@OVATION', 'CHP-HEAT.UNIT0@OVATION', 'PLB-HEAT.UNIT0@OVATION', 'HE-CALORY-TOTAL.UNIT0@OVATION',
        'SUPPLY-HEAT.UNIT0@OVATION', 'WHOLESALE.UNIT0@OVATION', 'TIT-4047.UNIT0@OVATION', 'ACC-HEAT.UNIT0@OVATION',
        'NO1-NOX.UNIT0@OVATION', 'NO2-NOX.UNIT0@OVATION', 'CP-DP.UNIT0@OVATION', 'TIT-4037.UNIT0@OVATION'
    ]

    while True:
        data = {}
        for point in points_list:
            data.update(get_point_value(point))
        socketio.emit('live_data', data)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    thread = threading.Thread(target=background_thread)
    thread.daemon = True
    thread.start()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, log_output=True, use_reloader=False)
