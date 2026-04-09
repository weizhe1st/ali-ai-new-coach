#!/usr/bin/env python3
"""
测试 MediaPipe 姿态分析功能
"""

import sys
import cv2
import numpy as np

print("🔍 测试 MediaPipe 姿态分析...\n")

# 1. 导入 MediaPipe
try:
    import mediapipe as mp
    print(f"✅ MediaPipe 版本：{mp.__version__}")
except Exception as e:
    print(f"❌ MediaPipe 导入失败：{e}")
    sys.exit(1)

# 2. 初始化姿态分析
try:
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    print("✅ MediaPipe Pose 初始化成功")
except Exception as e:
    print(f"⚠️ MediaPipe Pose 初始化失败：{e}")
    print("   尝试使用简化模式...")
    pose = None

# 3. 测试视频分析
test_video = '/home/admin/.openclaw/workspace/media/inbound/video-1775691707124.mp4'

import os
if not os.path.exists(test_video):
    print(f"\n❌ 测试视频不存在：{test_video}")
    sys.exit(1)

print(f"\n📹 测试视频：{os.path.basename(test_video)}")

cap = cv2.VideoCapture(test_video)

if not cap.isOpened():
    print("❌ 无法打开视频")
    sys.exit(1)

print(f"✅ 视频打开成功")
print(f"   帧率：{cap.get(cv2.CAP_PROP_FPS)}")
print(f"   帧数：{int(cap.get(cv2.CAP_PROP_FRAME_COUNT))}")

# 4. 分析视频
frame_count = 0
detected_frames = 0
metrics = {
    'elbow_angles': [],
    'knee_angles': [],
    'shoulder_angles': []
}

print("\n🔍 开始分析视频...")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_count += 1
    
    # 每 5 帧分析一次
    if frame_count % 5 != 0:
        continue
    
    # 转换为 RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    if pose:
        try:
            results = pose.process(rgb_frame)
            
            if results.pose_landmarks:
                detected_frames += 1
                landmark = results.pose_landmarks.landmark
                
                # 计算肘部角度（右侧）
                if all(landmark[i].visibility > 0.5 for i in [12, 14, 16]):
                    p1 = np.array([landmark[12].x, landmark[12].y])
                    p2 = np.array([landmark[14].x, landmark[14].y])
                    p3 = np.array([landmark[16].x, landmark[16].y])
                    angle = calculate_angle(p1, p2, p3)
                    metrics['elbow_angles'].append(angle)
                
                # 计算膝盖角度（右侧）
                if all(landmark[i].visibility > 0.5 for i in [24, 26, 28]):
                    p1 = np.array([landmark[24].x, landmark[24].y])
                    p2 = np.array([landmark[26].x, landmark[26].y])
                    p3 = np.array([landmark[28].x, landmark[28].y])
                    angle = calculate_angle(p1, p2, p3)
                    metrics['knee_angles'].append(angle)
                
                # 计算肩部角度
                if all(landmark[i].visibility > 0.5 for i in [12, 11, 23]):
                    p1 = np.array([landmark[12].x, landmark[12].y])
                    p2 = np.array([landmark[11].x, landmark[11].y])
                    p3 = np.array([landmark[23].x, landmark[23].y])
                    angle = calculate_angle(p1, p2, p3)
                    metrics['shoulder_angles'].append(angle)
        
        except Exception as e:
            # 跳过错误帧
            continue

cap.release()

# 5. 输出结果
print(f"\n✅ 分析完成！")
print(f"   总帧数：{frame_count}")
print(f"   检测到姿态：{detected_frames} 帧 ({detected_frames/frame_count*100:.1f}%)")

if metrics['elbow_angles']:
    print(f"\n📊 肘部角度统计:")
    print(f"   最大值：{max(metrics['elbow_angles']):.1f}°")
    print(f"   最小值：{min(metrics['elbow_angles']):.1f}°")
    print(f"   平均值：{sum(metrics['elbow_angles'])/len(metrics['elbow_angles']):.1f}°")

if metrics['knee_angles']:
    print(f"\n📊 膝盖角度统计:")
    print(f"   最大值：{max(metrics['knee_angles']):.1f}°")
    print(f"   最小值：{min(metrics['knee_angles']):.1f}°")
    print(f"   平均值：{sum(metrics['knee_angles'])/len(metrics['knee_angles']):.1f}°")

if metrics['shoulder_angles']:
    print(f"\n📊 肩部角度统计:")
    print(f"   最大值：{max(metrics['shoulder_angles']):.1f}°")
    print(f"   最小值：{min(metrics['shoulder_angles']):.1f}°")
    print(f"   平均值：{sum(metrics['shoulder_angles'])/len(metrics['shoulder_angles']):.1f}°")

print("\n✅ MediaPipe 姿态分析功能正常！")


def calculate_angle(p1, p2, p3):
    """计算三点角度"""
    ba = p1 - p2
    bc = p3 - p2
    norm = np.linalg.norm(ba) * np.linalg.norm(bc)
    if norm < 1e-8:
        return 0.0
    cosine = np.dot(ba, bc) / norm
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))
