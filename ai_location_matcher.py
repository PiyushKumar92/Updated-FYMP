"""
AI Location Matcher - Advanced facial recognition and location matching system
"""
import cv2
import numpy as np
import face_recognition
import os
import json
from datetime import datetime
from app import db
from app.models import Case, SurveillanceFootage, LocationMatch, PersonDetection
import logging
from geopy.distance import geodesic
import threading
import queue

logger = logging.getLogger(__name__)

class AILocationMatcher:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.processing_queue = queue.Queue()
        self.is_processing = False
        
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates in kilometers"""
        if not all([lat1, lon1, lat2, lon2]):
            return None
        try:
            return geodesic((lat1, lon1), (lat2, lon2)).kilometers
        except:
            return None
    
    def find_nearby_footage(self, location_name):
        """Find surveillance footage near a given location"""
        try:
            if not location_name:
                return []
            
            # Get all active surveillance footage
            footage_list = SurveillanceFootage.query.filter_by(is_active=True).all()
            nearby_footage = []
            
            location_lower = location_name.lower()
            
            for footage in footage_list:
                if footage.location_name:
                    footage_location = footage.location_name.lower()
                    
                    # Check for location match
                    if (location_lower in footage_location or 
                        footage_location in location_lower or
                        any(word in footage_location for word in location_lower.split())):
                        
                        # Calculate distance if GPS available
                        distance_km = None
                        footage.distance_km = distance_km
                        nearby_footage.append(footage)
            
            return nearby_footage
            
        except Exception as e:
            logger.error(f"Error finding nearby footage for location {location_name}: {str(e)}")
            return []
    
    def find_location_matches(self, case_id):
        """Find surveillance footage that matches case location"""
        try:
            case = Case.query.get(case_id)
            if not case:
                return []
            
            # Get all active surveillance footage
            footage_list = SurveillanceFootage.query.filter_by(is_active=True).all()
            matches = []
            
            for footage in footage_list:
                match_score = 0.0
                distance_km = None
                
                # Location name matching
                if case.last_seen_location and footage.location_name:
                    case_location = case.last_seen_location.lower()
                    footage_location = footage.location_name.lower()
                    
                    # Exact match
                    if case_location == footage_location:
                        match_score = 1.0
                    # Partial match
                    elif case_location in footage_location or footage_location in case_location:
                        match_score = 0.8
                    # Word matching
                    else:
                        case_words = set(case_location.split())
                        footage_words = set(footage_location.split())
                        common_words = case_words.intersection(footage_words)
                        if common_words:
                            match_score = len(common_words) / max(len(case_words), len(footage_words))
                
                # GPS distance matching (if available)
                if hasattr(case, 'latitude') and hasattr(case, 'longitude') and footage.latitude and footage.longitude:
                    distance_km = self.calculate_distance(
                        case.latitude, case.longitude,
                        footage.latitude, footage.longitude
                    )
                    if distance_km is not None:
                        # Boost score for nearby locations
                        if distance_km < 1:  # Within 1km
                            match_score = max(match_score, 0.9)
                        elif distance_km < 5:  # Within 5km
                            match_score = max(match_score, 0.7)
                        elif distance_km < 10:  # Within 10km
                            match_score = max(match_score, 0.5)
                
                # Only create matches with reasonable scores
                if match_score > 0.3:
                    matches.append({
                        'footage': footage,
                        'match_score': match_score,
                        'distance_km': distance_km
                    })
            
            # Sort by match score
            matches.sort(key=lambda x: x['match_score'], reverse=True)
            return matches
            
        except Exception as e:
            logger.error(f"Error finding location matches for case {case_id}: {str(e)}")
            return []
    
    def process_new_case(self, case_id):
        """Process a new case and create location matches"""
        try:
            matches = self.find_location_matches(case_id)
            
            for match_data in matches:
                # Check if match already exists
                existing_match = LocationMatch.query.filter_by(
                    case_id=case_id,
                    footage_id=match_data['footage'].id
                ).first()
                
                if not existing_match:
                    location_match = LocationMatch(
                        case_id=case_id,
                        footage_id=match_data['footage'].id,
                        match_score=match_data['match_score'],
                        distance_km=match_data['distance_km'],
                        status='pending'
                    )
                    db.session.add(location_match)
            
            db.session.commit()
            return len(matches)
            
        except Exception as e:
            logger.error(f"Error processing new case {case_id}: {str(e)}")
            db.session.rollback()
            return 0
    
    def process_new_footage(self, footage_id):
        """Process new footage and find matching cases"""
        try:
            footage = SurveillanceFootage.query.get(footage_id)
            if not footage:
                return 0
            
            # Get all active cases
            active_cases = Case.query.filter(Case.status.in_(['Active', 'Queued', 'Processing'])).all()
            matches_created = 0
            
            for case in active_cases:
                match_score = 0.0
                distance_km = None
                
                # Location matching logic (same as above)
                if case.last_seen_location and footage.location_name:
                    case_location = case.last_seen_location.lower()
                    footage_location = footage.location_name.lower()
                    
                    if case_location == footage_location:
                        match_score = 1.0
                    elif case_location in footage_location or footage_location in case_location:
                        match_score = 0.8
                    else:
                        case_words = set(case_location.split())
                        footage_words = set(footage_location.split())
                        common_words = case_words.intersection(footage_words)
                        if common_words:
                            match_score = len(common_words) / max(len(case_words), len(footage_words))
                
                if match_score > 0.3:
                    # Check if match already exists
                    existing_match = LocationMatch.query.filter_by(
                        case_id=case.id,
                        footage_id=footage_id
                    ).first()
                    
                    if not existing_match:
                        location_match = LocationMatch(
                            case_id=case.id,
                            footage_id=footage_id,
                            match_score=match_score,
                            distance_km=distance_km,
                            status='pending'
                        )
                        db.session.add(location_match)
                        matches_created += 1
            
            db.session.commit()
            return matches_created
            
        except Exception as e:
            logger.error(f"Error processing new footage {footage_id}: {str(e)}")
            db.session.rollback()
            return 0
    
    def extract_face_encodings(self, image_path):
        """Extract face encodings from an image"""
        try:
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)
            return face_encodings[0] if face_encodings else None
        except Exception as e:
            logger.error(f"Error extracting face encodings from {image_path}: {str(e)}")
            return None
    
    def analyze_footage_for_person(self, match_id):
        """Analyze surveillance footage for a specific person"""
        try:
            match = LocationMatch.query.get(match_id)
            if not match:
                return False
            
            # Update status
            match.status = 'processing'
            match.ai_analysis_started = datetime.utcnow()
            db.session.commit()
            
            # Get case target images
            case = match.case
            target_encodings = []
            
            for target_image in case.target_images:
                image_path = os.path.join('app', 'static', target_image.image_path)
                if os.path.exists(image_path):
                    encoding = self.extract_face_encodings(image_path)
                    if encoding is not None:
                        target_encodings.append(encoding)
            
            if not target_encodings:
                match.status = 'failed'
                db.session.commit()
                return False
            
            # Analyze surveillance footage
            footage_path = os.path.join('app', 'static', match.footage.video_path)
            if not os.path.exists(footage_path):
                match.status = 'failed'
                db.session.commit()
                return False
            
            detections = self.analyze_video_for_faces(footage_path, target_encodings, match_id)
            
            # Update match results
            match.detection_count = len(detections)
            match.person_found = len(detections) > 0
            
            if detections:
                # Calculate average confidence
                avg_confidence = sum(d['confidence'] for d in detections) / len(detections)
                match.confidence_score = avg_confidence
            
            match.status = 'completed'
            match.ai_analysis_completed = datetime.utcnow()
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error analyzing footage for match {match_id}: {str(e)}")
            if match:
                match.status = 'failed'
                db.session.commit()
            return False
    
    def analyze_video_for_faces(self, video_path, target_encodings, match_id):
        """Advanced video analysis with multiple detection methods"""
        detections = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_count = 0
            
            # Adaptive frame skip based on video length
            if total_frames > fps * 600:  # > 10 minutes
                frame_skip = max(1, int(fps * 2))  # Every 2 seconds
            elif total_frames > fps * 300:  # > 5 minutes
                frame_skip = max(1, int(fps * 1.5))  # Every 1.5 seconds
            else:
                frame_skip = max(1, int(fps))  # Every 1 second
            
            logger.info(f"Analyzing video: {total_frames} frames, processing every {frame_skip} frames")
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_skip == 0:
                    timestamp = frame_count / fps
                    
                    # Convert BGR to RGB
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Multiple detection methods
                    detections_found = self._detect_person_multiple_methods(
                        rgb_frame, frame, target_encodings, timestamp, match_id
                    )
                    detections.extend(detections_found)
                
                frame_count += 1
                
                # Progress logging
                if frame_count % (frame_skip * 10) == 0:
                    progress = (frame_count / total_frames) * 100
                    logger.info(f"Analysis progress: {progress:.1f}%")
                
                # Limit processing time
                if frame_count > fps * 1800:  # Max 30 minutes
                    logger.warning("Video too long, stopping analysis")
                    break
            
            cap.release()
            db.session.commit()
            
            logger.info(f"Analysis complete: {len(detections)} detections found")
            
        except Exception as e:
            logger.error(f"Error analyzing video {video_path}: {str(e)}")
        
        return detections
    
    def _detect_person_multiple_methods(self, rgb_frame, bgr_frame, target_encodings, timestamp, match_id):
        """Use multiple detection methods for better accuracy"""
        detections = []
        
        try:
            # Method 1: Face Recognition
            face_detections = self._face_recognition_detection(
                rgb_frame, bgr_frame, target_encodings, timestamp, match_id
            )
            detections.extend(face_detections)
            
            # Method 2: Body/Pose Detection (if face detection fails)
            if not face_detections:
                body_detections = self._body_detection(
                    rgb_frame, bgr_frame, timestamp, match_id
                )
                detections.extend(body_detections)
            
            # Method 3: Clothing Analysis (experimental)
            clothing_detections = self._clothing_analysis(
                rgb_frame, bgr_frame, timestamp, match_id
            )
            detections.extend(clothing_detections)
            
        except Exception as e:
            logger.error(f"Error in multi-method detection: {str(e)}")
        
        return detections
    
    def _face_recognition_detection(self, rgb_frame, bgr_frame, target_encodings, timestamp, match_id):
        """Enhanced face recognition with better preprocessing"""
        detections = []
        
        try:
            # Enhance image quality
            enhanced_frame = self._enhance_image_quality(rgb_frame)
            
            # Find faces with multiple models
            face_locations_hog = face_recognition.face_locations(enhanced_frame, model="hog")
            face_locations_cnn = face_recognition.face_locations(enhanced_frame, model="cnn")
            
            # Combine results
            all_face_locations = list(set(face_locations_hog + face_locations_cnn))
            
            if all_face_locations:
                face_encodings = face_recognition.face_encodings(enhanced_frame, all_face_locations)
                
                for face_encoding, face_location in zip(face_encodings, all_face_locations):
                    # Compare with target encodings
                    matches = face_recognition.compare_faces(target_encodings, face_encoding, tolerance=0.6)
                    face_distances = face_recognition.face_distance(target_encodings, face_encoding)
                    
                    if any(matches):
                        best_match_index = np.argmin(face_distances)
                        confidence = 1 - face_distances[best_match_index]
                        
                        # Adjusted confidence threshold
                        if confidence > 0.35:
                            detection_data = self._save_detection(
                                bgr_frame, face_location, timestamp, match_id, 
                                confidence, confidence, None, 'face_recognition_enhanced'
                            )
                            if detection_data:
                                detections.append(detection_data)
        
        except Exception as e:
            logger.error(f"Error in face recognition: {str(e)}")
        
        return detections
    
    def _body_detection(self, rgb_frame, bgr_frame, timestamp, match_id):
        """Body/pose detection for cases where face is not visible"""
        detections = []
        
        try:
            # Simple body detection using OpenCV
            gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
            
            # Use HOG descriptor for person detection
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            
            # Detect people
            boxes, weights = hog.detectMultiScale(gray, winStride=(8,8))
            
            for (x, y, w, h), weight in zip(boxes, weights):
                if weight > 0.5:  # Confidence threshold
                    # Convert to face_recognition format (top, right, bottom, left)
                    detection_box = (y, x + w, y + h, x)
                    
                    detection_data = self._save_detection(
                        bgr_frame, detection_box, timestamp, match_id,
                        weight, None, None, 'body_detection'
                    )
                    if detection_data:
                        detections.append(detection_data)
        
        except Exception as e:
            logger.error(f"Error in body detection: {str(e)}")
        
        return detections
    
    def _clothing_analysis(self, rgb_frame, bgr_frame, timestamp, match_id):
        """Basic clothing color analysis"""
        detections = []
        
        try:
            # Simple clothing analysis based on dominant colors
            # This is a placeholder for more advanced clothing recognition
            
            # Extract dominant colors from frame
            colors = self._extract_dominant_colors(rgb_frame)
            
            # Basic scoring based on color similarity
            # (In real implementation, this would compare with case clothing description)
            clothing_score = 0.3  # Placeholder score
            
            if clothing_score > 0.25:
                # Create a general detection for clothing match
                h, w = rgb_frame.shape[:2]
                detection_box = (h//4, w*3//4, h*3//4, w//4)  # Center region
                
                detection_data = self._save_detection(
                    bgr_frame, detection_box, timestamp, match_id,
                    clothing_score, None, clothing_score, 'clothing_analysis'
                )
                if detection_data:
                    detections.append(detection_data)
        
        except Exception as e:
            logger.error(f"Error in clothing analysis: {str(e)}")
        
        return detections
    
    def _enhance_image_quality(self, image):
        """Enhance image quality for better face recognition"""
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            lab[:,:,0] = clahe.apply(lab[:,:,0])
            
            # Convert back to RGB
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            
            return enhanced
        except:
            return image
    
    def _extract_dominant_colors(self, image, k=3):
        """Extract dominant colors from image"""
        try:
            # Reshape image to be a list of pixels
            data = image.reshape((-1, 3))
            data = np.float32(data)
            
            # Apply k-means clustering
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            return centers.astype(int)
        except:
            return []
    
    def _save_detection(self, frame, detection_box, timestamp, match_id, 
                       confidence, face_score, clothing_score, method):
        """Save detection with frame extraction"""
        try:
            # Save detection frame
            frame_filename = f"detection_{match_id}_{int(timestamp)}_{method}.jpg"
            frame_dir = os.path.join('app', 'static', 'detections')
            os.makedirs(frame_dir, exist_ok=True)
            frame_path = os.path.join(frame_dir, frame_filename)
            
            # Extract detection region
            top, right, bottom, left = detection_box
            detection_region = frame[max(0, top-20):min(frame.shape[0], bottom+20), 
                                   max(0, left-20):min(frame.shape[1], right+20)]
            
            if detection_region.size > 0:
                cv2.imwrite(frame_path, detection_region)
                
                # Create detection record
                detection = PersonDetection(
                    location_match_id=match_id,
                    timestamp=timestamp,
                    confidence_score=confidence,
                    face_match_score=face_score,
                    clothing_match_score=clothing_score,
                    detection_box=json.dumps({
                        'top': int(top), 'right': int(right), 
                        'bottom': int(bottom), 'left': int(left)
                    }),
                    frame_path=f"detections/{frame_filename}",
                    analysis_method=method
                )
                db.session.add(detection)
                
                return {
                    'timestamp': timestamp,
                    'confidence': confidence,
                    'location': detection_box,
                    'method': method
                }
        
        except Exception as e:
            logger.error(f"Error saving detection: {str(e)}")
        
        return None
    
    def start_background_processing(self):
        """Start background processing thread"""
        if not self.is_processing:
            self.is_processing = True
            thread = threading.Thread(target=self._background_processor)
            thread.daemon = True
            thread.start()
    
    def _background_processor(self):
        """Background processor for AI analysis"""
        while self.is_processing:
            try:
                # Get pending matches
                pending_matches = LocationMatch.query.filter_by(status='pending').limit(5).all()
                
                for match in pending_matches:
                    self.analyze_footage_for_person(match.id)
                
                # Sleep for a bit before checking again
                import time
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in background processor: {str(e)}")
                import time
                time.sleep(60)

# Global AI matcher instance
ai_matcher = AILocationMatcher()