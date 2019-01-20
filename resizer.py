#!/usr/bin/env python
import pika
import sys
import subprocess
import os

exchange = 'checinsm-minify'
queue = 'direct'
routing_key = ''

print("%s --[%s]--> %s" % (exchange, routing_key, queue))
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue=queue, durable=True)
channel.queue_bind(queue=queue, exchange=exchange, routing_key=routing_key)

def callback(ch, method, properties, body):
    print(" [x] Received %r, %s" % (body, method))
    head, tail = os.path.split(body)
    subprocess.call(["/usr/bin/convert", body, "-resize", "64x64",  "static/mini/"+tail]) # where the imagemagick is
    
    #channel.basic_ack(delivery_tag=method.delivery_tag)

#channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback,
                      queue=queue,
                      no_ack=False)

channel.start_consuming()
