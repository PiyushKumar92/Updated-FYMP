import os
from datetime import datetime, timedelta
import pytz
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    abort,
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from functools import wraps

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    """Get current time in IST"""
    return datetime.now(IST)

def utc_to_ist(utc_dt):
    """Convert UTC datetime to IST"""
    if utc_dt.tzinfo is None:
        utc_dt = pytz.utc.localize(utc_dt)
    return utc_dt.astimezone(IST)

from app import db
from app.models import User, Case, TargetImage, SearchVideo, Sighting, Announcement, AnnouncementRead
from app.forms import (
    RegistrationForm,
    LoginForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    NewCaseForm,
    ContactForm,
)


# File validation helper functions
def _is_allowed_image_file(filename):
    """Check if uploaded file is an allowed image type"""
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
    )


def _is_allowed_video_file(filename):
    """Check if uploaded file is an allowed video type"""
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "wmv", "flv", "webm"}
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS
    )


# Authorization helper functions
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def case_owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        case_id = kwargs.get("case_id")
        if case_id:
            case = Case.query.get_or_404(case_id)
            if case.user_id != current_user.id and not current_user.is_admin:
                abort(403)
        return f(*args, **kwargs)

    return decorated_function


# The 'process_case' import is moved inside the function to prevent a circular import.

# This 'bp' variable is what the error is looking for.
bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    """Public landing page for all visitors"""
    return render_template("index.html")


@bp.route("/.well-known/appspecific/com.chrome.devtools.json")
def chrome_devtools():
    """Handle Chrome DevTools request to prevent 404 errors"""
    return jsonify({}), 200


@bp.route("/dashboard")
@login_required
def dashboard():
    """Secure dashboard for authenticated users"""
    # Check if user is admin and redirect to admin dashboard
    if current_user.is_admin:
        return redirect(url_for("admin.dashboard"))

    # Regular user dashboard
    user_cases = Case.query.filter_by(user_id=current_user.id).all()
    total_cases = len(user_cases)
    active_cases = len([c for c in user_cases if c.status in ["Approved", "Queued", "Processing", "Active"]])
    pending_approval = len([c for c in user_cases if c.status == "Pending Approval"])
    completed_cases = len([c for c in user_cases if c.status == "Completed"])
    total_sightings = sum(len(c.sightings) for c in user_cases)

    # Get recent cases (last 5)
    recent_cases = (
        Case.query.filter_by(user_id=current_user.id)
        .order_by(Case.created_at.desc())
        .limit(5)
        .all()
    )

    user_stats = {
        "total_cases": total_cases,
        "active_cases": active_cases,
        "pending_approval": pending_approval,
        "completed_cases": completed_cases,
        "total_sightings": total_sightings,
    }
    
    # Get recent unread announcements for user dashboard
    try:
        all_active = Announcement.query.filter_by(is_active=True).order_by(Announcement.created_at.desc()).all()
        read_announcement_ids = db.session.query(AnnouncementRead.announcement_id).filter_by(user_id=current_user.id).all()
        read_ids = [r[0] for r in read_announcement_ids]
        recent_announcements = [a for a in all_active if a.id not in read_ids][:3]
    except Exception:
        # If table doesn't exist, show all announcements
        recent_announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.created_at.desc()).limit(3).all()

    return render_template(
        "user_dashboard.html", 
        user_stats=user_stats, 
        recent_cases=recent_cases,
        recent_announcements=recent_announcements
    )


@bp.route("/register_case", methods=["GET", "POST"])
@login_required
def register_case():
    # Prevent admin users from accessing this route
    if current_user.is_admin:
        flash("Admins cannot register new cases. Please use a regular user account.", "warning")
        return redirect(url_for("admin.dashboard"))
    form = NewCaseForm()
    if request.method == 'POST' and form.validate_on_submit():
        # Check for recent duplicate submissions (within last 5 minutes)
        from datetime import datetime, timedelta
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        existing_case = Case.query.filter(
            Case.user_id == current_user.id,
            Case.person_name == form.full_name.data,
            Case.created_at > recent_time
        ).first()
        
        if existing_case:
            flash(f"A case for {form.full_name.data} was already submitted recently. Please check your cases.", "warning")
            return redirect(url_for("main.profile"))
        # Get additional form data
        contact_address = request.form.get('contact_address', '')
        last_seen_time = request.form.get('last_seen_time')
        
        # Parse time if provided
        parsed_time = None
        if last_seen_time:
            try:
                from datetime import time
                hour, minute = map(int, last_seen_time.split(':'))
                parsed_time = time(hour, minute)
            except:
                parsed_time = None
        
        # Create new case with comprehensive data  
        new_case = Case(
            person_name=form.full_name.data,
            age=form.age.data,
            details=f"Nickname: {form.nickname.data or 'N/A'}\n"
            f"Gender: {form.gender.data}\n"
            f"Height: {form.height_cm.data}cm\n"
            f"Distinguishing Marks: {form.distinguishing_marks.data}\n"
            f"Contact Person: {form.contact_person_name.data}\n"
            f"Contact Phone: {form.contact_person_phone.data}\n"
            f"Contact Email: {form.contact_person_email.data}\n"
            f"Contact Address: {contact_address or 'Not provided'}\n"
            f"Additional Info: {form.additional_info.data or 'None'}",
            last_seen_location=form.last_seen_location.data,
            last_seen_time=parsed_time,
            contact_address=contact_address,
            date_missing=form.last_seen_date.data,
            priority="High",  # Default priority for new comprehensive form
            status="Pending Approval",  # Wait for admin approval
            user_id=current_user.id,
        )
        db.session.add(new_case)
        db.session.commit()

        # Handle multiple photo uploads with enhanced security
        photo_files = form.photos.data
        for photo_file in photo_files:
            if photo_file and photo_file.filename != "":
                # Validate file type
                if not _is_allowed_image_file(photo_file.filename):
                    flash(f"Invalid image file type: {photo_file.filename}", "error")
                    continue

                # Create secure unique filename
                try:
                    from app.utils import sanitize_filename, create_safe_filename
                    original_filename = sanitize_filename(photo_file.filename)
                except ImportError:
                    # Fallback if utils module doesn't exist
                    original_filename = secure_filename(photo_file.filename)
                
                if not original_filename:
                    flash("Invalid filename", "error")
                    continue

                # Generate unique filename to prevent conflicts
                file_ext = (
                    original_filename.rsplit(".", 1)[1].lower()
                    if "." in original_filename
                    else "jpg"
                )
                
                try:
                    unique_filename = create_safe_filename(f"case_{new_case.id}_photo", file_ext)
                except (ImportError, NameError):
                    # Fallback filename generation
                    import uuid
                    unique_filename = f"case_{new_case.id}_photo_{uuid.uuid4().hex[:8]}.{file_ext}"

                # Ensure uploads directory exists
                upload_dir = os.path.join("app", "static", "uploads")
                os.makedirs(upload_dir, exist_ok=True)

                save_path = os.path.join(upload_dir, unique_filename)

                # Validate file size (already handled by Flask config, but double-check)
                photo_file.seek(0, 2)  # Seek to end
                file_size = photo_file.tell()
                photo_file.seek(0)  # Reset to beginning

                if file_size > 16 * 1024 * 1024:  # 16MB limit
                    flash(f"File too large: {original_filename}", "error")
                    continue

                photo_file.save(save_path)

                # Validate file content after upload (optional)
                try:
                    from app.utils import validate_file_content
                    if not validate_file_content(save_path, "image"):
                        os.remove(save_path)  # Remove invalid file
                        flash(f"Invalid image file content: {original_filename}", "error")
                        continue
                except ImportError:
                    # Skip validation if utils module doesn't exist
                    pass

                db_path = os.path.join("static", "uploads", unique_filename).replace(
                    "\\", "/"
                )
                target_image = TargetImage(case_id=new_case.id, image_path=db_path)
                db.session.add(target_image)

        # Handle optional video upload with enhanced security
        video_file = form.video.data
        if video_file and video_file.filename != "":
            # Validate file type
            if not _is_allowed_video_file(video_file.filename):
                flash(f"Invalid video file type: {video_file.filename}", "error")
            else:
                # Create secure unique filename
                try:
                    from app.utils import sanitize_filename, create_safe_filename
                    original_filename = sanitize_filename(video_file.filename)
                except ImportError:
                    original_filename = secure_filename(video_file.filename)
                
                if not original_filename:
                    flash("Invalid video filename", "error")
                else:
                    # Generate unique filename to prevent conflicts
                    file_ext = (
                        original_filename.rsplit(".", 1)[1].lower()
                        if "." in original_filename
                        else "mp4"
                    )
                    
                    try:
                        unique_filename = create_safe_filename(f"case_{new_case.id}_video", file_ext)
                    except (ImportError, NameError):
                        import uuid
                        unique_filename = f"case_{new_case.id}_video_{uuid.uuid4().hex[:8]}.{file_ext}"

                    upload_dir = os.path.join("app", "static", "uploads")
                    os.makedirs(upload_dir, exist_ok=True)

                    save_path = os.path.join(upload_dir, unique_filename)

                    # Validate file size
                    video_file.seek(0, 2)
                    file_size = video_file.tell()
                    video_file.seek(0)

                    if file_size > 100 * 1024 * 1024:  # 100MB limit for videos
                        flash(f"Video file too large: {original_filename}", "error")
                    else:
                        video_file.save(save_path)

                        # Validate file content after upload (optional)
                        try:
                            from app.utils import validate_file_content
                            if not validate_file_content(save_path, "video"):
                                os.remove(save_path)  # Remove invalid file
                                flash(f"Invalid video file content: {original_filename}", "error")
                        except ImportError:
                            # Skip validation if utils module doesn't exist
                            pass
                        else:
                            db_path = os.path.join(
                                "static", "uploads", unique_filename
                            ).replace("\\", "/")
                            search_video = SearchVideo(
                                case_id=new_case.id,
                                video_path=db_path,
                                video_name=original_filename,
                            )
                            db.session.add(search_video)

        try:
            db.session.commit()
            
            # Validate that at least one photo was uploaded successfully
            if not new_case.target_images:
                flash("Warning: No valid photos were uploaded. Please add photos for better AI analysis.", "warning")
            
            # Create admin notification for new case
            from app.models import Notification, User
            admins = User.query.filter_by(is_admin=True).all()
            
            for admin in admins:
                notification = Notification(
                    user_id=admin.id,
                    sender_id=current_user.id,
                    title=f"🔍 New Case Pending Approval: {new_case.person_name}",
                    message=f"Location: {new_case.last_seen_location}\nAge: {new_case.age or 'Unknown'}\nRegistered by: {current_user.username}\n\nPlease review and approve this case.",
                    type="approval",
                    related_url=f"/admin/cases/{new_case.id}",
                    created_at=get_ist_now()
                )
                db.session.add(notification)
            
            # Don't start AI processing - wait for admin approval
            success_msg = f"Missing person case for {new_case.person_name} has been submitted successfully! Your case is now pending admin approval. You will be notified once it's reviewed."
            flash(success_msg, "success")
            return redirect(url_for("main.profile"))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error submitting case: {str(e)}. Please try again or contact support.", "error")

    return render_template(
        "register_case.html", title="Register Missing Person Case", form=form
    )


# ... (The rest of the file is the same, including all other routes)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully!")
        return redirect(url_for("main.login"))
    return render_template("register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("main.login"))
        
        # Update login tracking and online status
        ist_now = get_ist_now()
        user.last_login = ist_now
        user.login_count = (user.login_count or 0) + 1
        user.is_online = True
        user.last_seen = ist_now
        db.session.commit()
        
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for("main.index"))
    return render_template("login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    # Update offline status
    current_user.is_online = False
    current_user.last_seen = get_ist_now()
    db.session.commit()
    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash(
                "Password reset link would be sent to your email (email sending not implemented)."
            )
        else:
            flash("Email not found")
        return redirect(url_for("main.login"))
    return render_template("forgot_password.html", form=form)


@bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    user = User.verify_reset_token(token)
    if not user:
        flash("Invalid or expired token")
        return redirect(url_for("main.forgot_password"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Password has been reset successfully")
        return redirect(url_for("main.login"))
    return render_template("reset_password.html", form=form)


@bp.route("/profile")
@login_required
def profile():
    cases = Case.query.filter_by(user_id=current_user.id).order_by(Case.id.desc()).all()
    return render_template("profile.html", cases=cases)


@bp.route("/case/<int:case_id>")
@login_required
@case_owner_required
def case_details(case_id):
    """View detailed information about a specific case with AI analysis results"""
    try:
        case = Case.query.get_or_404(case_id)
        
        # Get AI analysis results
        from app.models import LocationMatch, PersonDetection
        location_matches = LocationMatch.query.filter_by(case_id=case_id).all()
        
        # Get all detections for this case
        all_detections = []
        for match in location_matches:
            detections = PersonDetection.query.filter_by(location_match_id=match.id).all()
            for detection in detections:
                detection.match = match  # Add match info to detection
                all_detections.append(detection)
        
        # Sort detections by confidence score
        all_detections.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return render_template(
            "case_details.html", 
            case=case,
            location_matches=location_matches,
            detections=all_detections
        )
        
    except Exception as e:
        print(f"Error loading case details {case_id}: {str(e)}")
        flash("Error loading case details. Please try again.", "error")
        return redirect(url_for("main.profile"))


@bp.route("/case/<int:case_id>/withdraw", methods=["POST"])
@login_required
@case_owner_required
def withdraw_case(case_id):
    """Completely delete a case and all associated data"""
    case = Case.query.get_or_404(case_id)
    person_name = case.person_name
    
    # Delete associated files from filesystem
    for target_image in case.target_images:
        try:
            file_path = os.path.join("app", target_image.image_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass  # Continue even if file deletion fails
    
    for search_video in case.search_videos:
        try:
            file_path = os.path.join("app", search_video.video_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass  # Continue even if file deletion fails
    
    # Delete case from database (cascade will handle related records)
    db.session.delete(case)
    db.session.commit()
    
    flash(f"Case for {person_name} has been completely removed.", "success")
    return redirect(url_for("main.profile"))


@bp.route("/case_status/<int:case_id>")
@login_required
@case_owner_required
def case_status(case_id):
    case = Case.query.get_or_404(case_id)
    sightings = []
    for s in case.sightings:
        video_name = (
            s.search_video.video_path.split("/")[-1] if s.search_video else "N/A"
        )
        sightings.append(
            {
                "video_name": video_name,
                "timestamp": s.timestamp,
                "confidence_score": round(s.confidence_score, 2),
                "thumbnail_path": url_for(
                    "static", filename=s.thumbnail_path.replace("static\\", "/")
                ),
            }
        )
    response_data = {"status": case.status, "sightings": sightings}
    return jsonify(response_data)


@bp.route("/notifications")
@login_required
def notifications():
    """User notifications page"""
    from app.models import Notification

    # Get all notifications for current user, ordered by newest first
    user_notifications = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )

    # Don't automatically mark as read - let user choose

    return render_template(
        "notifications.html", title="Notifications", notifications=user_notifications
    )


@bp.route("/missing_persons")
@login_required
def missing_persons():
    """Public directory of missing persons cases"""
    cases = (
        Case.query.filter(Case.status.in_(["Queued", "Processing", "Completed"]))
        .order_by(Case.created_at.desc())
        .all()
    )
    return render_template(
        "missing_persons.html", cases=cases, title="Missing Persons Directory"
    )


@bp.route("/about")
def about():
    """About page - detailed platform information"""
    return render_template("about.html", title="About the Platform")


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact page - available to all users"""
    form = ContactForm()

    # Pre-populate form with user data if logged in
    if current_user.is_authenticated and request.method == "GET":
        form.name.data = current_user.username
        form.email.data = current_user.email

    if request.method == "POST":
        # Handle both form validation and direct form data
        if form.validate_on_submit():
            name = form.name.data
            email = form.email.data
            subject = form.subject.data
            message = form.message.data
        else:
            # Fallback to request.form for hardcoded HTML form
            name = request.form.get('name')
            email = request.form.get('email')
            subject = request.form.get('subject')
            message = request.form.get('message')
        
        if name and email and subject and message:
            # Save message to database
            from app.models import ContactMessage
            contact_message = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            db.session.add(contact_message)
            db.session.commit()
            
            flash("Thank you for your message! We will get back to you shortly.", "success")
            return redirect(url_for("main.contact"))
        else:
            flash("Please fill in all required fields.", "error")

    return render_template("contact.html", title="Contact & Help", form=form)


@bp.route("/privacy")
def privacy():
    """Privacy & Security page"""
    return render_template("privacy.html", title="Privacy & Security")


@bp.route("/faq")
def faq():
    """FAQ page"""
    return render_template("faq.html", title="Frequently Asked Questions")


@bp.route("/chat")
@login_required
def chat_list():
    """List all chat rooms for current user"""
    from app.models import ChatRoom, User
    
    if current_user.is_admin:
        # Admin sees all chat rooms where they are the admin
        chat_rooms = ChatRoom.query.filter_by(admin_id=current_user.id).order_by(ChatRoom.last_message_at.desc()).all()
    else:
        # Regular user sees their chat rooms
        chat_rooms = ChatRoom.query.filter_by(user_id=current_user.id).order_by(ChatRoom.last_message_at.desc()).all()
        
        # If no chat room exists, create one with first available admin
        if not chat_rooms:
            admin = User.query.filter_by(is_admin=True).first()
            if admin:
                new_room = ChatRoom(user_id=current_user.id, admin_id=admin.id)
                db.session.add(new_room)
                db.session.commit()
                chat_rooms = [new_room]
            else:
                # No admin available, show message
                flash("No admin available for chat at the moment. Please try again later.", "warning")
    
    return render_template("chat/chat_list.html", chat_rooms=chat_rooms)


@bp.route("/chat/<int:room_id>")
@login_required
def chat_room(room_id):
    """Individual chat room"""
    from app.models import ChatRoom, ChatMessage
    
    room = ChatRoom.query.get_or_404(room_id)
    
    # Check access permissions
    if not current_user.is_admin and room.user_id != current_user.id:
        abort(403)
    if current_user.is_admin and room.admin_id != current_user.id:
        abort(403)
    
    # Get messages (exclude hidden ones for current user)
    try:
        messages_query = ChatMessage.query.filter_by(chat_room_id=room_id)
        
        if current_user.is_admin:
            messages_query = messages_query.filter((ChatMessage.hidden_for_admin == False) | (ChatMessage.hidden_for_admin == None))
        else:
            messages_query = messages_query.filter((ChatMessage.hidden_for_user == False) | (ChatMessage.hidden_for_user == None))
        
        messages = messages_query.order_by(ChatMessage.created_at.asc()).all()
    except Exception as e:
        print(f"Error loading messages: {e}")
        # Fallback to all messages if column doesn't exist
        messages = ChatMessage.query.filter_by(chat_room_id=room_id).order_by(ChatMessage.created_at.asc()).all()
    
    # Mark messages as seen (not just read)
    unread_messages = ChatMessage.query.filter_by(chat_room_id=room_id, is_read=False).filter(ChatMessage.sender_id != current_user.id).all()
    for msg in unread_messages:
        msg.mark_seen()
    
    return render_template("chat/chat_room.html", room=room, messages=messages, timedelta=timedelta)


@bp.route("/chat/<int:room_id>/send", methods=["POST"])
@login_required
def send_message(room_id):
    """Send a message in chat room"""
    try:
        from app.models import ChatRoom, ChatMessage, Notification, User
        
        print(f"Send message request for room {room_id} from user {current_user.id}")
        
        room = ChatRoom.query.get_or_404(room_id)
        
        # Check access permissions
        if not current_user.is_admin and room.user_id != current_user.id:
            print(f"Access denied: User {current_user.id} not authorized for room {room_id}")
            return jsonify({'error': 'Access denied'}), 403
        if current_user.is_admin and room.admin_id != current_user.id:
            print(f"Access denied: Admin {current_user.id} not authorized for room {room_id}")
            return jsonify({'error': 'Access denied'}), 403
        
        message_content = request.form.get('message', '').strip()
        file = request.files.get('file')
        
        print(f"Message content: '{message_content}', File: {file}")
        
        if not message_content and not file:
            print("No message content or file provided")
            return jsonify({'error': 'Message or file required'}), 400
        
        # Create message with current timestamp and initial status 'sent'
        message = ChatMessage(
            chat_room_id=room_id,
            sender_id=current_user.id,
            content=message_content if message_content else None,
            message_type='text',
            status='sent',
            created_at=get_ist_now()
        )
        
        # Handle file upload
        if file and file.filename:
            import os
            from werkzeug.utils import secure_filename
            
            filename = secure_filename(file.filename)
            if not filename:
                return jsonify({'error': 'Invalid filename'}), 400
                
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            # Determine message type
            if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
                message.message_type = 'image'
            elif file_ext in ['mp4', 'avi', 'mov', 'webm', 'mkv']:
                message.message_type = 'video'
            else:
                message.message_type = 'file'
            
            # Save file
            upload_dir = os.path.join('app', 'static', 'chat_uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            unique_filename = f"chat_{room_id}_{get_ist_now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            try:
                file.save(file_path)
                message.file_path = f"chat_uploads/{unique_filename}"
                message.file_name = filename
            except Exception as e:
                return jsonify({'error': f'File upload failed: {str(e)}'}), 500
        
        db.session.add(message)
        db.session.flush()  # Get message ID
        
        # Mark as delivered immediately (simulating instant delivery)
        message.mark_delivered()
        
        # Update room last message time
        room.last_message_at = get_ist_now()
        
        # Create notification for recipient
        recipient_id = room.admin_id if current_user.id == room.user_id else room.user_id
        notification = Notification(
            user_id=recipient_id,
            sender_id=current_user.id,
            title="New Chat Message",
            message=f"{current_user.username}: {message_content[:50]}..." if message_content else f"{current_user.username} sent a file",
            type="chat",
            related_url=f"/chat/{room_id}",
            created_at=get_ist_now()
        )
        db.session.add(notification)
        
        db.session.commit()
        
        print(f"Message {message.id} created successfully with status {message.status}")
        
        return jsonify({
            'success': True, 
            'message_id': message.id,
            'status': message.status,
            'message': 'Message sent successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in send_message: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@bp.route("/chat/<int:room_id>/messages")
@login_required
def get_messages(room_id):
    """Get messages for chat room (AJAX)"""
    from app.models import ChatRoom, ChatMessage
    
    room = ChatRoom.query.get_or_404(room_id)
    
    # Check access permissions
    if not current_user.is_admin and room.user_id != current_user.id:
        abort(403)
    if current_user.is_admin and room.admin_id != current_user.id:
        abort(403)
    
    since = request.args.get('since', type=int, default=0)
    
    try:
        messages_query = ChatMessage.query.filter_by(chat_room_id=room_id).filter(ChatMessage.id > since)
        
        if current_user.is_admin:
            messages_query = messages_query.filter((ChatMessage.hidden_for_admin == False) | (ChatMessage.hidden_for_admin == None))
        else:
            messages_query = messages_query.filter((ChatMessage.hidden_for_user == False) | (ChatMessage.hidden_for_user == None))
        
        messages = messages_query.order_by(ChatMessage.created_at.asc()).all()
    except Exception as e:
        print(f"Error loading messages: {e}")
        # Fallback to all messages if column doesn't exist
        messages = ChatMessage.query.filter_by(chat_room_id=room_id).filter(ChatMessage.id > since).order_by(ChatMessage.created_at.asc()).all()
    
    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'sender_name': msg.sender.username,
            'content': msg.content,
            'message_type': msg.message_type,
            'file_path': msg.file_path,
            'file_name': msg.file_name,
            'created_at': msg.created_at.isoformat(),
            'created_at_ist': utc_to_ist(msg.created_at).strftime('%I:%M %p IST'),
            'is_own': msg.sender_id == current_user.id,
            'status': msg.status,
            'delivered_at': utc_to_ist(msg.delivered_at).strftime('%I:%M %p IST') if msg.delivered_at else None,
            'seen_at': utc_to_ist(msg.seen_at).strftime('%I:%M %p IST') if msg.seen_at else None
        })
    
    return jsonify({'messages': messages_data})


@bp.route("/api/chat-notifications")
@login_required
def chat_notifications():
    """Get unread chat count for current user"""
    from app.models import ChatRoom, ChatMessage
    
    if current_user.is_admin:
        # Count unread messages from users to admin
        unread_count = db.session.query(ChatMessage).join(ChatRoom).filter(
            ChatRoom.admin_id == current_user.id,
            ChatMessage.is_read == False,
            ChatMessage.sender_id != current_user.id
        ).count()
    else:
        # Count unread messages from admin to user
        unread_count = db.session.query(ChatMessage).join(ChatRoom).filter(
            ChatRoom.user_id == current_user.id,
            ChatMessage.is_read == False,
            ChatMessage.sender_id != current_user.id
        ).count()
    
    return jsonify({'unread_count': unread_count})


@bp.route("/chat/start")
@login_required
def start_chat():
    """Start a new chat with admin (for users) or redirect to chat list"""
    from app.models import ChatRoom, User
    
    if current_user.is_admin:
        return redirect(url_for('main.chat_list'))
    
    # Check if user already has a chat room
    existing_room = ChatRoom.query.filter_by(user_id=current_user.id).first()
    if existing_room:
        return redirect(url_for('main.chat_room', room_id=existing_room.id))
    
    # Create new chat room with first available admin
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        flash("No admin available for chat at the moment. Please try again later.", "warning")
        return redirect(url_for('main.contact'))
    
    new_room = ChatRoom(user_id=current_user.id, admin_id=admin.id)
    db.session.add(new_room)
    db.session.commit()
    
    return redirect(url_for('main.chat_room', room_id=new_room.id))


@bp.route("/api/chat/<int:room_id>/mark-seen", methods=["POST"])
@login_required
def mark_messages_seen(room_id):
    """Mark all messages in room as seen by current user"""
    from app.models import ChatRoom, ChatMessage
    
    room = ChatRoom.query.get_or_404(room_id)
    
    # Check access permissions
    if not current_user.is_admin and room.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    if current_user.is_admin and room.admin_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Mark all unread messages from other user as seen
    unread_messages = ChatMessage.query.filter_by(
        chat_room_id=room_id, 
        is_read=False
    ).filter(ChatMessage.sender_id != current_user.id).all()
    
    for msg in unread_messages:
        msg.mark_seen()
    
    return jsonify({'success': True, 'marked_count': len(unread_messages)})


@bp.route("/api/announcement/<int:announcement_id>/mark-read", methods=["POST"])
@login_required
def mark_announcement_read(announcement_id):
    """Mark announcement as read for current user"""
    try:
        # Check if already marked as read
        existing = AnnouncementRead.query.filter_by(
            user_id=current_user.id,
            announcement_id=announcement_id
        ).first()
        
        if not existing:
            # Mark as read
            read_record = AnnouncementRead(
                user_id=current_user.id,
                announcement_id=announcement_id,
                read_at=get_ist_now()
            )
            db.session.add(read_record)
            db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route("/api/chat/message-status/<int:message_id>")
@login_required
def get_message_status(message_id):
    """Get status of a specific message"""
    from app.models import ChatMessage
    
    message = ChatMessage.query.get_or_404(message_id)
    
    # Only sender can check message status
    if message.sender_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'message_id': message.id,
        'status': message.status,
        'delivered_at': message.delivered_at.isoformat() if message.delivered_at else None,
        'seen_at': message.seen_at.isoformat() if message.seen_at else None
    })


@bp.route("/api/chat/<int:room_id>/clear", methods=["POST"])
@login_required
def clear_chat_history(room_id):
    """Hide messages for current user only"""
    from app.models import ChatRoom, ChatMessage
    
    room = ChatRoom.query.get_or_404(room_id)
    
    # Check access permissions
    if not current_user.is_admin and room.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    if current_user.is_admin and room.admin_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Hide messages for current user only
    try:
        messages = ChatMessage.query.filter_by(chat_room_id=room_id).all()
        
        for message in messages:
            if current_user.is_admin:
                message.hidden_for_admin = True
            else:
                message.hidden_for_user = True
        
        db.session.commit()
    except Exception as e:
        print(f"Error clearing messages: {e}")
        return jsonify({'error': 'Failed to clear messages'}), 500
    
    return jsonify({'success': True, 'message': 'Chat history cleared for you only'})


@bp.route("/api/user/<int:user_id>/status")
@login_required
def get_user_status(user_id):
    """Get online status and last seen for a user"""
    user = User.query.get_or_404(user_id)
    
    # Calculate if user is considered online (active within last 5 minutes)
    now = get_ist_now()
    online_threshold = now - timedelta(minutes=5)
    
    # Ensure both datetimes have timezone info for comparison
    user_last_seen_tz = utc_to_ist(user.last_seen) if user.last_seen and user.last_seen.tzinfo is None else user.last_seen
    is_online = user.is_online and (user_last_seen_tz and user_last_seen_tz > online_threshold)
    
    # Format last seen time
    last_seen_text = "Never"
    if user.last_seen:
        # Convert to IST if needed
        user_last_seen = utc_to_ist(user.last_seen) if user.last_seen.tzinfo is None else user.last_seen
        time_diff = now - user_last_seen
        if time_diff.total_seconds() < 60:
            last_seen_text = "Just now"
        elif time_diff.total_seconds() < 3600:
            minutes = int(time_diff.total_seconds() / 60)
            last_seen_text = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif time_diff.total_seconds() < 86400:
            hours = int(time_diff.total_seconds() / 3600)
            last_seen_text = f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            last_seen_text = user_last_seen.strftime('%d %b %Y at %I:%M %p IST')
    
    return jsonify({
        'user_id': user.id,
        'username': user.username,
        'is_online': is_online,
        'last_seen': last_seen_text,
        'last_seen_timestamp': utc_to_ist(user.last_seen).isoformat() if user.last_seen else None
    })


@bp.route("/api/user/update-activity", methods=["POST"])
@login_required
def update_user_activity():
    """Update user's last seen timestamp"""
    current_user.last_seen = get_ist_now()
    current_user.is_online = True
    db.session.commit()
    return jsonify({'success': True})


@bp.route("/api/notification/<int:notification_id>/mark-read", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    """Mark a specific notification as read"""
    from app.models import Notification
    
    notification = Notification.query.get_or_404(notification_id)
    
    # Check if user owns this notification
    if notification.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        notification.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route("/api/notification/<int:notification_id>/delete", methods=["POST"])
@login_required
def delete_notification(notification_id):
    """Delete a specific notification"""
    from app.models import Notification
    
    notification = Notification.query.get_or_404(notification_id)
    
    # Check if user owns this notification
    if notification.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        db.session.delete(notification)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route("/api/notifications/clear-all", methods=["POST"])
@login_required
def clear_all_notifications():
    """Delete all notifications for current user"""
    from app.models import Notification
    
    try:
        Notification.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route("/api/notifications/count")
@login_required
def get_notification_count():
    """Get unread notification count for current user"""
    from app.models import Notification
    
    try:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return jsonify({'unread_count': unread_count})
    except Exception as e:
        return jsonify({'unread_count': 0, 'error': str(e)}), 500
