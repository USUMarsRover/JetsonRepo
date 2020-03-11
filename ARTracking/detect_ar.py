# @File - Part1_2.py
# @Brief - Part 1 & 2 of submission for project-1 for ENPM 673
# @Authors - Rishabh Choudhary, Akash Atharv, Sanchit Gupta
# @Description - AR tag detection and tracking and placement of lena image 


import numpy as np
import cv2
from matplotlib import pyplot as plt
import copy
import math
from time import time


cap = cv2.VideoCapture(1)


lena_img = cv2.imread('Lena.png')
lena_resize = cv2.resize(lena_img, (200, 200))

dim = 200
p1 = np.array([
    [0, 0],
    [dim - 1, 0],
    [dim - 1, dim - 1],
    [0, dim - 1]], dtype="float32")

# Decode the tag ID and 4 digit binary and orientation
def id_decode(image):
    ret, img_bw = cv2.threshold(image, 200, 255, cv2.THRESH_BINARY)
    corner_pixel = 255
    cropped_img = img_bw[50:150, 50:150]

    block_1 = cropped_img[37, 37]
    block_3 = cropped_img[62, 37]
    block_2 = cropped_img[37, 62]
    block_4 = cropped_img[62, 62]
    white = 255
    if block_3 == white:
        block_3 = 1
    else:
        block_3 = 0
    if block_4 == white:
        block_4 = 1
    else:
        block_4 = 0
    if block_2 == white:
        block_2 = 1
    else:
        block_2 = 0
    if block_1 == white:
        block_1 = 1
    else:
        block_1 = 0

    if cropped_img[85, 85] == corner_pixel:
        return list([block_3, block_4, block_2, block_1]), "BR"
    elif cropped_img[15, 85] == corner_pixel:
        return list([block_4, block_2, block_1, block_3]), "TR"
    elif cropped_img[15, 15] == corner_pixel:
        return list([block_2, block_1, block_3, block_4]), "TL"
    elif cropped_img[85, 15] == corner_pixel:
        return list([block_1, block_3, block_4, block_2]), "BL"

    return None, None


# Function to return the order of points in camera frame
def order(pts):
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    # print(np.argmax(s))
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    # print(np.argmax(diff))
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    # return the ordered coordinates
    return rect

# Function to compute homography between world and camera frame 
def homograph(p, p1):
    A = []
    p2 = order(p)

    for i in range(0, len(p1)):
        x, y = p1[i][0], p1[i][1]
        u, v = p2[i][0], p2[i][1]
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    A = np.array(A)
    U, S, Vh = np.linalg.svd(A)
    l = Vh[-1, :] / Vh[-1, -1]
    h = np.reshape(l, (3, 3))
    # print(l)
    # print(h)
    return h

# Generate contours to detect corners of the tag
def contour_generator(frame):
    test_img1 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    test_blur = cv2.GaussianBlur(test_img1, (5, 5), 0)
    edge = cv2.Canny(test_blur, 75, 200)
    edge1 = copy.copy(edge)
    contour_list = list()

    cnts, h = cv2.findContours(edge1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    index = list()

    if h is None:
        return False

    if h[0] is not None:
        for hier in h[0]:
            if hier[3] != -1:
                index.append(hier[3])

        # loop over the contours
        for c in index:
            peri = cv2.arcLength(cnts[c], True)
            approx = cv2.approxPolyDP(cnts[c], 0.02 * peri, True)

            if len(approx) > 4:
                peri1 = cv2.arcLength(cnts[c - 1], True)
                corners = cv2.approxPolyDP(cnts[c - 1], 0.02 * peri1, True)
                contour_list.append(corners)

        new_contour_list = list()
        for contour in contour_list:
            if len(contour) == 4:
                new_contour_list.append(contour)
        final_contour_list = list()
        for element in new_contour_list:
            if cv2.contourArea(element) < 2500:
                final_contour_list.append(element)

        return final_contour_list
    else:
        return False
# Reorient the tag based on the original orientation
def reorient(location, maxDim):
    if location == "BR":
        p1 = np.array([
            [0, 0],
            [maxDim - 1, 0],
            [maxDim - 1, maxDim - 1],
            [0, maxDim - 1]], dtype="float32")
        return p1
    elif location == "TR":
        p1 = np.array([
            [maxDim - 1, 0],
            [maxDim - 1, maxDim - 1],
            [0, maxDim - 1],
            [0, 0]], dtype="float32")
        return p1
    elif location == "TL":
        p1 = np.array([
            [maxDim - 1, maxDim - 1],
            [0, maxDim - 1],
            [0, 0],
            [maxDim - 1, 0]], dtype="float32")
        return p1

    elif location == "BL":
        p1 = np.array([
            [0, maxDim - 1],
            [0, 0],
            [maxDim - 1, 0],
            [maxDim - 1, maxDim - 1]], dtype="float32")
        return p1

# main function to process the tag
def image_process(frame, p1):
    final_contour_list = contour_generator(frame)
    finalImage = frame.copy()
    if final_contour_list:
        lena_list = list()

        for i in range(len(final_contour_list)):
            cv2.drawContours(frame, [final_contour_list[i]], -1, (0, 255, 0), 2)
            # cv2.imshow("Outline", frame)

            # warped = homogenous_transform(small, final_contour_list[i][:, 0])

            c_rez = final_contour_list[i][:, 0]
            H_matrix = homograph(p1, order(c_rez))

            # H_matrix = homo(p1,order(c))
            tag = cv2.warpPerspective(frame, H_matrix, (200, 200))

            # cv2.imshow("Outline", frame)
            # cv2.imshow("Tag after Homo", tag)

            tag1 = cv2.cvtColor(tag, cv2.COLOR_BGR2GRAY)
            decoded, location = id_decode(tag1)
            empty = np.full(frame.shape, 0, dtype='uint8')
            if not location == None:
                p2 = reorient(location, 200)
                if not decoded == None:
                    print("location", c_rez)
                    H_Lena = homograph(order(c_rez), p2)
                    lena_overlap = cv2.warpPerspective(lena_resize, H_Lena, (frame.shape[1], frame.shape[0]))
                    if not np.array_equal(lena_overlap, empty):
                        lena_list.append(lena_overlap.copy())
                        # print(lena_overlap.shape)

        mask = np.full(frame.shape, 0, dtype='uint8')
        if lena_list != []:
            for lena in lena_list:
                temp = cv2.add(mask, lena.copy())
                mask = temp

            lena_gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
            r, lena_bin = cv2.threshold(lena_gray, 10, 255, cv2.THRESH_BINARY)

            mask_inv = cv2.bitwise_not(lena_bin)

            mask_3d = frame.copy()
            mask_3d[:, :, 0] = mask_inv
            mask_3d[:, :, 1] = mask_inv
            mask_3d[:, :, 2] = mask_inv
            img_masked = cv2.bitwise_and(finalImage, mask_3d)
            finalImage = cv2.add(img_masked, mask)
            # cv2.imshow("Lena", final_image)
            # cv2.waitKey(0)


    cv2.imshow('ouput', finalImage)
    out.write(finalImage)
    if cv2.waitKey(1) & 0xff == 27:
        cv2.destroyAllWindows()

height = 640
width = 800
fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
fps = 30
video_filename = "output" + str(time()) + 'output.avi'
out = cv2.VideoWriter(video_filename, fourcc, fps, (width, height))
count = 0
# Read the input video frame by frame
while cap.isOpened():
    success, frame = cap.read()
    if success == False:
        break

    # width, height, depth = frame.shape
    # print(width, height)
    # img = cv2.resize(frame, (int(height/2), int(width/2)))
    image_process(frame, p1)
    count +=1

    # if count > 600:
    #     break

cap.release()
