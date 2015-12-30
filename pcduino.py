import cv2
import serial


TRESH = 30
counter = 0
RED = (255,0,0)
GREEN = (0,255,0)
WIDTH = 320
HEIGHT = 240
ROI_HEIGHT = 50


def get_centers(frame):
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

        if area > 400: 
            # print 'Found area of %f' % area
            if moments['m00'] != 0.0:
                if moments['m01'] != 0.0:
                    cx = int(moments['m10'] / moments['m00'])         # cx = M10/M00
                    cy = int(moments['m01'] / moments['m00'])         # cy = M01/M00
                    centers.append((cx, cy))
                    # print 'Found center in (%s, %s)' % (cx, cy)

                    cv2.circle(frame, (cx, cy + 80), 4, RED, -1)
                    cv2.circle(frame,(cx,cy+80), 8, GREEN, 0)
                    x,y,w,h = cv2.boundingRect(i)
                    cv2.rectangle(frame, (x ,y+80), (x+w, y+h+80), GREEN, 2)

    return centers


if __name__ == '__main__':
    ser = serial.Serial('/dev/ttyUSB0', 9600)

    cap = cv2.VideoCapture(0)
    ret = cap.set(3, WIDTH)
    ret = cap.set(4, HEIGHT)

    while True:
        line = ser.readline().replace('\n', '').replace('\r', '')
        if line.startswith('ready'):
            ret, frame = cap.read()
            centers = get_centers(frame)
            if len(centers) > 0:
                error = 1.0 - 2.0 * centers[0][0] / WIDTH
            else:
                error = 0
            print 'Error:', error
            ser.write(str(error) + '\r\n')
        else:
            print 'Recv:', line
