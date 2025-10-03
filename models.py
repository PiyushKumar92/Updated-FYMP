from datetime import datetime, timedelta
import pytz
from flask_login import UserMixin
from flask_bcrypt import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from app import db
from app.utils import sanitize_input

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    """Get current time in IST"""
    return datetime.now(IST)

def utc_to_ist(utc_dt):
    """Convert UTC datetime to IST for display"""
    if utc_dt is None:
        return None
    if utc_dt.tzinfo is None:
        # Assume UTC if no timezone info
        utc_dt = pytz.UTC.localize(utc_dt)
    return utc_dt.astimezone(IST)


class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    details = db.Column(db.Text)
    clothing_description = db.Column(db.Text)
    last_seen_location = db.Column(db.String(200))
    last_seen_time = db.Column(db.Time)  # Optional time field
    contact_address = db.Column(db.Text)  # Contact person address
    date_missing = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(
        db.String(20), default="Pending Approval"
    )  # Pending Approval, Approved, Queued, Processing, Active, Resolved, Withdrawn
    priority = db.Column(db.String(10), default="Medium")  # Low, Medium, High, Critical
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed_at = db.Column(db.DateTime)

    # Relationships
    target_images = db.relationship(
        "TargetImage", backref="case", lazy=True, cascade="all, delete-orphan"
    )
    search_videos = db.relationship(
        "SearchVideo", backref="case", lazy=True, cascade="all, delete-orphan"
    )
    sightings = db.relationship(
        "Sighting", backref="case", lazy=True, cascade="all, delete-orphan"
    )
    case_notes = db.relationship(
        "CaseNote", backref="case", lazy=True, cascade="all, delete-orphan"
    )
    location_matches = db.relationship(
        "LocationMatch", back_populates="case", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        safe_name = sanitize_input(self.person_name) if self.person_name else 'Unknown'
        return f"<Case {safe_name} - {self.status}>"

    @property
    def total_sightings(self):
        return len(self.sightings)

    @property
    def high_confidence_sightings(self):
        return len([s for s in self.sightings if s.confidence_score > 0.8])


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Enhanced user fields
    last_login = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    location = db.Column(db.String(200))
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships with cascade delete
    cases = db.relationship(
        "Case", foreign_keys="Case.user_id", backref="creator", lazy=True, cascade="all, delete-orphan"
    )
    assigned_cases = db.relationship(
        "Case", foreign_keys="Case.assigned_to", backref="assignee", lazy=True
    )
    
    @property
    def unread_notifications_count(self):
        """Get count of unread notifications for this user"""
        return Notification.query.filter_by(user_id=self.id, is_read=False).count()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return s.dumps({"user_id": self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token, max_age=expires_sec)["user_id"]
        except:
            return None
        return User.query.get(user_id)


class TargetImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("case.id"), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    image_type = db.Column(
        db.String(20), default="front"
    )  # front, side, back, full_body
    description = db.Column(db.String(200))
    is_primary = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TargetImage {self.image_type} for Case {self.case_id}>"


class SearchVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("case.id"), nullable=False)
    video_path = db.Column(db.String(200), nullable=False)
    video_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    duration = db.Column(db.Float)  # in seconds
    fps = db.Column(db.Float)
    resolution = db.Column(db.String(20))
    file_size = db.Column(db.BigInteger)  # in bytes
    status = db.Column(
        db.String(20), default="Pending"
    )  # Pending, Processing, Completed, Failed
    processed_at = db.Column(db.DateTime)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sightings = db.relationship("Sighting", backref="search_video", lazy=True)

    def __repr__(self):
        safe_name = sanitize_input(self.video_name) if self.video_name else 'Unknown'
        return f"<SearchVideo {safe_name} for Case {self.case_id}>"


class Sighting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("case.id"), nullable=False)
    search_video_id = db.Column(
        db.Integer, db.ForeignKey("search_video.id"), nullable=False
    )
    video_name = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.Float, nullable=False)  # timestamp in video (seconds)
    confidence_score = db.Column(db.Float, nullable=False)  # combined confidence
    face_score = db.Column(db.Float)
    clothing_score = db.Column(db.Float)
    detection_method = db.Column(
        db.String(20), nullable=False
    )  # face, clothing, multi_modal
    thumbnail_path = db.Column(db.String(200))
    bounding_box = db.Column(db.Text)  # JSON string of coordinates
    verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Sighting Case {self.case_id} at {self.timestamp}s - {self.confidence_score:.2f}>"

    @property
    def formatted_timestamp(self):
        minutes = int(self.timestamp // 60)
        seconds = int(self.timestamp % 60)
        return f"{minutes:02d}:{seconds:02d}"


class CaseNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("case.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    note_type = db.Column(
        db.String(20), default="General"
    )  # General, Update, Evidence, Contact
    content = db.Column(db.Text, nullable=False)
    is_important = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    author = db.relationship("User", backref="case_notes")

    def __repr__(self):
        safe_type = sanitize_input(self.note_type) if self.note_type else 'Unknown'
        return f"<CaseNote {safe_type} for Case {self.case_id}>"


class SystemLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("case.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    action = db.Column(
        db.String(50), nullable=False
    )  # case_created, video_uploaded, sighting_found, etc.
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        safe_action = sanitize_input(self.action) if self.action else 'Unknown'
        return f"<SystemLog {safe_action} at {self.timestamp}>"


class AdminMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default="info")  # info, warning, success, danger
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=get_ist_now)
    expires_at = db.Column(db.DateTime)
    
    author = db.relationship("User", backref="announcements")
    read_by = db.relationship("AnnouncementRead", backref="announcement", lazy=True, cascade="all, delete-orphan")
    
    @property
    def ist_created_at(self):
        """Get created_at in IST timezone for display"""
        if self.created_at.tzinfo is None:
            # If stored as naive datetime, assume it's already IST
            return self.created_at
        return utc_to_ist(self.created_at)


class AnnouncementRead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    announcement_id = db.Column(db.Integer, db.ForeignKey("announcement.id"), nullable=False)
    read_at = db.Column(db.DateTime, default=get_ist_now)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'announcement_id', name='unique_user_announcement'),)
    
    @property
    def ist_read_at(self):
        """Get read_at in IST timezone for display"""
        if self.read_at.tzinfo is None:
            # If stored as naive datetime, assume it's already IST
            return self.read_at
        return utc_to_ist(self.read_at)


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    is_published = db.Column(db.Boolean, default=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    author = db.relationship("User", backref="blog_posts")


class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="General")
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    author = db.relationship("User", backref="faqs")


class AISettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_name = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    updater = db.relationship("User", backref="ai_settings_updates")


class ContactMessage(db.Model):
    """Contact form messages from users"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        safe_name = sanitize_input(self.name) if self.name else 'Unknown'
        return f"<ContactMessage from {safe_name}>"


class ChatRoom(db.Model):
    """Chat room between user and admin"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship("User", foreign_keys=[user_id], backref="user_chat_rooms")
    admin = db.relationship("User", foreign_keys=[admin_id], backref="admin_chat_rooms")
    messages = db.relationship("ChatMessage", backref="chat_room", lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatRoom {self.id} - User {self.user_id} & Admin {self.admin_id}>"
    
    @property
    def unread_count_for_user(self):
        return ChatMessage.query.filter_by(chat_room_id=self.id, is_read=False).filter(ChatMessage.sender_id != self.user_id).count()
    
    @property
    def unread_count_for_admin(self):
        return ChatMessage.query.filter_by(chat_room_id=self.id, is_read=False).filter(ChatMessage.sender_id != self.admin_id).count()


class ChatMessage(db.Model):
    """Individual chat messages"""
    id = db.Column(db.Integer, primary_key=True)
    chat_room_id = db.Column(db.Integer, db.ForeignKey("chat_room.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message_type = db.Column(db.String(20), default="text")  # text, image, video, file
    content = db.Column(db.Text)  # Text content or file path
    file_path = db.Column(db.String(500))  # For media files
    file_name = db.Column(db.String(200))  # Original filename
    is_read = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default="sent")  # sent, delivered, seen
    delivered_at = db.Column(db.DateTime)
    seen_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    hidden_for_user = db.Column(db.Boolean, default=False)  # Hidden for regular user
    hidden_for_admin = db.Column(db.Boolean, default=False)  # Hidden for admin
    
    # Relationships
    sender = db.relationship("User", backref="sent_chat_messages")
    
    def __repr__(self):
        return f"<ChatMessage {self.id} from User {self.sender_id}>"
    
    def mark_delivered(self):
        """Mark message as delivered"""
        if self.status == 'sent':
            self.status = 'delivered'
            self.delivered_at = get_ist_now()
            db.session.commit()
    
    def mark_seen(self):
        """Mark message as seen"""
        if self.status in ['sent', 'delivered']:
            self.status = 'seen'
            self.seen_at = get_ist_now()
            self.is_read = True
            db.session.commit()


class Notification(db.Model):
    """User notification system for admin messages and system alerts"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"))  # Null for system messages
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default="info")  # info, warning, success, danger, chat
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_ist_now)
    related_url = db.Column(db.String(200))  # For chat notifications
    
    # Relationships
    recipient = db.relationship("User", foreign_keys=[user_id])
    sender = db.relationship("User", foreign_keys=[sender_id])
    
    def __repr__(self):
        safe_title = sanitize_input(self.title) if self.title else 'Unknown'
        return f"<Notification {safe_title} for User {self.user_id}>"
    
    @property
    def ist_created_at(self):
        """Get created_at in IST timezone for display"""
        if self.created_at.tzinfo is None:
            # If stored as naive datetime, assume it's already IST
            return self.created_at
        return utc_to_ist(self.created_at)


class SurveillanceFootage(db.Model):
    """Admin uploaded surveillance footage for location-based searches"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    location_name = db.Column(db.String(200), nullable=False)
    location_address = db.Column(db.String(500))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    video_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    file_size = db.Column(db.BigInteger)  # in bytes
    duration = db.Column(db.Float)  # in seconds
    fps = db.Column(db.Float)
    resolution = db.Column(db.String(20))
    quality = db.Column(db.String(20), default="HD")  # SD, HD, FHD, 4K
    date_recorded = db.Column(db.DateTime)
    camera_type = db.Column(db.String(50))  # CCTV, Security, Traffic, etc.
    is_active = db.Column(db.Boolean, default=True)
    is_processed = db.Column(db.Boolean, default=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    uploader = db.relationship("User", backref="surveillance_footage")
    matches = db.relationship("LocationMatch", backref="footage", lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        safe_title = sanitize_input(self.title) if self.title else 'Unknown'
        return f"<SurveillanceFootage {safe_title} at {self.location_name}>"
    
    @property
    def formatted_duration(self):
        if not self.duration:
            return "Unknown"
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def formatted_file_size(self):
        if not self.file_size:
            return "Unknown"
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"


class LocationMatch(db.Model):
    """AI-powered location matches between cases and surveillance footage"""
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("case.id"), nullable=False)
    footage_id = db.Column(db.Integer, db.ForeignKey("surveillance_footage.id"), nullable=False)
    match_score = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    distance_km = db.Column(db.Float)  # Distance between locations in km
    match_type = db.Column(db.String(20), default="location")  # location, proximity, exact
    status = db.Column(db.String(20), default="pending")  # pending, processing, completed, failed
    ai_analysis_started = db.Column(db.DateTime)
    ai_analysis_completed = db.Column(db.DateTime)
    person_found = db.Column(db.Boolean, default=False)
    confidence_score = db.Column(db.Float)  # AI confidence if person found
    detection_count = db.Column(db.Integer, default=0)  # Number of detections
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    case = db.relationship("Case", back_populates="location_matches")
    detections = db.relationship("PersonDetection", backref="location_match", lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<LocationMatch Case {self.case_id} - Footage {self.footage_id} ({self.match_score:.2f})>"


class PersonDetection(db.Model):
    """AI detection results from surveillance footage analysis"""
    id = db.Column(db.Integer, primary_key=True)
    location_match_id = db.Column(db.Integer, db.ForeignKey("location_match.id"), nullable=False)
    timestamp = db.Column(db.Float, nullable=False)  # Video timestamp in seconds
    confidence_score = db.Column(db.Float, nullable=False)  # AI confidence 0.0-1.0
    face_match_score = db.Column(db.Float)  # Face recognition score
    clothing_match_score = db.Column(db.Float)  # Clothing analysis score
    body_pose_score = db.Column(db.Float)  # Body pose similarity
    detection_box = db.Column(db.Text)  # JSON bounding box coordinates
    frame_path = db.Column(db.String(500))  # Extracted frame image path
    analysis_method = db.Column(db.String(50))  # face_recognition, clothing_analysis, multi_modal
    verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    verifier = db.relationship("User", backref="verified_detections")
    
    def __repr__(self):
        return f"<PersonDetection Match {self.location_match_id} at {self.timestamp}s ({self.confidence_score:.2f})>"
    
    @property
    def formatted_timestamp(self):
        minutes = int(self.timestamp // 60)
        seconds = int(self.timestamp % 60)
        return f"{minutes:02d}:{seconds:02d}"
