#!/usr/bin/python

import cv2
import cv2.cv as cv
import numpy as np
import serial
import sys
import getopt
import socket
import thread


TRESH = 60
AREA = 500
RED = (0, 0, 255)
GREEN = (0, 255, 0)
WIDTH = 320
HEIGHT = 240
ROI_HEIGHT = 50


def get_centers(frame, verbose = False):
    roi = frame [(WIDTH / 2 - ROI_HEIGHT / 2):(WIDTH / 2 + ROI_HEIGHT / 2), 0:WIDTH]
    roiImg = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    ret, roiImg = cv2.threshold(roiImg, TRESH , 255, 0)
    cv2.bitwise_not(roiImg, roiImg)      # negative image

    erodeElmt = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilateElmt = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    cv2.erode(roiImg, erodeElmt)
    cv2.dilate(roiImg, dilateElmt)

    contours, hierarchy = cv2.findContours(
        roiImg, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)


    centers = []
    for i in contours:
        area = cv2.contourArea(i)
        moments = cv2.moments(i)

        if area > AREA:
            if verbose: print 'Found area of %f' % area
            if moments['m00'] != 0.0:
                if moments['m01'] != 0.0:
                    cx = int(moments['m10'] / moments['m00'])         # cx = M10/M00
                    cy = int(moments['m01'] / moments['m00'])         # cy = M01/M00
                    centers.append((cx, cy))
                    if verbose: print 'Found center in (%s, %s)' % (cx, cy)

                    y_offset = WIDTH / 2 - ROI_HEIGHT / 2
                    cv2.circle(frame, (cx, cy + y_offset), 4, RED, -1)
                    cv2.circle(frame,(cx,cy + y_offset), 8, GREEN, 0)
                    x,y,w,h = cv2.boundingRect(i)
                    cv2.rectangle(frame, (x ,y + y_offset), (x+w, y+h+y_offset), GREEN, 2)

    return centers, frame

def start_server(callback):
    server = socket.socket()
    hp = (ip, port)
    server.bind(hp)
    server.listen(5)
    print 'Waiting for connection on %s:%d' % hp
    client, addr = server.accept()
    print 'Connection from', addr
    write_header(client)
    callback(client)

def write_header(client, boundary = '1337'):
    client.send("HTTP/1.0 200 OK\r\n" +
            "Connection: close\r\n" +
            "Max-Age: 0\r\n" +
            "Expires: 0\r\n" +
            "Cache-Control: no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0\r\n" +
            "Pragma: no-cache\r\n" +
            "Content-Type: multipart/x-mixed-replace; " +
            "boundary=" + boundary + "\r\n" +
            "\r\n" +
            "--" + boundary + "\r\n")

def write_frame(client, frame, boundary = '1337'):
    ret = cv.EncodeImage('.jpeg', cv.fromarray(frame))
    image_bytes = bytearray(np.asarray(ret))
    client.send("Content-type: image/jpeg\r\n")
    client.send("Content-Length: %d\r\n\r\n" % len(image_bytes))
    client.send(image_bytes)
    client.send("\r\n--" + boundary + "\r\n")



if __name__ == '__main__':

    try:
        options, args = getopt.getopt(sys.argv[1:],
            'r:vsp:i:', ['redbot=', 'verbose', 'stream', 'port=', 'ip='])
    except getopt.GetoptError as err:
        print str(err)
        print 'Usage: ' + ['redbot=', 'verbose', 'stream', 'port=', 'ip='].join(', ')
        sys.exit(2)

    redbot_port = '/dev/ttyUSB0'
    verbose = False
    stream = False
    port = 1337
    ip = '127.0.0.1'

    for opt, arg in options:
        if opt in ('-r', '--redbot'):
            redbot_port = arg
        elif opt in ('-v', '--verbose'):
            verbose = True
        elif opt in ('-s', '--stream'):
            stream = True
        elif opt in ('-p', '--port'):
            port = arg
        elif opt in ('-i', '--ip'):
            ip = arg

    client = None
    if stream:
        def set_client(c): global client; client = c
        thread.start_new_thread(start_server, (set_client, ))

    ser = serial.Serial(redbot_port, 9600)

    cap = cv2.VideoCapture(0)
    cap.set(cv.CV_CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv.CV_CAP_PROP_FRAME_HEIGHT, HEIGHT)

    try:
        while True:
            line = ser.readline().replace('\n', '').replace('\r', '')
            if line.startswith('ready'):
                ret, frame = cap.read()

                centers, frame_after = get_centers(frame, verbose)

                if client != None:
                    write_frame(client, frame_after)

                if len(centers) > 0:
                    error = 1.0 - 2.0 * centers[0][0] / WIDTH
                else:
                    error = 0
                print 'Error:', error

                ser.write(str(error) + '\r\n')
            else:
                print 'Recv:', line
    except KeyboardInterrupt:
        print 'Closing...'
        ser.write("stop" + "\r\n")
        if client != None:
            client.close()
