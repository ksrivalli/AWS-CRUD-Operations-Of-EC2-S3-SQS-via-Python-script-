import boto3
import time

ec2_client = boto3.client('ec2')
s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')

def create_EC2_instance(instance_name):
    print("Requesting EC2 instance creation.....")
    instances = ec2_client.run_instances(
        ImageId='ami-0e86e20dae9224db8',  # Replace with the Ubuntu AMI ID you found
        InstanceType='t2.micro',  # Free Tier eligible instance type
        MinCount=1,
        MaxCount=1,
        KeyName='EC2-CSE546',  # Replace with your actual key pair name
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': instance_name  # Replace with your desired instance name
                    }
                ]
            }
        ]
    )
    instance_id = instances['Instances'][0]['InstanceId']
    print(f"EC2 instance created: {instance_id}")
    return instance_id


def create_S3_bucket(bucket_name):
    print("Requesting S3 bucket creation ......")
    s3_client.create_bucket(
        Bucket=bucket_name
    )
    print(f"S3 bucket created: {bucket_name}")
    return bucket_name

def create_SQS_queue(queue_name):
    print("Requesting SQS queue creation .....")
    queue = sqs_client.create_queue(
        QueueName = queue_name,
        Attributes={'FifoQueue': 'true'}
    )
    print(f"SQS queue created: {queue_name}")
    return queue['QueueUrl']

def list_resources():
    print("Listing all resources.....")
    #Listing EC2 Instances
    instances = ec2_client.describe_instances()
    instance_info = []

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_state = instance['State']['Name']  # State of the instance
            instance_info.append((instance_id, instance_state))
    
    if instance_info:
        print("EC2 Instances:")
        for instance_id, state in instance_info:
            print(f"  Instance ID: {instance_id}, State: {state}")
    else:
        print("No EC2 instances found.")

    #Listing S3 buckets
    buckets = s3_client.list_buckets()
    if buckets['Buckets']:
        print("S3 Buckets:")
        for bucket in buckets['Buckets']:
            print(f"  Bucket Name: {bucket['Name']}")
    else:
        print("No S3 buckets found.")

    #List SQS queues
    queues = sqs_client.list_queues()
    if 'QueueUrls' in queues:
        print("SQS Queues:")
        for queue_url in queues['QueueUrls']:
            print(f"  Queue URL: {queue_url}")
    else:
        print("No SQS queues found.")

    print("Resource listing completed.")

def upload_file_to_S3(bucket_name):
    print("Uplaoding file to S3 ......")
    try:
        s3_client.put_object(Bucket=bucket_name, Key="CSE546test.txt", Body="")
        print("File upload successful")
    except Exception as e:
        print(f"Exception: {e}")

def check_message_count_in_sqs(queue_url):
    attributes = sqs_client.get_queue_attributes(
        QueueUrl = queue_url,
        AttributeNames = ['ApproximateNumberOfMessages']
    )
    message_count = int(attributes['Attributes']['ApproximateNumberOfMessages'])
    return message_count


def send_message_to_sqs(queue_url):
    print("Sending message to SQS......")
    sqs_client.send_message(
        QueueUrl = queue_url,
        MessageBody = "This is a test message",
        MessageGroupId = "testGroup",
        MessageDeduplicationId = "testMessage1"
    )
    print("Message sent to SQS: test message.")

def pull_message_from_sqs(queue_url):
    print("Pulling messages from queue....")
    messages = sqs_client.receive_message(
        QueueUrl = queue_url,
        MaxNumberOfMessages = 1,
        WaitTimeSeconds = 10
    )
    if 'Messages' in messages:
        message = messages['Messages'][0]
        print("Message name: test message")
        print(f"Message received: {message['Body']}")
        
    else:
        print("No messages in SQS")

def delete_all_resources():
    print("Deleting all EC2 instances, S3 buckets, and SQS queues...")

    ec2_instances = ec2_client.describe_instances()
    instance_ids = [instance['InstanceId'] for reservation in ec2_instances['Reservations'] for instance in reservation['Instances']]

    if instance_ids:
        ec2_client.terminate_instances(InstanceIds = instance_ids)
        print(f"Terminated instance ids: {instance_ids}")
    else:
        print("No instance ids to terminate")

    
    buckets = s3_client.list_buckets()
    if buckets['Buckets']:
        for bucket in buckets['Buckets']:
            bucket_name = bucket['Name']
            try:
                objects = s3_client.list_objects_v2(Bucket=bucket_name)
                if 'Contents' in objects:
                    for obj in objects['Contents']:
                        s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
                    s3_client.delete_bucket(Bucket=bucket_name)
                print(f"Deleted S3 Bucket: {bucket_name}")
            except Exception as e:
                print(f"Error deleting bucket {bucket_name}: {e}")
    else:
        print("No buckets to delete...")

    
    queues = sqs_client.list_queues()
    if 'QueueUrls' in queues:
        for queue_url in queues['QueueUrls']:
            sqs_client.delete_queue(QueueUrl=queue_url)
            print(f"Deleted SQS queue, Queue URL: {queue_url}")
    else:
        print("No queues to delete")

    print("All resources are now deleted...")



if __name__ == "__main__":
    ec2_instance_name = "EC2-CSE546-SriValliKanumuri-v90311"
    ec2_instance_id = create_EC2_instance(ec2_instance_name)
    s3_bucket_name = "cse546-ec2-bucket-version0311-9-0311"
    create_S3_bucket(s3_bucket_name)
    sqs_queue_name = "CSE546-SQS-SriValliKanumuriv90311.fifo"
    sqs_queue_url = create_SQS_queue(sqs_queue_name)

    print("Request sent, wait for 1 min.")
    time.sleep(60)

    list_resources()

    upload_file_to_S3(s3_bucket_name)

    send_message_to_sqs(sqs_queue_url)

    print("Checking messages in SQS...")
    message_count = check_message_count_in_sqs(sqs_queue_url)
    print(f"Message count in queue: {message_count}")
    pull_message_from_sqs(sqs_queue_url)
    check_message_count_in_sqs(sqs_queue_url)
    print(f"Message count in queue: {message_count}")

    time.sleep(10)

    delete_all_resources()

    time.sleep(60)

    list_resources()
