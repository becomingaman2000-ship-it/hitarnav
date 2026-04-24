import argparse
import math
import cv2
import numpy as np


def detect_rooms(img, min_area=2000):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 200, 255, cv2.THRESH_BINARY_INV)

    # Morphology to close gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rooms = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue

        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

        # Accept contours that are roughly rectangular (4 or more vertices)
        if len(approx) >= 4:
            x, y, w, h = cv2.boundingRect(approx)
            cx = x + w // 2
            cy = y + h // 2
            rooms.append({'rect': (x, y, w, h), 'centroid': (cx, cy), 'area': area})

    return rooms


def build_mst(points):
    # Prim's algorithm for MST on points using Euclidean distance
    n = len(points)
    if n == 0:
        return []
    visited = [False] * n
    visited[0] = True
    edges = []
    for _ in range(n - 1):
        best = None
        best_d = float('inf')
        for i in range(n):
            if not visited[i]:
                continue
            for j in range(n):
                if visited[j]:
                    continue
                dx = points[i][0] - points[j][0]
                dy = points[i][1] - points[j][1]
                d = math.hypot(dx, dy)
                if d < best_d:
                    best_d = d
                    best = (i, j)
        if best is None:
            break
        i, j = best
        visited[j] = True
        edges.append((i, j))
    return edges


def draw_overlay(img, rooms, edges, out_path):
    vis = img.copy()
    # draw room rectangles and centroids
    for r in rooms:
        x, y, w, h = r['rect']
        cx, cy = r['centroid']
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 200, 0), 2)
        cv2.circle(vis, (cx, cy), 4, (0, 0, 255), -1)

    # draw corridors (MST edges)
    for i, j in edges:
        p1 = rooms[i]['centroid']
        p2 = rooms[j]['centroid']
        # draw an L-shaped corridor: horizontal then vertical
        mid = (p2[0], p1[1])
        cv2.line(vis, p1, mid, (255, 0, 0), 6)
        cv2.line(vis, mid, p2, (255, 0, 0), 6)

    cv2.imwrite(out_path, vis)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', required=True, help='Input floorplan image path')
    parser.add_argument('--output', '-o', default='map_output.png', help='Output image path')
    parser.add_argument('--min-area', type=int, default=2000, help='Minimum contour area to be considered a room')
    args = parser.parse_args()

    img = cv2.imread(args.input)
    if img is None:
        raise SystemExit(f'Failed to open image: {args.input}')

    rooms = detect_rooms(img, min_area=args.min_area)
    points = [r['centroid'] for r in rooms]
    edges = build_mst(points)
    draw_overlay(img, rooms, edges, args.output)
    print(f'Wrote {args.output} with {len(rooms)} rooms and {len(edges)} corridors')


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""Detect rectangular rooms in a floorplan image and draw corridors between them.

Usage:
    python scripts/draw_map.py "ChatGPT Image Apr 16, 2026, 01_35_30 PM (2).png" out.png

This script uses OpenCV to detect contours that look like room boxes, computes
their centroids, then connects centroids using a minimum spanning tree so the
resulting lines resemble a corridor network. The output image is saved to the
path you provide.
"""
import math
import sys
import os
from collections import namedtuple

try:
    import cv2
    import numpy as np
except Exception as e:
    print("Missing dependency (cv2/numpy). Please install: pip install opencv-python numpy")
    raise


def find_room_rects(img, debug=False):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    # Use adaptive threshold and invert so boxes (dark lines) are white
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 21, 5)

    # Morphological closing to join broken box lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    Rect = namedtuple('Rect', 'x y w h area cx cy')
    rects = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 2000:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        if w < 30 or h < 30:
            continue
        # filter extremely tall or thin shapes
        ar = max(w / h, h / w)
        if ar > 8:
            continue

        cx = x + w // 2
        cy = y + h // 2
        rects.append(Rect(x, y, w, h, area, cx, cy))

    # Sort by area descending and remove nested/duplicate boxes using IoU
    rects.sort(key=lambda r: r.area, reverse=True)
    kept = []
    def iou(a, b):
        xa1, ya1, xa2, ya2 = a.x, a.y, a.x + a.w, a.y + a.h
        xb1, yb1, xb2, yb2 = b.x, b.y, b.x + b.w, b.y + b.h
        xi1 = max(xa1, xb1); yi1 = max(ya1, yb1)
        xi2 = min(xa2, xb2); yi2 = min(ya2, yb2)
        if xi2 <= xi1 or yi2 <= yi1:
            return 0.0
        inter = (xi2 - xi1) * (yi2 - yi1)
        union = a.area + b.area - inter
        return inter / union

    for r in rects:
        skip = False
        for k in kept:
            if iou(r, k) > 0.25:
                skip = True
                break
        if not skip:
            kept.append(r)

    if debug:
        print(f"Found {len(kept)} room-like rectangles")

    return kept


def mst_edges(points):
    # Kruskal on complete graph (sufficient for small n)
    n = len(points)
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            dx = points[i][0] - points[j][0]
            dy = points[i][1] - points[j][1]
            d = math.hypot(dx, dy)
            edges.append((d, i, j))
    edges.sort(key=lambda e: e[0])

    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        parent[rb] = ra
        return True

    mst = []
    for d, i, j in edges:
        if union(i, j):
            mst.append((i, j))
            if len(mst) == n - 1:
                break
    return mst


def draw_map(input_path, output_path, debug=False):
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError(f"Cannot open image: {input_path}")

    rects = find_room_rects(img, debug=debug)
    points = [(r.cx, r.cy) for r in rects]

    out = img.copy()
    # Draw detected rectangles
    for r in rects:
        cv2.rectangle(out, (r.x, r.y), (r.x + r.w, r.y + r.h), (0, 200, 0), 2)
        cv2.circle(out, (r.cx, r.cy), 4, (0, 0, 255), -1)

    if len(points) >= 2:
        edges = mst_edges(points)
        # Draw corridors (thick semi-transparent lines)
        for i, j in edges:
            p1 = points[i]
            p2 = points[j]
            cv2.line(out, p1, p2, (0, 0, 255), 10)

    # Optionally overlay semi-transparent corridor (blend)
    alpha = 0.85
    blended = cv2.addWeighted(out, alpha, img, 1 - alpha, 0)
    cv2.imwrite(output_path, blended)
    print(f"Saved output: {output_path}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    inp = sys.argv[1]
    outp = sys.argv[2]
    draw_map(inp, outp, debug=True)
