# Case Approval Workflow Implementation

## Overview
This document describes the complete implementation of the case approval workflow where admin must review and approve cases before AI processing begins.

## Key Features Implemented

### 1. Case Status Flow
- **Pending Approval** (Default): New cases wait for admin review
- **Approved**: Admin has approved the case, ready for AI processing  
- **Processing**: AI analysis is actively running
- **Rejected**: Admin rejected the case, needs revision
- **Completed**: AI analysis finished

### 2. Admin Approval Process

#### Case Review Interface (`/admin/cases/{id}/review`)
- **Location-based Footage Check**: Admin can see available CCTV footage for the case location
- **Approval Controls**: 
  - ✅ **Approve**: Only if relevant footage is available
  - ❌ **Reject**: With reason for rejection
- **Manual Footage Assignment**: Admin can manually assign specific footage to cases
- **Bulk Analysis**: Start AI analysis for all relevant footage

#### Approval Logic
```python
# Admin can only approve if footage is available
nearby_footage = ai_matcher.find_nearby_footage(case.last_seen_location)
if not nearby_footage:
    # Show warning: "No footage available for this location"
    # Redirect to upload footage
else:
    # Allow approval and start AI processing
```

### 3. Location-Based Footage Matching

#### AI Location Matcher (`ai_location_matcher.py`)
```python
def find_nearby_footage(location_name):
    """Find surveillance footage near a given location"""
    # Smart location matching:
    # - Exact location name match
    # - Partial location name match  
    # - Word-based matching
    # - GPS distance matching (if available)
```

#### Automatic Matching
- When admin uploads new footage, system automatically:
  1. Finds cases with matching locations
  2. Notifies case owners about available footage
  3. Creates location matches for approved cases
  4. Starts AI analysis if cases are already approved

### 4. User Experience

#### Dashboard Status Display
- **Pending Approval**: ⏳ "Awaiting admin approval"
- **Approved**: ✅ "Ready for AI processing" 
- **Processing**: 🔄 "AI analysis in progress"
- **Rejected**: ❌ "Needs revision"

#### Notifications
Users receive notifications when:
- Case is approved by admin
- Case is rejected (with reason)
- New footage becomes available for their location
- AI analysis starts/completes

### 5. Admin Workflow

#### Step 1: Review New Cases
```
/admin/cases/{id}/review
- View case details and photos
- Check available footage for location
- Approve or reject with reason
```

#### Step 2: Upload Relevant Footage (if needed)
```
/admin/surveillance-footage/upload
- Upload CCTV footage with location metadata
- System automatically matches with pending cases
- Notifies case owners about new footage
```

#### Step 3: Start AI Analysis
```
- Manual: Assign specific footage to cases
- Automatic: Bulk analysis for all approved cases
- Monitor: Track analysis progress and results
```

### 6. Technical Implementation

#### Database Changes
```sql
-- Case status now defaults to 'Pending Approval'
ALTER TABLE case ALTER COLUMN status SET DEFAULT 'Pending Approval';

-- Location matches track manual assignments
ALTER TABLE location_match ADD COLUMN match_type VARCHAR(20) DEFAULT 'location';
-- Values: 'location', 'proximity', 'exact', 'manual'
```

#### Key Routes Added/Modified
- `POST /admin/cases/{id}/approve` - Approve case
- `POST /admin/cases/{id}/reject` - Reject case with reason
- `GET /admin/cases/{id}/review` - Case review interface
- `POST /admin/analyze-footage/{case_id}/{footage_id}` - Manual assignment
- `POST /admin/cases/{id}/start-analysis` - Bulk analysis

#### AI Processing Flow
```python
# Old flow: Immediate processing
case.status = "Queued"
start_ai_processing(case_id)

# New flow: Admin approval required
case.status = "Pending Approval"
# Wait for admin approval...
# After approval:
case.status = "Approved" 
if has_nearby_footage:
    case.status = "Processing"
    start_ai_processing(case_id)
```

### 7. Notification System

#### Admin Notifications
- New case submitted (pending approval)
- Case requires footage upload
- Analysis results available

#### User Notifications  
- Case approved/rejected
- New footage available for location
- AI analysis started/completed
- Detection results found

### 8. Error Handling

#### No Footage Available
```python
if not nearby_footage:
    flash("⚠️ No CCTV footage available for location. Please upload relevant footage first.")
    return redirect(url_for('admin.upload_surveillance_footage'))
```

#### Failed AI Analysis
- Automatic retry mechanism
- Admin notification of failures
- Manual reprocessing option

### 9. Security & Validation

#### Access Control
- Only admins can approve/reject cases
- Case owners can only view their own cases
- Proper CSRF protection on all forms

#### Input Validation
- Location name sanitization
- File type validation for footage uploads
- Rejection reason required for case rejection

### 10. Performance Optimizations

#### Background Processing
- AI analysis runs in background threads
- Progress tracking and status updates
- Automatic cleanup of old analysis data

#### Database Optimization
- Indexed queries for location matching
- Pagination for large datasets
- Efficient status filtering

## Usage Examples

### For Users
1. **Submit Case**: Upload photos and details → Status: "Pending Approval"
2. **Wait for Review**: Admin reviews case and checks footage availability
3. **Get Notification**: "Case approved" or "Case rejected with reason"
4. **Track Progress**: Dashboard shows "Processing" → "AI analysis in progress"
5. **View Results**: Receive notifications when detections are found

### For Admins
1. **Review Cases**: Check pending approval queue
2. **Verify Footage**: Ensure relevant CCTV footage exists for location
3. **Approve/Reject**: Make decision based on case quality and footage availability
4. **Upload Footage**: Add missing surveillance footage if needed
5. **Monitor Analysis**: Track AI processing and verify results

## Benefits

### Quality Control
- Admin review ensures case quality before processing
- Prevents wasted AI resources on poor quality submissions
- Ensures relevant footage is available before analysis

### Better User Experience  
- Clear status tracking and notifications
- Realistic expectations about processing time
- Feedback on case quality and requirements

### Efficient Resource Usage
- AI only processes cases with available footage
- Manual assignment for edge cases
- Bulk processing for efficiency

### Scalability
- Admin can prioritize high-quality cases
- Automatic matching reduces manual work
- Background processing handles load

## Testing

Run the test script to verify implementation:
```bash
python test_approval_workflow.py
```

The test validates:
- ✅ Case status transitions
- ✅ AI location matching
- ✅ Admin approval process  
- ✅ Notification system
- ✅ Database integrity

## Conclusion

This implementation provides a complete case approval workflow that ensures:
1. **Quality Control**: Admin reviews all cases before AI processing
2. **Resource Efficiency**: Only process cases with available footage
3. **User Transparency**: Clear status updates and notifications
4. **Admin Control**: Manual override and bulk processing options
5. **Scalability**: Automated matching and background processing

The system now properly handles the workflow where admin acceptance is required, footage availability is checked, and users are kept informed throughout the process.