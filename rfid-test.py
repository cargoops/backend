import random
import string
import time
import json
import paho.mqtt.client as mqtt

IOT_ENDPOINT = "avt319l6989mq-ats.iot.us-east-2.amazonaws.com"
PORT = 8883
CA_PATH = "connect_device_package/root-CA.crt"
CERT_PATH = "connect_device_package/rfid-tester.cert.pem"
KEY_PATH = "connect_device_package/rfid-tester.private.key"
TOPIC = "rfid/scan"

def random_rfid():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    if rc != 0:
        print("Connection failed! Check certs, endpoint, policy, etc.")

def on_publish(client, userdata, mid):
    print("Message published. mid:", mid)

def on_log(client, userdata, level, buf):
    print("LOG:", buf)

def on_disconnect(client, userdata, rc):
    print("Disconnected with result code", rc)

def main():
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
    for _ in range(10):
        rfid = random_rfid()
        payload = json.dumps({"rfid_id": rfid, "timestamp": int(time.time())})
        result = client.publish(TOPIC, payload)
        print(f"Published: {payload}, result: {result.rc}")
        time.sleep(1)
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    main()
