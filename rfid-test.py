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

def main():
    client = mqtt.Client()
    client.tls_set(ca_certs=CA_PATH, certfile=CERT_PATH, keyfile=KEY_PATH)
    client.connect(IOT_ENDPOINT, PORT, 60)
    client.loop_start()
    for _ in range(10):
        rfid = random_rfid()
        payload = json.dumps({"rfid_id": rfid, "timestamp": int(time.time())})
        client.publish(TOPIC, payload)
        print(f"Published: {payload}")
        time.sleep(1)
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    main()
