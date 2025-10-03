from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response, send_file, abort
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Case, SystemLog, AdminMessage, Announcement, BlogPost, FAQ, AISettings, Sighting, ContactMessage, ChatRoom, ChatMessage, SurveillanceFootage, LocationMatch, PersonDetection, Notification
from werkzeug.utils import secure_filename
import os
import cv2
import io
from sqlalchemy import func, desc, and_, or_, case
from datetime import datetime, timedelta, date
import csv
import io
import json
from app.models import get_ist_now

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    # Basic statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_cases = Case.query.count()
    pending_approvals = Case.query.filter_by(status="Pending Approval").count()
    total_sightings = Sighting.query.count()
    
    # Announcement statistics
    try:
        active_announcements = Announcement.query.filter_by(is_active=True).count()
    except Exception:
        active_announcements = 0
    
    # Status distribution
    status_counts = db.session.query(Case.status, func.count(Case.id)).group_by(Case.status).all()
    
    # Time-based analytics
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_cases_raw = (
        db.session.query(
            func.date(Case.created_at).label("date"), 
            func.count(Case.id).label("count")
        )
        .filter(Case.created_at >= thirty_days_ago)
        .group_by(func.date(Case.created_at))
        .all()
    )
    
    # Convert date objects to formatted strings
    daily_cases = []
    for date_obj, count in daily_cases_raw:
        if date_obj:
            if isinstance(date_obj, str):
                # If it's already a string, parse it first
                try:
                    parsed_date = datetime.strptime(str(date_obj), "%Y-%m-%d")
                    formatted_date = parsed_date.strftime("%m/%d")
                except:
                    formatted_date = str(date_obj)
            else:
                # If it's a date object, format it directly
                formatted_date = date_obj.strftime("%m/%d")
        else:
            formatted_date = ""
        daily_cases.append((formatted_date, count))
    
    # AI Performance metrics
    avg_processing_time = db.session.query(
        func.avg(func.extract('epoch', Case.updated_at - Case.created_at))
    ).filter(Case.status.in_(['Completed', 'Active'])).scalar() or 0
    
    high_confidence_matches = Sighting.query.filter(Sighting.confidence_score > 0.8).count()
    
    # Geographic data (top locations)
    location_stats = (
        db.session.query(
            Case.last_seen_location,
            func.count(Case.id).label('case_count')
        )
        .filter(Case.last_seen_location.isnot(None))
        .group_by(Case.last_seen_location)
        .order_by(desc('case_count'))
        .limit(10)
        .all()
    )
    
    # Recent activity
    recent_logs = SystemLog.query.order_by(desc(SystemLog.timestamp)).limit(10).all()
    
    # Contact messages (with error handling for missing table)
    try:
        unread_messages = ContactMessage.query.filter_by(is_read=False).count()
        recent_contact_messages = ContactMessage.query.order_by(desc(ContactMessage.created_at)).limit(5).all()
    except Exception:
        unread_messages = 0
        recent_contact_messages = []
    
    # Recent cases with error handling
    try:
        recent_cases = Case.query.order_by(desc(Case.created_at)).limit(10).all()
    except Exception:
        recent_cases = []
    
    # Chat statistics
    try:
        active_chats = ChatRoom.query.filter_by(is_active=True).count()
        total_chat_messages = ChatMessage.query.count()
    except Exception:
        active_chats = 0
        total_chat_messages = 0
    
    # AI Analysis Statistics with error handling
    try:
        from app.models import LocationMatch, PersonDetection, SurveillanceFootage
        # Only count real footage (not test data)
        real_footage_count = SurveillanceFootage.query.filter(
            and_(
                ~SurveillanceFootage.video_path.like('%test%'),
                ~SurveillanceFootage.title.like('%Test%')
            )
        ).count()
        total_location_matches = LocationMatch.query.join(SurveillanceFootage).filter(
            and_(
                ~SurveillanceFootage.video_path.like('%test%'),
                ~SurveillanceFootage.title.like('%Test%')
            )
        ).count()
        successful_detections = LocationMatch.query.join(SurveillanceFootage).filter(
            LocationMatch.person_found == True,
            ~SurveillanceFootage.video_path.like('%test%'),
            ~SurveillanceFootage.title.like('%Test%')
        ).count()
        pending_analysis = LocationMatch.query.join(SurveillanceFootage).filter(
            LocationMatch.status == 'pending',
            ~SurveillanceFootage.video_path.like('%test%'),
            ~SurveillanceFootage.title.like('%Test%')
        ).count()
        processing_analysis = LocationMatch.query.join(SurveillanceFootage).filter(
            LocationMatch.status == 'processing',
            ~SurveillanceFootage.video_path.like('%test%'),
            ~SurveillanceFootage.title.like('%Test%')
        ).count()
    except Exception:
        real_footage_count = 0
        total_location_matches = 0
        successful_detections = 0
        pending_analysis = 0
        processing_analysis = 0
    
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        active_users=active_users,
        total_cases=total_cases,
        total_sightings=total_sightings,
        status_counts=status_counts,
        daily_cases=daily_cases,
        avg_processing_time=avg_processing_time,
        high_confidence_matches=high_confidence_matches,
        location_stats=location_stats,
        recent_logs=recent_logs,
        unread_messages=unread_messages,
        recent_contact_messages=recent_contact_messages,
        active_chats=active_chats,
        total_chat_messages=total_chat_messages,
        recent_cases=recent_cases,
        real_footage_count=real_footage_count,
        total_location_matches=total_location_matches,
        successful_detections=successful_detections,
        pending_analysis=pending_analysis,
        processing_analysis=processing_analysis,
        active_announcements=active_announcements,
        pending_approvals=pending_approvals
    )


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    role_filter = request.args.get('role', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    query = User.query
    
    # Apply search filter with enhanced matching
    if search:
        search_term = f"%{search.strip().lower()}%"
        # Split search term for better matching
        search_words = search.strip().lower().split()
        
        if len(search_words) == 1:
            # Single word search - use ilike for partial matching
            query = query.filter(or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term)
            ))
        else:
            # Multiple words - search each word
            conditions = []
            for word in search_words:
                word_term = f"%{word}%"
                conditions.extend([
                    User.username.ilike(word_term),
                    User.email.ilike(word_term)
                ])
            query = query.filter(or_(*conditions))
    
    # Apply status filter
    if status_filter == 'active':
        query = query.filter(User.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(User.is_active == False)
    
    # Apply role filter
    if role_filter == 'admin':
        query = query.filter(User.is_admin == True)
    elif role_filter == 'user':
        query = query.filter(User.is_admin == False)
    
    # Apply sorting
    if sort_by == 'username':
        sort_column = User.username
    elif sort_by == 'email':
        sort_column = User.email
    elif sort_by == 'last_login':
        sort_column = User.last_login
    else:
        sort_column = User.created_at
    
    if sort_order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    users = query.paginate(page=page, per_page=20, error_out=False)
    
    # Calculate statistics
    total_cases_on_page = sum(len(user.cases) for user in users.items)
    active_users = User.query.filter(User.last_login.isnot(None)).count()
    admin_users = User.query.filter(User.is_admin == True).count()
    
    # Debug info for search
    debug_info = None
    if search:
        debug_info = {
            'search_term': search,
            'total_found': users.total if users else 0,
            'available_users': [u.username for u in User.query.all()]
        }
    
    return render_template(
        "admin/users.html", 
        users=users, 
        search=search,
        status_filter=status_filter,
        role_filter=role_filter,
        sort_by=sort_by,
        sort_order=sort_order,
        total_cases=total_cases_on_page,
        active_users=active_users,
        admin_users=admin_users,
        moment=datetime,
        debug_info=debug_info
    )


@admin_bp.route("/users/<int:user_id>/toggle_admin", methods=["POST"])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("❌ Cannot modify your own admin status", "error")
        return redirect(url_for("admin.users"))

    old_status = user.is_admin
    user.is_admin = not user.is_admin
    
    try:
        db.session.commit()
        status_text = "granted" if user.is_admin else "revoked"
        flash(f"✅ Admin privileges {status_text} for {user.username}", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Failed to update admin status: {str(e)}", "error")
    
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("❌ Cannot delete your own account", "error")
        return redirect(url_for("admin.users"))

    username = user.username
    case_count = len(user.cases)
    
    try:
        # Delete user files first
        import os
        for case in user.cases:
            # Delete case images
            for image in case.target_images:
                try:
                    file_path = os.path.join("app", image.image_path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass
            
            # Delete case videos
            for video in case.search_videos:
                try:
                    file_path = os.path.join("app", video.video_path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass
        
        # Delete user from database (cascade will handle related records)
        db.session.delete(user)
        db.session.commit()
        
        flash(f"✅ User '{username}' and all associated data deleted successfully ({case_count} cases removed)", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Failed to delete user: {str(e)}", "error")
    
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>")
@login_required
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    
    # Calculate total sightings across all user's cases
    total_sightings = sum(len(case.sightings) for case in user.cases)
    
    # Get recent activity logs for this user
    activity_logs = SystemLog.query.filter_by(user_id=user_id).order_by(desc(SystemLog.timestamp)).limit(10).all()
    
    return render_template(
        "admin/user_detail.html", 
        user=user, 
        total_sightings=total_sightings,
        activity_logs=activity_logs
    )


@admin_bp.route("/impersonate/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def impersonate_user(user_id):
    from flask_login import logout_user, login_user
    from flask import session
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot impersonate yourself'}), 400
    
    # Store admin user ID for later restoration
    session['impersonating_admin_id'] = current_user.id
    session['is_impersonating'] = True
    
    # Log the impersonation
    log = SystemLog(
        user_id=user_id,
        action='admin_impersonation',
        details=f'Admin {current_user.username} logged in as {user.username}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    login_user(user)
    
    return jsonify({'success': True})


@admin_bp.route("/stop_impersonation", methods=["POST"])
@login_required
def stop_impersonation():
    from flask_login import logout_user, login_user
    from flask import session
    
    if not session.get('is_impersonating'):
        return jsonify({'error': 'Not currently impersonating'}), 400
    
    admin_id = session.get('impersonating_admin_id')
    if not admin_id:
        return jsonify({'error': 'Admin ID not found'}), 400
    
    admin_user = User.query.get(admin_id)
    if not admin_user:
        return jsonify({'error': 'Admin user not found'}), 400
    
    # Log the end of impersonation
    log = SystemLog(
        user_id=admin_id,
        action='admin_impersonation_end',
        details=f'Admin {admin_user.username} stopped impersonating {current_user.username}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    login_user(admin_user)
    
    session.pop('impersonating_admin_id', None)
    session.pop('is_impersonating', None)
    
    return jsonify({'success': True})


@admin_bp.route("/cases")
@login_required
@admin_required
def cases():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = Case.query
    
    # Apply filters
    if status_filter:
        query = query.filter_by(status=status_filter)
    if search:
        query = query.filter(or_(
            Case.person_name.contains(search),
            Case.last_seen_location.contains(search)
        ))
    
    cases = query.order_by(desc(Case.created_at)).paginate(
        page=page, per_page=12, error_out=False
    )
    
    # Statistics
    total_cases = Case.query.count()
    active_cases = Case.query.filter(Case.status.in_(['Pending Approval', 'Queued', 'Processing', 'Active'])).count()
    completed_cases = Case.query.filter_by(status='Completed').count()
    
    return render_template(
        "admin/cases.html", 
        cases=cases,
        total_cases=total_cases,
        active_cases=active_cases,
        completed_cases=completed_cases,
        status_filter=status_filter,
        search=search
    )


@admin_bp.route("/cases/<int:case_id>")
@login_required
@admin_required
def case_detail(case_id):
    """Detailed admin view of a specific case with full AI analysis"""
    try:
        case = Case.query.get_or_404(case_id)
        
        # Get system logs
        logs = (
            SystemLog.query.filter_by(case_id=case_id)
            .order_by(SystemLog.timestamp.desc())
            .all()
        )
        
        # Get AI analysis results
        from app.models import LocationMatch, PersonDetection
        location_matches = LocationMatch.query.filter_by(case_id=case_id).all()
        
        # Get all detections with match info
        all_detections = []
        for match in location_matches:
            detections = PersonDetection.query.filter_by(location_match_id=match.id).all()
            for detection in detections:
                detection.match = match
                all_detections.append(detection)
        
        # Sort by confidence and timestamp
        all_detections.sort(key=lambda x: (x.confidence_score, x.timestamp), reverse=True)
        
        # Calculate analysis statistics
        analysis_stats = {
            'total_matches': len(location_matches),
            'successful_matches': len([m for m in location_matches if m.person_found]),
            'total_detections': len(all_detections),
            'high_confidence_detections': len([d for d in all_detections if d.confidence_score > 0.7]),
            'processing_matches': len([m for m in location_matches if m.status == 'processing']),
            'pending_matches': len([m for m in location_matches if m.status == 'pending'])
        }
        
        return render_template(
            "admin/case_detail.html", 
            case=case, 
            logs=logs,
            location_matches=location_matches,
            detections=all_detections,
            analysis_stats=analysis_stats
        )
        
    except Exception as e:
        logger.error(f"Error loading admin case detail {case_id}: {str(e)}")
        flash("Error loading case details. Please try again.", "error")
        return redirect(url_for("admin.cases"))


@admin_bp.route("/cases/<int:case_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_case(case_id):
    try:
        # Check if user is authenticated and is admin
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("❌ Access denied", "error")
            return redirect(url_for("admin.cases"))
        
        # Check for confirmation
        if not request.form.get('confirm_delete'):
            flash("❌ Delete confirmation required", "error")
            return redirect(url_for("admin.case_detail", case_id=case_id))
        
        case = Case.query.get_or_404(case_id)
        person_name = case.person_name
        
        # Log the deletion attempt
        try:
            log = SystemLog(
                case_id=case_id,
                user_id=current_user.id,
                action='case_deleted',
                details=f'Admin {current_user.username} deleted case for {person_name}',
                ip_address=request.remote_addr
            )
            db.session.add(log)
        except:
            pass  # Don't fail if logging fails
        
        # Delete case from database (cascade will handle related records)
        db.session.delete(case)
        db.session.commit()
        
        flash(f"✅ Case for {person_name} deleted successfully", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error deleting case: {str(e)}", "error")
    
    return redirect(url_for("admin.cases"))


@admin_bp.route("/cases/<int:case_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_case(case_id):
    case = Case.query.get_or_404(case_id)
    
    if case.status != "Pending Approval":
        flash("Case is not pending approval", "error")
        return redirect(url_for("admin.case_detail", case_id=case_id))
    
    # Check if there's footage available for this location
    from app.ai_location_matcher import ai_matcher
    nearby_footage = ai_matcher.find_nearby_footage(case.last_seen_location)
    
    if not nearby_footage:
        # No footage available - show notification to admin
        flash(f"⚠️ No CCTV footage available for location '{case.last_seen_location}' or nearby areas. Please upload relevant footage or this case cannot be processed effectively.", "warning")
        return redirect(url_for("admin.case_review", case_id=case_id))
    
    case.status = "Approved"
    db.session.commit()
    
    # Notify user about approval
    from app.models import Notification
    notification = Notification(
        user_id=case.user_id,
        sender_id=current_user.id,
        title=f"✅ Case Approved: {case.person_name}",
        message=f"Your missing person case for {case.person_name} has been approved. AI analysis will begin shortly with available CCTV footage from {len(nearby_footage)} locations.",
        type="success",
        created_at=get_ist_now()
    )
    db.session.add(notification)
    db.session.commit()
    
    # Start AI processing with location matching
    try:
        matches_created = ai_matcher.process_new_case(case_id)
        if matches_created > 0:
            case.status = "Processing"
            db.session.commit()
            flash(f"Case approved! AI analysis started with {matches_created} footage matches.", "success")
        else:
            flash(f"Case approved but no suitable footage matches found.", "warning")
    except Exception as e:
        flash(f"Case approved but AI processing failed: {str(e)}", "warning")
    
    return redirect(url_for("admin.case_detail", case_id=case_id))


@admin_bp.route("/cases/<int:case_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_case(case_id):
    case = Case.query.get_or_404(case_id)
    
    if case.status != "Pending Approval":
        flash("Case is not pending approval", "error")
        return redirect(url_for("admin.case_detail", case_id=case_id))
    
    rejection_reason = request.form.get('rejection_reason', 'No reason provided')
    case.status = "Rejected"
    db.session.commit()
    
    # Notify user about rejection
    from app.models import Notification
    notification = Notification(
        user_id=case.user_id,
        sender_id=current_user.id,
        title=f"❌ Case Rejected: {case.person_name}",
        message=f"Your missing person case for {case.person_name} has been rejected.\n\nReason: {rejection_reason}\n\nPlease review and resubmit with correct information.",
        type="danger",
        created_at=get_ist_now()
    )
    db.session.add(notification)
    db.session.commit()
    
    flash(f"Case for {case.person_name} has been rejected", "success")
    return redirect(url_for("admin.case_detail", case_id=case_id))


@admin_bp.route("/cases/<int:case_id>/requeue", methods=["POST"])
@login_required
@admin_required
def requeue_case(case_id):
    case = Case.query.get_or_404(case_id)
    case.status = "Queued"
    case.completed_at = None
    db.session.commit()

    from app.tasks import process_case
    process_case.delay(case_id)

    flash(f"Case for {case.person_name} re-queued for processing")
    return redirect(url_for("admin.case_detail", case_id=case_id))


# ===== ADVANCED ADMIN FEATURES =====

# Data Export Routes
@admin_bp.route("/export/users")
@login_required
@admin_required
def export_users():
    users = User.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    
    # CSV headers
    writer.writerow(['ID', 'Username', 'Email', 'Is Admin', 'Active', 'Cases Count', 'Created At', 'Last Login', 'Location'])
    
    for user in users:
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.is_admin,
            user.is_active,
            len(user.cases),
            user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
            user.location or 'Not specified'
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )


@admin_bp.route("/export/cases")
@login_required
@admin_required
def export_cases():
    cases = Case.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Person Name', 'Age', 'Status', 'Priority', 'Creator', 'Location', 'Sightings', 'Created At'])
    
    for case in cases:
        writer.writerow([
            case.id,
            case.person_name,
            case.age or 'Unknown',
            case.status,
            case.priority,
            case.creator.username,
            case.last_seen_location or 'Not specified',
            case.total_sightings,
            case.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'cases_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )


# Analytics Routes
@admin_bp.route("/analytics")
@login_required
@admin_required
def analytics():
    try:
        # Basic statistics
        total_cases = Case.query.count()
        total_users = User.query.count()
        total_sightings = Sighting.query.count()
        
        # Case status distribution - convert to tuples
        processing_results = db.session.query(
            Case.status,
            func.count(Case.id).label('count')
        ).group_by(Case.status).all()
        
        # Convert Row objects to tuples
        processing_stats = [(row[0], row[1]) for row in processing_results]
        
        # Simple confidence distribution without complex CASE statements
        confidence_distribution = []
        try:
            very_high = Sighting.query.filter(Sighting.confidence_score >= 0.90).count()
            high = Sighting.query.filter(and_(Sighting.confidence_score >= 0.80, Sighting.confidence_score < 0.90)).count()
            medium = Sighting.query.filter(and_(Sighting.confidence_score >= 0.60, Sighting.confidence_score < 0.80)).count()
            low = Sighting.query.filter(and_(Sighting.confidence_score >= 0.40, Sighting.confidence_score < 0.60)).count()
            very_low = Sighting.query.filter(Sighting.confidence_score < 0.40).count()
            
            confidence_distribution = [
                ('Very High (90%+)', very_high),
                ('High (80-89%)', high),
                ('Medium (60-79%)', medium),
                ('Low (40-59%)', low),
                ('Very Low (<40%)', very_low)
            ]
        except Exception:
            confidence_distribution = [('No Data', 0)]
        
        # Geographic data - convert to tuples for template compatibility
        location_data = []
        try:
            location_results = db.session.query(
                Case.last_seen_location,
                func.count(Case.id).label('case_count')
            ).filter(Case.last_seen_location.isnot(None)).group_by(Case.last_seen_location).all()
            
            # Convert Row objects to tuples
            location_data = [(row[0], row[1]) for row in location_results]
        except Exception:
            location_data = []
        
        # AI Performance metrics
        ai_stats = {
            'total_matches': 0,
            'successful_matches': 0,
            'pending_analysis': 0,
            'avg_confidence': 0.0
        }
        
        try:
            from app.models import LocationMatch
            ai_stats['total_matches'] = LocationMatch.query.count()
            ai_stats['successful_matches'] = LocationMatch.query.filter_by(person_found=True).count()
            ai_stats['pending_analysis'] = LocationMatch.query.filter_by(status='pending').count()
            
            avg_conf = db.session.query(func.avg(Sighting.confidence_score)).scalar()
            ai_stats['avg_confidence'] = round(avg_conf or 0.0, 2)
        except Exception:
            pass
        
        return render_template(
            "admin/analytics.html",
            total_cases=total_cases,
            total_users=total_users,
            total_sightings=total_sightings,
            processing_stats=processing_stats,
            confidence_distribution=confidence_distribution,
            location_data=location_data,
            ai_stats=ai_stats
        )
        
    except Exception as e:
        flash(f"Error loading analytics: {str(e)}", "error")
        return redirect(url_for("admin.dashboard"))


# User Messaging System
@admin_bp.route("/messages")
@login_required
@admin_required
def messages():
    sent_messages = AdminMessage.query.filter_by(sender_id=current_user.id).order_by(desc(AdminMessage.created_at)).all()
    return render_template("admin/messages.html", sent_messages=sent_messages)




@admin_bp.route("/send-message/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def send_message(user_id):
    from app.models import Notification
    user = User.query.get_or_404(user_id)
    
    subject = request.form.get('subject', 'Admin Message')
    message_content = request.form.get('message', '')
    
    if not message_content.strip():
        flash("Message cannot be empty.", "error")
        return redirect(url_for("admin.users"))
    
    try:
        # Create admin message record
        admin_message = AdminMessage(
            sender_id=current_user.id,
            recipient_id=user_id,
            subject=subject,
            content=message_content
        )
        db.session.add(admin_message)
        
        # Create notification for user
        notification = Notification(
            user_id=user_id,
            sender_id=current_user.id,
            title=f"Message from Admin: {subject}",
            message=message_content,
            type="info",
            created_at=get_ist_now()
        )
        db.session.add(notification)
        db.session.commit()
        
        flash(f"✅ Message sent to {user.username} successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to send message: {str(e)}", "error")
    
    return redirect(url_for("admin.users"))


# Announcement Management
@admin_bp.route("/announcements")
@login_required
@admin_required
def announcements():
    announcements = Announcement.query.order_by(desc(Announcement.created_at)).all()
    return render_template("admin/announcements.html", announcements=announcements)


@admin_bp.route("/announcements/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_announcement():
    # Calculate tomorrow's date
    tomorrow = date.today() + timedelta(days=1)
    
    if request.method == "POST":
        title = request.form.get('title')
        content = request.form.get('content')
        type = request.form.get('type', 'info')
        expires_at = request.form.get('expires_at')
        
        announcement = Announcement(
            title=title,
            content=content,
            type=type,
            created_by=current_user.id,
            created_at=get_ist_now(),
            expires_at=datetime.strptime(expires_at, '%Y-%m-%d') if expires_at else None
        )
        db.session.add(announcement)
        db.session.flush()  # Get announcement ID
        
        # Create notifications for all non-admin users
        from app.models import Notification
        regular_users = User.query.filter_by(is_admin=False).all()
        
        for user in regular_users:
            notification = Notification(
                user_id=user.id,
                sender_id=current_user.id,
                title=f"📢 New Announcement: {title}",
                message=content,
                type=type,
                created_at=get_ist_now()
            )
            db.session.add(notification)
        
        db.session.commit()
        
        flash(f"Announcement created and sent to {len(regular_users)} users!", "success")
        return redirect(url_for("admin.announcements"))
    
    return render_template("admin/create_announcement.html", tomorrow=tomorrow)


@admin_bp.route("/announcements/<int:announcement_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    announcement.is_active = not announcement.is_active
    db.session.commit()
    
    status = "activated" if announcement.is_active else "deactivated"
    flash(f"Announcement {status} successfully!", "success")
    return redirect(url_for("admin.announcements"))


@admin_bp.route("/announcements/<int:announcement_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_announcement(announcement_id):
    """Permanently delete an announcement"""
    try:
        announcement = Announcement.query.get_or_404(announcement_id)
        title = announcement.title
        
        # Delete all read records for this announcement
        try:
            from app.models import AnnouncementRead
            AnnouncementRead.query.filter_by(announcement_id=announcement_id).delete()
        except Exception:
            pass  # Table might not exist
        
        # Delete the announcement
        db.session.delete(announcement)
        db.session.commit()
        
        flash(f"Announcement '{title}' has been permanently deleted.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting announcement: {str(e)}", "error")
    
    return redirect(url_for("admin.announcements"))


# AI Settings Management
@admin_bp.route("/ai-settings")
@login_required
@admin_required
def ai_settings():
    settings = AISettings.query.all()
    
    # Initialize default settings if none exist
    if not settings:
        default_settings = [
            ('confidence_threshold', '0.7', 'Minimum confidence score for matches'),
            ('max_processing_time', '300', 'Maximum processing time per video (seconds)'),
            ('face_detection_model', 'hog', 'Face detection model (hog/cnn)'),
            ('enable_clothing_analysis', 'true', 'Enable clothing-based matching')
        ]
        
        for name, value, desc in default_settings:
            setting = AISettings(setting_name=name, setting_value=value, description=desc, updated_by=current_user.id)
            db.session.add(setting)
        
        db.session.commit()
        settings = AISettings.query.all()
    
    return render_template("admin/ai_settings.html", settings=settings)


@admin_bp.route("/ai-settings", methods=["POST"])
@login_required
@admin_required
def update_ai_settings():
    """Handle AI settings form submission"""
    for setting_id, value in request.form.items():
        if setting_id.startswith('setting_'):
            setting_id = setting_id.replace('setting_', '')
            setting = AISettings.query.get(setting_id)
            if setting:
                setting.setting_value = value
                setting.updated_by = current_user.id
                setting.updated_at = datetime.utcnow()
    
    db.session.commit()
    flash("AI settings updated successfully!", "success")
    return redirect(url_for("admin.ai_settings"))


# Content Management
@admin_bp.route("/content")
@login_required
@admin_required
def content_management():
    blog_posts = BlogPost.query.order_by(desc(BlogPost.created_at)).limit(5).all()
    faqs = FAQ.query.order_by(FAQ.order, FAQ.id).all()
    return render_template("admin/content_management.html", blog_posts=blog_posts, faqs=faqs)


@admin_bp.route("/content/faq/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_faq():
    if request.method == "POST":
        question = request.form.get('question')
        answer = request.form.get('answer')
        category = request.form.get('category', 'General')
        order = int(request.form.get('order', 0))
        
        faq = FAQ(
            question=question,
            answer=answer,
            category=category,
            order=order,
            created_by=current_user.id
        )
        db.session.add(faq)
        db.session.commit()
        
        flash("FAQ created successfully!", "success")
        return redirect(url_for("admin.content_management"))
    
    return render_template("admin/create_faq.html")


@admin_bp.route("/contact-messages")
@login_required
@admin_required
def contact_messages():
    page = request.args.get('page', 1, type=int)
    messages = ContactMessage.query.order_by(desc(ContactMessage.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template("admin/contact_messages.html", messages=messages)


@admin_bp.route("/contact-messages/<int:message_id>/mark-read", methods=["POST"])
@login_required
@admin_required
def mark_message_read(message_id):
    try:
        message = ContactMessage.query.get_or_404(message_id)
        message.is_read = True
        db.session.commit()
        flash("Message marked as read successfully!", "success")
        return redirect(url_for('admin.contact_messages'))
    except Exception as e:
        db.session.rollback()
        flash("Failed to mark message as read.", "error")
        return redirect(url_for('admin.contact_messages'))


@admin_bp.route("/contact-messages/<int:message_id>/view", methods=["GET"])
@login_required
@admin_required
def view_full_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    return jsonify({
        'success': True,
        'message': {
            'id': message.id,
            'name': message.name,
            'email': message.email,
            'subject': message.subject,
            'content': message.message,
            'created_at': message.created_at.strftime('%B %d, %Y at %I:%M %p'),
            'is_read': message.is_read
        }
    })


@admin_bp.route("/contact-messages/<int:message_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_contact_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash("Message deleted successfully!", "success")
    return redirect(url_for("admin.contact_messages"))


@admin_bp.route("/chats")
@login_required
@admin_required
def admin_chats():
    """Admin chat management"""
    from app.models import ChatRoom, ChatMessage
    
    # Get all chat rooms with recent activity
    chat_rooms = ChatRoom.query.order_by(desc(ChatRoom.last_message_at)).all()
    
    # Get chat statistics
    total_chats = ChatRoom.query.count()
    active_chats = ChatRoom.query.filter_by(is_active=True).count()
    total_messages = ChatMessage.query.count()
    
    return render_template(
        "admin/chats.html",
        chat_rooms=chat_rooms,
        total_chats=total_chats,
        active_chats=active_chats,
        total_messages=total_messages
    )


@admin_bp.route("/chats/<int:room_id>/close", methods=["POST"])
@login_required
@admin_required
def close_chat(room_id):
    """Close a chat room"""
    from app.models import ChatRoom
    
    room = ChatRoom.query.get_or_404(room_id)
    room.is_active = False
    db.session.commit()
    
    flash(f"Chat with {room.user.username} has been closed.", "success")
    return redirect(url_for("admin.admin_chats"))


@admin_bp.route("/surveillance-footage")
@login_required
@admin_required
def surveillance_footage():
    """Surveillance footage management"""
    from app.models import SurveillanceFootage
    
    page = request.args.get('page', 1, type=int)
    # Only show real footage (exclude test data)
    footage_list = SurveillanceFootage.query.filter(
        and_(
            ~SurveillanceFootage.video_path.like('%test%'),
            ~SurveillanceFootage.title.like('%Test%')
        )
    ).order_by(desc(SurveillanceFootage.created_at)).paginate(
        page=page, per_page=12, error_out=False
    )
    
    # AI Analysis Statistics (exclude test data)
    from app.models import LocationMatch
    total_matches = LocationMatch.query.join(SurveillanceFootage).filter(
        and_(
            ~SurveillanceFootage.video_path.like('%test%'),
            ~SurveillanceFootage.title.like('%Test%')
        )
    ).count()
    successful_detections = LocationMatch.query.join(SurveillanceFootage).filter(
        LocationMatch.person_found == True,
        ~SurveillanceFootage.video_path.like('%test%'),
        ~SurveillanceFootage.title.like('%Test%')
    ).count()
    
    return render_template(
        "admin/surveillance_footage.html", 
        footage_list=footage_list,
        total_matches=total_matches,
        successful_detections=successful_detections
    )


@admin_bp.route("/surveillance-footage/upload", methods=["GET", "POST"])
@login_required
@admin_required
def upload_surveillance_footage():
    """Upload new surveillance footage with automatic case matching"""
    from app.models import SurveillanceFootage
    from app.ai_location_matcher import ai_matcher
    import os
    import cv2
    from werkzeug.utils import secure_filename
    from flask import current_app
    
    if request.method == "POST":
        try:
            # Get form data
            title = request.form.get('title')
            description = request.form.get('description')
            location_name = request.form.get('location_name')
            location_address = request.form.get('location_address')
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')
            date_recorded = request.form.get('date_recorded')
            camera_type = request.form.get('camera_type')
            quality = request.form.get('quality')
            
            # Handle file upload
            if 'video_file' not in request.files:
                flash('No video file selected', 'error')
                return redirect(request.url)
            
            file = request.files['video_file']
            if file.filename == '':
                flash('No video file selected', 'error')
                return redirect(request.url)
            
            if file:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"surveillance_{timestamp}_{filename}"
                
                # Create surveillance directory
                surveillance_dir = os.path.join('app', 'static', 'surveillance')
                os.makedirs(surveillance_dir, exist_ok=True)
                
                file_path = os.path.join(surveillance_dir, filename)
                file.save(file_path)
                
                # Get video metadata
                cap = cv2.VideoCapture(file_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                duration = frame_count / fps if fps > 0 else 0
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                resolution = f"{width}x{height}"
                file_size = os.path.getsize(file_path)
                cap.release()
                
                # Create database entry
                footage = SurveillanceFootage(
                    title=title,
                    description=description,
                    location_name=location_name,
                    location_address=location_address,
                    latitude=float(latitude) if latitude else None,
                    longitude=float(longitude) if longitude else None,
                    video_path=f"surveillance/{filename}",
                    file_size=file_size,
                    duration=duration,
                    fps=fps,
                    resolution=resolution,
                    quality=quality,
                    date_recorded=datetime.strptime(date_recorded, '%Y-%m-%dT%H:%M') if date_recorded else None,
                    camera_type=camera_type,
                    uploaded_by=current_user.id
                )
                
                db.session.add(footage)
                db.session.commit()
                
                # AI: Automatically find matching cases and start analysis
                matches_found = ai_matcher.process_new_footage(footage.id)
                
                # Check for pending approval cases that can now be processed
                pending_cases = Case.query.filter_by(status='Pending Approval').all()
                newly_processable_cases = []
                
                for case in pending_cases:
                    if case.last_seen_location and location_name:
                        # Check if this footage location matches any pending case
                        if (location_name.lower() in case.last_seen_location.lower() or 
                            case.last_seen_location.lower() in location_name.lower()):
                            newly_processable_cases.append(case)
                
                # Notify case owners about available footage
                for case in newly_processable_cases:
                    notification = Notification(
                        user_id=case.user_id,
                        sender_id=current_user.id,
                        title=f"📹 New CCTV Footage Available: {case.person_name}",
                        message=f"New surveillance footage has been uploaded for location '{location_name}' which matches your case location '{case.last_seen_location}'. Your case can now be processed once approved by admin.",
                        type="info",
                        created_at=get_ist_now()
                    )
                    db.session.add(notification)
                
                db.session.commit()
                
                if matches_found > 0 and newly_processable_cases:
                    flash(f'Surveillance footage uploaded! Found {matches_found} case matches and {len(newly_processable_cases)} pending cases can now be processed.', 'success')
                elif matches_found > 0:
                    flash(f'Surveillance footage uploaded! AI found {matches_found} location matches and started analysis.', 'success')
                elif newly_processable_cases:
                    flash(f'Surveillance footage uploaded! {len(newly_processable_cases)} pending cases can now be processed with this footage.', 'success')
                else:
                    flash('Surveillance footage uploaded successfully!', 'success')
                
                return redirect(url_for('admin.surveillance_footage'))
                
        except Exception as e:
            flash(f'Error uploading footage: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template("admin/upload_surveillance_footage.html")


@admin_bp.route("/surveillance-footage/<int:footage_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_surveillance_footage(footage_id):
    """Delete surveillance footage"""
    from app.models import SurveillanceFootage
    import os
    
    footage = SurveillanceFootage.query.get_or_404(footage_id)
    
    try:
        # Delete file from filesystem
        file_path = os.path.join(current_app.root_path, 'static', footage.video_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        db.session.delete(footage)
        db.session.commit()
        
        flash('Surveillance footage deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting footage: {str(e)}', 'error')
    
    return redirect(url_for('admin.surveillance_footage'))


@admin_bp.route("/ai-analysis")
@login_required
@admin_required
def ai_analysis():
    """AI Analysis Results Dashboard"""
    from app.models import LocationMatch, PersonDetection, SurveillanceFootage
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    # Get location matches with filters
    query = LocationMatch.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    matches = query.order_by(desc(LocationMatch.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Statistics
    total_matches = LocationMatch.query.count()
    successful_matches = LocationMatch.query.filter_by(person_found=True).count()
    pending_matches = LocationMatch.query.filter_by(status='pending').count()
    processing_matches = LocationMatch.query.filter_by(status='processing').count()
    
    return render_template(
        "admin/ai_analysis.html",
        matches=matches,
        total_matches=total_matches,
        successful_matches=successful_matches,
        pending_matches=pending_matches,
        processing_matches=processing_matches,
        status_filter=status_filter
    )


@admin_bp.route("/ai-analysis/<int:match_id>")
@login_required
@admin_required
def ai_analysis_detail(match_id):
    """Detailed AI analysis results for a specific match"""
    from app.models import LocationMatch, PersonDetection
    
    match = LocationMatch.query.get_or_404(match_id)
    detections = PersonDetection.query.filter_by(location_match_id=match_id).order_by(PersonDetection.timestamp).all()
    
    return render_template(
        "admin/ai_analysis_detail.html",
        match=match,
        detections=detections
    )


@admin_bp.route("/ai-analysis/<int:match_id>/reprocess", methods=["POST"])
@login_required
@admin_required
def reprocess_ai_analysis(match_id):
    """Reprocess AI analysis for a specific match"""
    from app.models import LocationMatch
    from app.ai_location_matcher import ai_matcher
    
    match = LocationMatch.query.get_or_404(match_id)
    
    # Reset status and start reprocessing
    match.status = 'pending'
    match.person_found = False
    match.confidence_score = None
    match.detection_count = 0
    db.session.commit()
    
    # Start AI analysis
    success = ai_matcher.analyze_footage_for_person(match_id)
    
    if success:
        flash('AI analysis restarted successfully!', 'success')
    else:
        flash('Failed to restart AI analysis.', 'error')
    
    return redirect(url_for('admin.ai_analysis_detail', match_id=match_id))


@admin_bp.route("/location-insights")
@login_required
@admin_required
def location_insights():
    """Location intelligence dashboard for CCTV deployment"""
    from app.models import SurveillanceFootage, LocationMatch
    
    # Get location statistics
    location_stats = db.session.query(
        Case.last_seen_location,
        func.count(Case.id).label('case_count')
    ).filter(Case.last_seen_location.isnot(None)).group_by(Case.last_seen_location).order_by(desc('case_count')).all()
    
    # Get CCTV coverage data (exclude test data) - FIXED
    cctv_locations = SurveillanceFootage.query.filter(
        and_(
            ~SurveillanceFootage.video_path.like('%test%'),
            ~SurveillanceFootage.title.like('%Test%'),
            SurveillanceFootage.location_name.isnot(None)
        )
    ).with_entities(
        SurveillanceFootage.location_name,
        func.count(SurveillanceFootage.id).label('camera_count')
    ).group_by(SurveillanceFootage.location_name).all()
    
    # Debug print to verify correct count
    print(f"DEBUG: CCTV locations count = {len(cctv_locations)}")
    print(f"DEBUG: CCTV locations data = {cctv_locations}")
    
    # Calculate coverage gaps
    case_locations = set([stat[0].lower() for stat in location_stats])
    cctv_coverage = set([loc[0].lower() for loc in cctv_locations])
    coverage_gaps = case_locations - cctv_coverage
    
    return render_template(
        "admin/location_insights.html",
        location_stats=location_stats,
        cctv_locations=cctv_locations,
        coverage_gaps=coverage_gaps
    )


@admin_bp.route("/surveillance-footage/<int:footage_id>/details")
@login_required
@admin_required
def footage_details(footage_id):
    """Get footage details for modal display"""
    from app.models import SurveillanceFootage, LocationMatch
    
    footage = SurveillanceFootage.query.get_or_404(footage_id)
    matches = LocationMatch.query.filter_by(footage_id=footage_id).all()
    
    html_content = f"""
    <div class="row">
        <div class="col-md-6">
            <h6>Footage Information</h6>
            <table class="table table-sm">
                <tr><td><strong>Title:</strong></td><td>{footage.title}</td></tr>
                <tr><td><strong>Location:</strong></td><td>{footage.location_name}</td></tr>
                <tr><td><strong>Duration:</strong></td><td>{footage.formatted_duration}</td></tr>
                <tr><td><strong>Quality:</strong></td><td>{footage.quality}</td></tr>
                <tr><td><strong>File Size:</strong></td><td>{footage.formatted_file_size}</td></tr>
                <tr><td><strong>Uploaded:</strong></td><td>{footage.created_at.strftime('%d %b %Y %H:%M')}</td></tr>
            </table>
        </div>
        <div class="col-md-6">
            <h6>AI Analysis Results</h6>
            <p><strong>Total Matches:</strong> {len(matches)}</p>
            <p><strong>Successful Detections:</strong> {len([m for m in matches if m.person_found])}</p>
            <p><strong>Processing Status:</strong> {'Processed' if footage.is_processed else 'Pending'}</p>
        </div>
    </div>
    """
    
    return jsonify({'success': True, 'html': html_content})


@admin_bp.route("/ai-analysis/bulk-start", methods=["POST"])
@login_required
@admin_required
def bulk_start_analysis():
    """Start bulk AI analysis for pending matches"""
    try:
        from app.models import LocationMatch
        from app.ai_location_matcher import ai_matcher
        
        pending_matches = LocationMatch.query.filter_by(status='pending').all()
        
        for match in pending_matches:
            # Start analysis in background
            try:
                ai_matcher.analyze_footage_for_person(match.id)
            except Exception as e:
                logger.error(f"Error starting analysis for match {match.id}: {str(e)}")
        
        return jsonify({
            'success': True, 
            'count': len(pending_matches),
            'message': f'Started analysis for {len(pending_matches)} matches'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route("/ai-analysis/<int:match_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_analysis_match(match_id):
    """Delete an AI analysis match"""
    try:
        from app.models import LocationMatch
        
        match = LocationMatch.query.get_or_404(match_id)
        db.session.delete(match)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Match deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route("/detection/<int:detection_id>/<action>", methods=["POST"])
@login_required
@admin_required
def verify_detection(detection_id, action):
    """Verify or reject a detection"""
    try:
        from app.models import PersonDetection
        
        detection = PersonDetection.query.get_or_404(detection_id)
        
        if action == 'verify':
            detection.verified = True
            detection.verified_by = current_user.id
            message = 'Detection verified successfully'
        elif action == 'reject':
            detection.verified = False
            detection.verified_by = current_user.id
            message = 'Detection rejected successfully'
        else:
            return jsonify({'success': False, 'error': 'Invalid action'})
        
        db.session.commit()
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route("/cases/<int:case_id>/review")
@login_required
@admin_required
def case_review(case_id):
    """Detailed case review with nearby footage and approval controls"""
    from app.ai_location_matcher import ai_matcher
    
    case = Case.query.get_or_404(case_id)
    
    # Find nearby surveillance footage
    nearby_footage = ai_matcher.find_nearby_footage(case.last_seen_location)
    
    # Get existing location matches
    location_matches = LocationMatch.query.filter_by(case_id=case_id).all()
    
    # Check if case can be approved (has nearby footage)
    can_approve = len(nearby_footage) > 0
    
    # Check if case can be approved (has nearby footage)
    can_approve = len(nearby_footage) > 0
    
    return render_template(
        "admin/case_review.html",
        case=case,
        nearby_footage=nearby_footage,
        location_matches=location_matches,
        can_approve=can_approve
    )


@admin_bp.route("/analyze-footage/<int:case_id>/<int:footage_id>", methods=["POST"])
@login_required
@admin_required
def analyze_footage(case_id, footage_id):
    """Manually assign case to specific footage for AI analysis"""
    try:
        from app.ai_location_matcher import ai_matcher
        
        case = Case.query.get_or_404(case_id)
        footage = SurveillanceFootage.query.get_or_404(footage_id)
        
        # Check if match already exists
        existing_match = LocationMatch.query.filter_by(
            case_id=case_id,
            footage_id=footage_id
        ).first()
        
        if not existing_match:
            # Create new location match with manual assignment
            location_match = LocationMatch(
                case_id=case_id,
                footage_id=footage_id,
                match_score=0.9,  # High score for admin-selected footage
                match_type='manual',
                status='pending'
            )
            db.session.add(location_match)
            db.session.commit()
            
            # Log the manual assignment
            log = SystemLog(
                case_id=case_id,
                user_id=current_user.id,
                action='manual_footage_assignment',
                details=f'Admin manually assigned case {case.person_name} to footage {footage.title}',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            # Start AI analysis
            success = ai_matcher.analyze_footage_for_person(location_match.id)
            
            if success:
                return jsonify({
                    'success': True, 
                    'message': f'Manual analysis started for {footage.title}'
                })
            else:
                return jsonify({
                    'success': False, 
                    'error': 'Failed to start AI analysis'
                })
        else:
            # Restart analysis for existing match
            existing_match.status = 'pending'
            existing_match.match_type = 'manual'
            db.session.commit()
            
            success = ai_matcher.analyze_footage_for_person(existing_match.id)
            
            if success:
                return jsonify({
                    'success': True, 
                    'message': 'Analysis restarted for existing match'
                })
            else:
                return jsonify({
                    'success': False, 
                    'error': 'Failed to restart analysis'
                })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route("/cases/<int:case_id>/start-analysis", methods=["POST"])
@login_required
@admin_required
def start_case_analysis(case_id):
    """Start AI analysis for all nearby footage after approval"""
    try:
        from app.ai_location_matcher import ai_matcher
        
        case = Case.query.get_or_404(case_id)
        
        # Check if case is approved
        if case.status not in ['Approved', 'Processing']:
            return jsonify({
                'success': False, 
                'error': 'Case must be approved before starting analysis'
            })
        
        # Find or create location matches for all nearby footage
        matches_created = ai_matcher.process_new_case(case_id)
        
        if matches_created == 0:
            return jsonify({
                'success': False, 
                'error': 'No suitable footage found for this location. Please upload relevant CCTV footage.'
            })
        
        # Update case status
        case.status = 'Processing'
        db.session.commit()
        
        # Start analysis for all pending matches
        pending_matches = LocationMatch.query.filter_by(
            case_id=case_id, 
            status='pending'
        ).all()
        
        analysis_started = 0
        for match in pending_matches:
            if ai_matcher.analyze_footage_for_person(match.id):
                analysis_started += 1
        
        # Notify user about analysis start
        from app.models import Notification
        notification = Notification(
            user_id=case.user_id,
            sender_id=current_user.id,
            title=f"🔍 AI Analysis Started: {case.person_name}",
            message=f"AI analysis has begun for your case. We're analyzing {analysis_started} CCTV footage files from the area. You'll be notified when results are available.",
            type="info",
            created_at=get_ist_now()
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Started analysis for {analysis_started} footage matches'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route("/surveillance-footage/bulk-upload", methods=["GET", "POST"])
@login_required
@admin_required
def bulk_upload_footage():
    """Bulk upload multiple CCTV footage files"""
    if request.method == "POST":
        try:
            uploaded_files = request.files.getlist('video_files')
            location_name = request.form.get('location_name')
            camera_type = request.form.get('camera_type', 'CCTV')
            quality = request.form.get('quality', 'HD')
            
            uploaded_count = 0
            
            for file in uploaded_files:
                if file and file.filename:
                    # Process each file
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"bulk_{timestamp}_{filename}"
                    
                    # Save file
                    surveillance_dir = os.path.join('app', 'static', 'surveillance')
                    os.makedirs(surveillance_dir, exist_ok=True)
                    file_path = os.path.join(surveillance_dir, filename)
                    file.save(file_path)
                    
                    # Get video metadata
                    import cv2
                    cap = cv2.VideoCapture(file_path)
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    duration = frame_count / fps if fps > 0 else 0
                    file_size = os.path.getsize(file_path)
                    cap.release()
                    
                    # Create database entry
                    footage = SurveillanceFootage(
                        title=f"{location_name} - {file.filename}",
                        location_name=location_name,
                        video_path=f"surveillance/{filename}",
                        file_size=file_size,
                        duration=duration,
                        fps=fps,
                        quality=quality,
                        camera_type=camera_type,
                        uploaded_by=current_user.id
                    )
                    
                    db.session.add(footage)
                    uploaded_count += 1
            
            db.session.commit()
            
            # Auto-match with existing cases
            from app.ai_location_matcher import ai_matcher
            total_matches = 0
            
            for footage in SurveillanceFootage.query.filter_by(location_name=location_name).all():
                matches = ai_matcher.process_new_footage(footage.id)
                total_matches += matches
            
            flash(f'Successfully uploaded {uploaded_count} files and created {total_matches} AI matches', 'success')
            return redirect(url_for('admin.surveillance_footage'))
            
        except Exception as e:
            flash(f'Error during bulk upload: {str(e)}', 'error')
    
    return render_template("admin/bulk_upload_footage.html")


@admin_bp.route("/footage-analysis-results/<int:case_id>")
@login_required
@admin_required
def footage_analysis_results(case_id):
    """View detailed analysis results for a case"""
    case = Case.query.get_or_404(case_id)
    
    # Get all matches and detections
    matches_with_detections = []
    location_matches = LocationMatch.query.filter_by(case_id=case_id).all()
    
    for match in location_matches:
        detections = PersonDetection.query.filter_by(location_match_id=match.id).all()
        matches_with_detections.append({
            'match': match,
            'detections': detections,
            'footage': match.footage
        })
    
    return render_template(
        "admin/footage_analysis_results.html",
        case=case,
        matches_with_detections=matches_with_detections
    )


@admin_bp.route("/detection/<int:detection_id>/note", methods=["POST"])
@login_required
@admin_required
def add_detection_note(detection_id):
    """Add note to a detection"""
    try:
        from app.models import PersonDetection
        
        detection = PersonDetection.query.get_or_404(detection_id)
        data = request.get_json()
        note = data.get('note', '').strip()
        
        if note:
            detection.notes = note
            db.session.commit()
            return jsonify({'success': True, 'message': 'Note added successfully'})
        else:
            return jsonify({'success': False, 'error': 'Note cannot be empty'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route("/cases/<int:case_id>/export-results")
@login_required
@admin_required
def export_case_results(case_id):
    """Export case analysis results"""
    try:
        case = Case.query.get_or_404(case_id)
        
        # Get all matches and detections
        location_matches = LocationMatch.query.filter_by(case_id=case_id).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # CSV headers
        writer.writerow([
            'Case ID', 'Person Name', 'Footage Title', 'Location', 
            'Match Score', 'Detection Time', 'Confidence Score', 
            'Face Score', 'Clothing Score', 'Method', 'Verified', 'Notes'
        ])
        
        for match in location_matches:
            detections = PersonDetection.query.filter_by(location_match_id=match.id).all()
            
            if detections:
                for detection in detections:
                    writer.writerow([
                        case.id,
                        case.person_name,
                        match.footage.title,
                        match.footage.location_name,
                        f"{match.match_score:.3f}",
                        detection.formatted_timestamp,
                        f"{detection.confidence_score:.3f}",
                        f"{detection.face_match_score:.3f}" if detection.face_match_score else '',
                        f"{detection.clothing_match_score:.3f}" if detection.clothing_match_score else '',
                        detection.analysis_method or '',
                        'Yes' if detection.verified else 'No',
                        detection.notes or ''
                    ])
            else:
                writer.writerow([
                    case.id,
                    case.person_name,
                    match.footage.title,
                    match.footage.location_name,
                    f"{match.match_score:.3f}",
                    'No detections',
                    '', '', '', '', '', ''
                ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'case_{case_id}_analysis_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        flash(f'Error exporting results: {str(e)}', 'error')
        return redirect(url_for('admin.case_review', case_id=case_id))


@admin_bp.route("/system-status")
@login_required
@admin_required
def system_status():
    """System status and health check"""
    try:
        # Database status
        db_status = 'Connected'
        try:
            db.session.execute('SELECT 1')
        except:
            db_status = 'Error'
        
        # Redis status
        redis_status = 'Not Available'
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            redis_status = 'Connected'
        except:
            pass
        
        # AI system status
        ai_status = 'Available'
        try:
            from app.ai_location_matcher import ai_matcher
            if ai_matcher.face_cascade.empty():
                ai_status = 'Error - Face cascade not loaded'
        except Exception as e:
            ai_status = f'Error - {str(e)}'
        
        # System statistics (exclude test data)
        stats = {
            'total_cases': Case.query.count(),
            'pending_cases': Case.query.filter_by(status='Pending Approval').count(),
            'active_cases': Case.query.filter(Case.status.in_(['Queued', 'Processing', 'Active'])).count(),
            'total_footage': SurveillanceFootage.query.filter(
                ~SurveillanceFootage.video_path.like('%test%')
            ).count(),
            'total_matches': LocationMatch.query.join(SurveillanceFootage).filter(
                ~SurveillanceFootage.video_path.like('%test%')
            ).count(),
            'processing_matches': LocationMatch.query.join(SurveillanceFootage).filter(
                LocationMatch.status == 'processing',
                ~SurveillanceFootage.video_path.like('%test%')
            ).count(),
            'total_detections': PersonDetection.query.join(LocationMatch).join(SurveillanceFootage).filter(
                ~SurveillanceFootage.video_path.like('%test%')
            ).count(),
            'verified_detections': PersonDetection.query.join(LocationMatch).join(SurveillanceFootage).filter(
                PersonDetection.verified == True,
                ~SurveillanceFootage.video_path.like('%test%')
            ).count()
        }
        
        return render_template(
            "admin/system_status.html",
            db_status=db_status,
            redis_status=redis_status,
            ai_status=ai_status,
            stats=stats
        )
        
    except Exception as e:
        flash(f'Error loading system status: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route("/system-report")
@login_required
@admin_required
def system_report():
    """Generate comprehensive system report"""
    try:
        # Generate detailed system report
        report_data = {
            'generated_at': datetime.now(),
            'total_users': User.query.count(),
            'active_users': User.query.filter_by(is_active=True).count(),
            'admin_users': User.query.filter_by(is_admin=True).count(),
            'total_cases': Case.query.count(),
            'pending_cases': Case.query.filter_by(status='Pending Approval').count(),
            'completed_cases': Case.query.filter_by(status='Completed').count(),
            'total_footage': SurveillanceFootage.query.count(),
            'total_matches': LocationMatch.query.count(),
            'successful_matches': LocationMatch.query.filter_by(person_found=True).count(),
            'total_detections': PersonDetection.query.count(),
            'verified_detections': PersonDetection.query.filter_by(verified=True).count()
        }
        
        return render_template("admin/system_report.html", report=report_data)
        
    except Exception as e:
        flash(f'Error generating system report: {str(e)}', 'error')
        return redirect(url_for('admin.system_status'))


@admin_bp.route("/optimize-database", methods=["POST"])
@login_required
@admin_required
def optimize_database():
    """Optimize database performance"""
    try:
        # Perform database optimization tasks
        optimizations_performed = []
        
        # Clean up old logs
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        old_logs = SystemLog.query.filter(SystemLog.timestamp < thirty_days_ago).count()
        SystemLog.query.filter(SystemLog.timestamp < thirty_days_ago).delete()
        optimizations_performed.append(f"Cleaned {old_logs} old system logs")
        
        # Clean up old notifications
        old_notifications = db.session.query(Notification).filter(
            Notification.created_at < thirty_days_ago,
            Notification.is_read == True
        ).count()
        db.session.query(Notification).filter(
            Notification.created_at < thirty_days_ago,
            Notification.is_read == True
        ).delete()
        optimizations_performed.append(f"Cleaned {old_notifications} old notifications")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Database optimization completed',
            'optimizations': optimizations_performed
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route("/test-ai-system", methods=["POST"])
@login_required
@admin_required
def test_ai_system():
    """Test AI system functionality"""
    try:
        test_results = []
        
        # Test face recognition
        try:
            import face_recognition
            import numpy as np
            test_image = np.zeros((100, 100, 3), dtype=np.uint8)
            face_locations = face_recognition.face_locations(test_image)
            test_results.append("✅ Face recognition library working")
        except Exception as e:
            test_results.append(f"❌ Face recognition error: {str(e)}")
        
        # Test OpenCV
        try:
            import cv2
            test_results.append(f"✅ OpenCV version: {cv2.__version__}")
        except Exception as e:
            test_results.append(f"❌ OpenCV error: {str(e)}")
        
        # Test AI matcher
        try:
            from app.ai_location_matcher import ai_matcher
            test_results.append("✅ AI location matcher loaded")
        except Exception as e:
            test_results.append(f"❌ AI matcher error: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': 'AI system test completed',
            'results': test_results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route("/clear-cache", methods=["POST"])
@login_required
@admin_required
def clear_cache():
    """Clear system cache"""
    try:
        # Clear Redis cache if available
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.flushdb()
            cache_cleared = True
        except:
            cache_cleared = False
        
        # Clear temporary files
        import os
        import shutil
        temp_dirs = ['app/static/temp', 'app/static/cache']
        files_cleared = 0
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                for filename in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                            files_cleared += 1
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                            files_cleared += 1
                    except:
                        pass
        
        return jsonify({
            'success': True,
            'message': f'Cache cleared successfully. {files_cleared} files removed.',
            'redis_cleared': cache_cleared
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@admin_bp.route("/generate-system-report", methods=["POST"])
@login_required
@admin_required
def generate_system_report():
    """Generate comprehensive system report"""
    try:
        # Generate report data
        report_data = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'system_stats': {
                'total_users': User.query.count(),
                'active_users': User.query.filter_by(is_active=True).count(),
                'admin_users': User.query.filter_by(is_admin=True).count(),
                'total_cases': Case.query.count(),
                'pending_cases': Case.query.filter_by(status='Pending Approval').count(),
                'approved_cases': Case.query.filter_by(status='Approved').count(),
                'processing_cases': Case.query.filter_by(status='Processing').count(),
                'completed_cases': Case.query.filter_by(status='Completed').count(),
                'real_footage': SurveillanceFootage.query.filter(
                    ~SurveillanceFootage.video_path.like('%test%')
                ).count(),
                'location_matches': LocationMatch.query.count(),
                'successful_detections': LocationMatch.query.filter_by(person_found=True).count(),
                'total_detections': PersonDetection.query.count(),
                'verified_detections': PersonDetection.query.filter_by(verified=True).count()
            },
            'performance_metrics': {
                'avg_processing_time': 0,
                'success_rate': 0,
                'verification_rate': 0
            }
        }
        
        # Calculate performance metrics
        total_matches = report_data['system_stats']['location_matches']
        successful = report_data['system_stats']['successful_detections']
        total_detections = report_data['system_stats']['total_detections']
        verified = report_data['system_stats']['verified_detections']
        
        if total_matches > 0:
            report_data['performance_metrics']['success_rate'] = round((successful / total_matches) * 100, 2)
        
        if total_detections > 0:
            report_data['performance_metrics']['verification_rate'] = round((verified / total_detections) * 100, 2)
        
        return jsonify({
            'success': True,
            'message': 'System report generated successfully',
            'report': report_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})



