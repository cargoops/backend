import random
import string
import time
import json
import paho.mqtt.client as mqtt
import argparse
import datetime
import boto3

IOT_ENDPOINT = "avt319l6989mq-ats.iot.us-east-2.amazonaws.com"
PORT = 8883
CA_PATH = "connect_device_package/root-CA.crt"
CERT_PATH = "connect_device_package/rfid-tester.cert.pem"
KEY_PATH = "connect_device_package/rfid-tester.private.key"
TOPIC = "rfid/bin"

connected_flag = False

def random_rfid():
    return f"RFID{random.randint(1000, 9999)}"

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
    args = parser.parse_args()
    package_id = args.package_id
    
    # bin_allocation과 rfid_ids 모두 조회
    bin_allocation = get_package_bin_allocation(package_id)
    if isinstance(bin_allocation, str):
        bin_allocation = json.loads(bin_allocation)
    rfid_ids = get_rfids_by_package_id(package_id)
    if not bin_allocation or not rfid_ids:
        print("bin_allocation 또는 rfid_ids가 없습니다.")
        return
    total_quantity = sum(bin_allocation.values())
    if total_quantity != len(rfid_ids):
        print(f"개수가 다릅니다. bin_allocation의 합: {total_quantity}, rfid_ids 개수: {len(rfid_ids)}")
        return

    # MQTT 클라이언트 설정
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

    idx = 0
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for bin_id, quantity in bin_allocation.items():
        for _ in range(quantity):
            rfid_id = rfid_ids[idx]
            payload = json.dumps({
                "rfid_id": rfid_id,
                "package_id": package_id,
                "bin_id": bin_id,
                "binned_date": now_str
            })
            result = client.publish(TOPIC, payload)
            print(f"Published: {payload}, result: {result.rc}")
            idx += 1
            time.sleep(0.5)
    client.loop_stop()
    client.disconnect()

def get_package_bin_allocation(package_id):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    table = dynamodb.Table('Packages')
    response = table.get_item(Key={'package_id': package_id})
    item = response.get('Item')
    if not item:
        print("패키지 없음")
        return None
    bin_allocation = item.get('bin_allocation')
    print("bin_allocation:", bin_allocation)
    return bin_allocation

def get_rfids_by_package_id(package_id):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    table = dynamodb.Table('Items')
    response = table.query(
        IndexName='PackageIdIndex',
        KeyConditionExpression=boto3.dynamodb.conditions.Key('package_id').eq(package_id)
    )
    items = response.get('Items', [])
    rfid_ids = [item['rfid_id'] for item in items]
    print("rfid_ids:", rfid_ids)
    return rfid_ids

if __name__ == "__main__":
    main()
