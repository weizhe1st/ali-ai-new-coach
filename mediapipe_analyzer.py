#!/usr/bin/env python3
"""
MediaPipe 姿态分析模块 - 集成到原系统
提供量化指标供 AI 分析参考
"""

import os
import cv2
import numpy as np
import mediapipe as mp


class MediaPipeAnalyzer:
    """MediaPipe 姿态分析器"""
    
    def __init__(self):
        """初始化 MediaPipe"""
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1,
            smooth_landmarks=True
        )
        print("✅ MediaPipe 分析器已初始化")
    
    def analyze_video(self, video_path):
        """
        分析视频，提取姿态量化指标
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            dict: 包含量化指标和统计数据
        """
        
        if not os.path.exists(video_path):
            return {'error': f'视频文件不存在：{video_path}'}
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return {'error': '无法打开视频文件'}
        
        # 视频信息
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        # 初始化指标
        metrics = {
            'video_info': {
                'fps': fps,
                'total_frames': total_frames,
                'duration_sec': duration
            },
            'elbow_angles': [],  # 肘部角度
            'knee_angles': [],   # 膝盖角度
            'shoulder_angles': [],  # 肩部角度
            'hip_angles': [],    # 髋部角度
            'frame_count': 0,
            'detected_frames': 0
        }
        
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_idx += 1
            
            # 每 3 帧分析一次（平衡性能和精度）
            if frame_idx % 3 != 0:
                continue
            
            metrics['frame_count'] += 1
            
            # 转换为 RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            try:
                results = self.pose.process(rgb_frame)
                
                if results.pose_landmarks:
                    metrics['detected_frames'] += 1
                    landmark = results.pose_landmarks.landmark
                    
                    # 计算关键角度
                    angles = self._calculate_key_angles(landmark)
                    
                    if angles['elbow_right'] is not None:
                        metrics['elbow_angles'].append(angles['elbow_right'])
                    
                    if angles['knee_right'] is not None:
                        metrics['knee_angles'].append(angles['knee_right'])
                    
                    if angles['shoulder_right'] is not None:
                        metrics['shoulder_angles'].append(angles['shoulder_right'])
                    
                    if angles['hip_right'] is not None:
                        metrics['hip_angles'].append(angles['hip_right'])
            
            except Exception as e:
                # 跳过错误帧
                continue
        
        cap.release()
        
        # 计算统计数据
        metrics = self._calculate_statistics(metrics)
        
        return metrics
    
    def _calculate_key_angles(self, landmark):
        """计算关键角度"""
        
        angles = {
            'elbow_right': None,
            'elbow_left': None,
            'knee_right': None,
            'knee_left': None,
            'shoulder_right': None,
            'shoulder_left': None,
            'hip_right': None,
            'hip_left': None
        }
        
        # 右侧肘部（肩 - 肘 - 腕）
        if self._is_visible(landmark, [12, 14, 16]):
            angles['elbow_right'] = self._calculate_angle(
                landmark[12], landmark[14], landmark[16]
            )
        
        # 左侧肘部
        if self._is_visible(landmark, [11, 13, 15]):
            angles['elbow_left'] = self._calculate_angle(
                landmark[11], landmark[13], landmark[15]
            )
        
        # 右侧膝盖（髋 - 膝 - 踝）
        if self._is_visible(landmark, [24, 26, 28]):
            angles['knee_right'] = self._calculate_angle(
                landmark[24], landmark[26], landmark[28]
            )
        
        # 左侧膝盖
        if self._is_visible(landmark, [23, 25, 27]):
            angles['knee_left'] = self._calculate_angle(
                landmark[23], landmark[25], landmark[27]
            )
        
        # 右侧肩部
        if self._is_visible(landmark, [12, 11, 23]):
            angles['shoulder_right'] = self._calculate_angle(
                landmark[12], landmark[11], landmark[23]
            )
        
        # 右侧髋部
        if self._is_visible(landmark, [24, 23, 11]):
            angles['hip_right'] = self._calculate_angle(
                landmark[24], landmark[23], landmark[11]
            )
        
        return angles
    
    def _calculate_angle(self, p1, p2, p3):
        """计算三点角度"""
        a = np.array([p1.x, p1.y])
        b = np.array([p2.x, p2.y])
        c = np.array([p3.x, p3.y])
        
        ba = a - b
        bc = c - b
        
        norm = np.linalg.norm(ba) * np.linalg.norm(bc)
        if norm < 1e-8:
            return 0.0
        
        cosine = np.dot(ba, bc) / norm
        angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
        
        return float(angle)
    
    def _is_visible(self, landmark, indices, threshold=0.5):
        """检查骨骼点是否可见"""
        return all(landmark[i].visibility > threshold for i in indices)
    
    def _calculate_statistics(self, metrics):
        """计算统计数据"""
        
        # 检测率
        if metrics['frame_count'] > 0:
            metrics['detection_rate'] = metrics['detected_frames'] / metrics['frame_count']
        else:
            metrics['detection_rate'] = 0
        
        # 角度统计
        for angle_key in ['elbow_angles', 'knee_angles', 'shoulder_angles', 'hip_angles']:
            angles = metrics[angle_key]
            if angles:
                metrics[f'{angle_key}_max'] = max(angles)
                metrics[f'{angle_key}_min'] = min(angles)
                metrics[f'{angle_key}_avg'] = sum(angles) / len(angles)
            else:
                metrics[f'{angle_key}_max'] = None
                metrics[f'{angle_key}_min'] = None
                metrics[f'{angle_key}_avg'] = None
        
        return metrics
    
    def format_for_ai(self, metrics):
        """
        格式化为 AI 分析可用的文本
        
        Args:
            metrics: analyze_video() 返回的指标
        
        Returns:
            str: 格式化的文本描述
        """
        
        if 'error' in metrics:
            return f"MediaPipe 分析失败：{metrics['error']}"
        
        lines = []
        lines.append("📏 MediaPipe 姿态量化分析：")
        lines.append("")
        
        # 视频信息
        video_info = metrics.get('video_info', {})
        lines.append(f"  视频时长：{video_info.get('duration_sec', 0):.1f}秒")
        lines.append(f"  帧率：{video_info.get('fps', 0):.1f} FPS")
        lines.append(f"  姿态检测率：{metrics.get('detection_rate', 0)*100:.1f}%")
        lines.append("")
        
        # 膝盖角度（蓄力关键指标）
        knee_avg = metrics.get('knee_angles_avg')
        knee_max = metrics.get('knee_angles_max')
        knee_min = metrics.get('knee_angles_min')
        
        if knee_avg is not None:
            lines.append(f"  膝盖角度分析:")
            lines.append(f"    平均：{knee_avg:.1f}°")
            lines.append(f"    范围：{knee_min:.1f}° - {knee_max:.1f}°")
            
            # NTRP 等级评估
            if knee_avg < 100:
                level = "4.5+ (专业级深蹲)"
            elif knee_avg < 120:
                level = "4.0 (中级深蹲)"
            elif knee_avg < 140:
                level = "3.5 (进阶)"
            else:
                level = "3.0 (基础级，蓄力不足)"
            
            lines.append(f"    评估：{level}")
            lines.append("")
        
        # 肘部角度（奖杯姿势关键指标）
        elbow_avg = metrics.get('elbow_angles_avg')
        elbow_max = metrics.get('elbow_angles_max')
        
        if elbow_avg is not None:
            lines.append(f"  肘部角度分析:")
            lines.append(f"    平均：{elbow_avg:.1f}°")
            lines.append(f"    最大：{elbow_max:.1f}°")
            
            # 奖杯姿势评估
            if elbow_max > 170:
                trophy = "✅ 奖杯姿势标准（肘部高于肩膀）"
            elif elbow_max > 150:
                trophy = "⚠️ 奖杯姿势基本合格"
            else:
                trophy = "❌ 奖杯姿势不完整（肘部未高于肩膀）"
            
            lines.append(f"    评估：{trophy}")
            lines.append("")
        
        # 肩部角度（转体关键指标）
        shoulder_avg = metrics.get('shoulder_angles_avg')
        
        if shoulder_avg is not None:
            lines.append(f"  肩部旋转角度：{shoulder_avg:.1f}°")
            
            if shoulder_avg > 90:
                rotation = "✅ 转体充分"
            elif shoulder_avg > 70:
                rotation = "⚠️ 转体基本合格"
            else:
                rotation = "❌ 转体不足"
            
            lines.append(f"    评估：{rotation}")
            lines.append("")
        
        return '\n'.join(lines)


# 测试
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎯 MediaPipe 姿态分析器测试")
    print("="*60 + "\n")
    
    analyzer = MediaPipeAnalyzer()
    
    test_video = '/home/admin/.openclaw/workspace/media/inbound/video-1775691707124.mp4'
    
    if os.path.exists(test_video):
        print(f"分析视频：{os.path.basename(test_video)}\n")
        metrics = analyzer.analyze_video(test_video)
        
        print(analyzer.format_for_ai(metrics))
    else:
        print(f"测试视频不存在：{test_video}")
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60 + "\n")
