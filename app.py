from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from models import db, User, Appointment, Service, Testimonial, GalleryImage, DoctorProfile

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key_change_me_in_prod')
database_url = os.environ.get('DATABASE_URL', 'sqlite:///clinic.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure upload directory exists
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'admin_login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    with app.app_context():
        db.create_all()
        # Create default admin if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password_hash=generate_password_hash('admin123'))
            db.session.add(admin)
            
            # Create default Doctor Profile if not exists
            profile = DoctorProfile(
                name="Dr. Your Name",
                title="Cosmetic & Implant Dentistry",
                description="With over 10 years of dedicated practice, Dr. Your Name combines advanced clinical expertise with a compassionate approach to patient care. Specializing in cosmetic and implant dentistry, they are committed to creating healthy, confident smiles that transform lives.",
                experience_years=10,
                patients_count="5K+",
                treatments_count="2K+"
            )
            db.session.add(profile)
            
            # Create default Services
            default_services = [
                Service(name="Teeth Cleaning", description="Professional deep cleaning for healthier, brighter teeth and optimal gum health.", icon="✨", order=1),
                Service(name="Dental Implants", description="Permanent, natural-looking replacements for missing teeth that last a lifetime.", icon="🦷", order=2),
                Service(name="Teeth Whitening", description="Advanced laser whitening treatments for a noticeably brighter, confident smile.", icon="😁", order=3),
                Service(name="Braces & Aligners", description="Straighten teeth comfortably with clear aligners and modern orthodontic solutions.", icon="⚡", order=4)
            ]
            for s in default_services:
                db.session.add(s)
                
            # Create default Testimonials
            default_testimonials = [
                Testimonial(patient_name="Rahul S.", review_text="Excellent dental care and very friendly staff. I was nervous at first but they made me feel so comfortable throughout the entire treatment.", stars=5, tag="Dental Implants Patient", avatar_emoji="👨"),
                Testimonial(patient_name="Priya M.", review_text="The clinic is modern and the treatment was completely painless. My smile looks absolutely amazing now — best investment I've ever made!", stars=5, tag="Teeth Whitening Patient", avatar_emoji="👩"),
                Testimonial(patient_name="Arjun T.", review_text="I've been coming here for 3 years and the level of professionalism is unmatched. The equipment is state-of-the-art and the team is incredibly skilled.", stars=5, tag="Regular Patient", avatar_emoji="👨"),
                Testimonial(patient_name="Ananya K.", review_text="Got clear aligners from here and the transformation is unbelievable. The doctor was patient, explained everything clearly and results exceeded my expectations.", stars=5, tag="Braces & Aligners Patient", avatar_emoji="👩"),
                Testimonial(patient_name="Vikram R.", review_text="Best dental experience I've ever had. Clean, modern, and incredibly caring staff. I used to dread going to the dentist — not anymore!", stars=5, tag="Teeth Cleaning Patient", avatar_emoji="👨")
            ]
            for t in default_testimonials:
                db.session.add(t)

            db.session.commit()

# Initialize database automatically so Gunicorn creates tables on startup
init_db()

# --- PUBLIC ROUTES ---
@app.route('/')
def index():
    services = Service.query.order_by(Service.order).all()
    testimonials = Testimonial.query.all()
    doctor = DoctorProfile.query.first()
    gallery = GalleryImage.query.all()
    return render_template('index.html', services=services, testimonials=testimonials, doctor=doctor, gallery=gallery)

@app.route('/api/book', methods=['POST'])
def api_book():
    data = request.json
    if not data or not data.get('name') or not data.get('phone') or not data.get('service'):
        return jsonify({'error': 'Missing required fields'}), 400
        
    appointment = Appointment(
        name=data['name'],
        phone=data['phone'],
        service=data['service']
    )
    db.session.add(appointment)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Appointment requested successfully!'})

# --- ADMIN ROUTES ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
            
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

@app.route('/admin')
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    stats = {
        'appointments': Appointment.query.count(),
        'services': Service.query.count(),
        'testimonials': Testimonial.query.count(),
        'images': GalleryImage.query.count()
    }
    recent_appointments = Appointment.query.order_by(Appointment.date_requested.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats, appointments=recent_appointments)

@app.route('/admin/appointments')
@login_required
def admin_appointments():
    appointments = Appointment.query.order_by(Appointment.date_requested.desc()).all()
    return render_template('admin/appointments.html', appointments=appointments)

@app.route('/admin/appointments/status/<int:id>', methods=['POST'])
@login_required
def admin_appointment_status(id):
    app = Appointment.query.get_or_404(id)
    app.status = request.form.get('status', 'Pending')
    db.session.commit()
    flash(f'Appointment status updated to {app.status}', 'success')
    return redirect(url_for('admin_appointments'))

@app.route('/admin/appointments/delete/<int:id>', methods=['POST'])
@login_required
def admin_appointment_delete(id):
    app = Appointment.query.get_or_404(id)
    db.session.delete(app)
    db.session.commit()
    flash('Appointment deleted', 'success')
    return redirect(url_for('admin_appointments'))

@app.route('/admin/services', methods=['GET', 'POST'])
@login_required
def admin_services():
    if request.method == 'POST':
        service = Service(
            name=request.form.get('name'),
            icon=request.form.get('icon'),
            description=request.form.get('description'),
            order=int(request.form.get('order', 0))
        )
        db.session.add(service)
        db.session.commit()
        flash('Service added successfully', 'success')
        return redirect(url_for('admin_services'))
        
    services = Service.query.order_by(Service.order).all()
    return render_template('admin/services.html', services=services)

@app.route('/admin/services/delete/<int:id>', methods=['POST'])
@login_required
def admin_service_delete(id):
    service = Service.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    flash('Service deleted', 'success')
    return redirect(url_for('admin_services'))

@app.route('/admin/testimonials', methods=['GET', 'POST'])
@login_required
def admin_testimonials():
    if request.method == 'POST':
        test = Testimonial(
            patient_name=request.form.get('patient_name'),
            avatar_emoji=request.form.get('avatar_emoji'),
            tag=request.form.get('tag'),
            stars=int(request.form.get('stars', 5)),
            review_text=request.form.get('review_text')
        )
        db.session.add(test)
        db.session.commit()
        flash('Testimonial added successfully', 'success')
        return redirect(url_for('admin_testimonials'))
        
    testimonials = Testimonial.query.all()
    return render_template('admin/testimonials.html', testimonials=testimonials)

@app.route('/admin/testimonials/delete/<int:id>', methods=['POST'])
@login_required
def admin_testimonial_delete(id):
    test = Testimonial.query.get_or_404(id)
    db.session.delete(test)
    db.session.commit()
    flash('Testimonial deleted', 'success')
    return redirect(url_for('admin_testimonials'))

@app.route('/admin/gallery', methods=['GET', 'POST'])
@login_required
def admin_gallery():
    from werkzeug.utils import secure_filename
    if request.method == 'POST':
        title = request.form.get('title')
        is_ba = request.form.get('is_before_after') == 'true'
        file = request.files.get('image')
        
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            img = GalleryImage(
                title=title,
                image_path=f'static/uploads/{filename}',
                is_before_after=is_ba
            )
            db.session.add(img)
            db.session.commit()
            flash('Image uploaded successfully', 'success')
        else:
            flash('No image selected', 'error')
            
        return redirect(url_for('admin_gallery'))
        
    gallery = GalleryImage.query.all()
    return render_template('admin/gallery.html', gallery=gallery)

@app.route('/admin/gallery/delete/<int:id>', methods=['POST'])
@login_required
def admin_gallery_delete(id):
    img = GalleryImage.query.get_or_404(id)
    # optional: delete file from disk here
    db.session.delete(img)
    db.session.commit()
    flash('Image deleted', 'success')
    return redirect(url_for('admin_gallery'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    doctor = DoctorProfile.query.first()
    if request.method == 'POST':
        doctor.name = request.form.get('name')
        doctor.title = request.form.get('title')
        doctor.description = request.form.get('description')
        doctor.experience_years = int(request.form.get('experience_years', 0))
        doctor.patients_count = request.form.get('patients_count')
        doctor.treatments_count = request.form.get('treatments_count')
        db.session.commit()
        flash('Doctor profile updated successfully', 'success')
        return redirect(url_for('admin_settings'))
        
    return render_template('admin/settings.html', doctor=doctor)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
