import random
import string
import time
import json
import paho.mqtt.client as mqtt
import argparse
import datetime
import uuid

IOT_ENDPOINT = "avt319l6989mq-ats.iot.us-east-2.amazonaws.com"
PORT = 8883
CA_PATH = "connect_device_package/root-CA.crt"
CERT_PATH = "connect_device_package/rfid-tester.cert.pem"
KEY_PATH = "connect_device_package/rfid-tester.private.key"
TOPIC = "rfid/tq"

connected_flag = False

def random_rfid():
    # UUID4를 사용하여 고유한 ID 생성 후 8자리로 축약
    uid = str(uuid.uuid4()).replace('-', '')[:8]
    return f"RFID{uid}"

def on_connect(client, userdata, flags, rc):
    global connected_flag
    print("Connected with result code", rc)
    if rc == 0:
        connected_flag = True
    else:
        print("Connection failed! Check certs, endpoint, policy, etc.")

def on_publish(client, userdata, mid):
    print("Message published. mid:", mid)

def on_log(client, userdata, level, buf):
    print("LOG:", buf)

def on_disconnect(client, userdata, rc):
    print("Disconnected with result code", rc)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("package_id", type=str, help="패키지 ID를 입력하세요.")
    parser.add_argument("quantity", type=int, help="생성할 RFID 개수를 입력하세요.")
    args = parser.parse_args()
    package_id = args.package_id
    quantity = args.quantity
    
    # client_id를 랜덤하게 지정 (중복 방지)
    client_id = "rfid-tester-" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    client = mqtt.Client(client_id=client_id)
    client.tls_set(ca_certs=CA_PATH, certfile=CERT_PATH, keyfile=KEY_PATH)
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_log = on_log
    client.on_disconnect = on_disconnect
    client.connect(IOT_ENDPOINT, PORT, 60)
    client.loop_start()

    # 연결될 때까지 대기
    while not connected_flag:
        time.sleep(0.1)

    for _ in range(quantity):
        rfid = random_rfid()
        payload = json.dumps({"rfid_id": rfid, "package_id": package_id, "tq_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        result = client.publish(TOPIC, payload)
        print(f"Published: {payload}, result: {result.rc}")
        time.sleep(1)
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    main()
