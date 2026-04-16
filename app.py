from flask import Flask, render_template, request, redirect, flash
import pyodbc
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

try:
    conn = pyodbc.connect(
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        r'SERVER=localhost\SQLEXPRESS;'
        r'DATABASE=StudentDB;'
        r'Trusted_Connection=yes;'
    )
    cursor = conn.cursor()
except pyodbc.Error as e:
    print(f"Database connection error: {e}")

def validate_form_data(name, email, course, phone, address, gender, dob):
    """Validate all form fields - All fields are mandatory"""
    errors = []
    
    # Name validation
    if not name or len(name.strip()) < 2:
        errors.append('Name must be at least 2 characters long.')
    elif len(name) > 100:
        errors.append('Name cannot exceed 100 characters.')
    elif not re.match(r"^[a-zA-Z\s]*$", name):
        errors.append('Name can only contain letters and spaces.')
    
    # Email validation
    if not email:
        errors.append('Email is required.')
    else:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors.append('Please enter a valid email address.')
    
    # Course validation
    if not course:
        errors.append('Course is required.')
    else:
        valid_courses = ['Computer Science', 'Information Technology', 'Business Administration', 'Engineering', 'Liberal Arts']
        if course not in valid_courses:
            errors.append('Invalid course selected.')
    
    # Phone validation - MANDATORY
    if not phone:
        errors.append('Phone number is required.')
    else:
        phone_clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if not re.match(r'^\+?1?\d{9,15}$', phone_clean):
            errors.append('Please enter a valid phone number.')
    
    # Gender validation - MANDATORY
    if not gender:
        errors.append('Gender is required.')
    else:
        valid_genders = ['Male', 'Female', 'Other']
        if gender not in valid_genders:
            errors.append('Invalid gender selected.')
    
    # DOB validation - MANDATORY
    if not dob:
        errors.append('Date of Birth is required.')
    else:
        try:
            dob_date = datetime.strptime(dob, '%Y-%m-%d')
            # Check if date is not in the future
            if dob_date > datetime.now():
                errors.append('Date of birth cannot be in the future.')
            # Check if person is at least 16 years old
            age = (datetime.now() - dob_date).days // 365
            if age < 16:
                errors.append('Student must be at least 16 years old.')
        except ValueError:
            errors.append('Invalid date format for Date of Birth.')
    
    # Address validation - MANDATORY
    if not address:
        errors.append('Address is required.')
    elif len(address) > 500:
        errors.append('Address cannot exceed 500 characters.')
    
    return errors

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        course = request.form.get('course', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        gender = request.form.get('gender', '').strip()
        dob = request.form.get('dob', '').strip()

        # Validate all fields
        errors = validate_form_data(name, email, course, phone, address, gender, dob)
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect('/')

        cursor.execute("""
            INSERT INTO Students (name, email, course, phone, address, gender, dob)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, email, course, phone, address, gender, dob))
        
        conn.commit()
        flash(f'Student {name} added successfully!', 'success')
        return redirect('/view')

    except pyodbc.Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect('/')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect('/')

@app.route('/view')
def view():
    try:
        cursor.execute("SELECT id, name, email, course, phone, address, gender, dob FROM Students ORDER BY id DESC")
        students = cursor.fetchall()
        return render_template('view.html', students=students)
    except pyodbc.Error as e:
        flash(f'Error fetching students: {str(e)}', 'error')
        return render_template('view.html', students=[])

@app.route('/delete/<int:student_id>', methods=['POST'])
def delete(student_id):
    try:
        cursor.execute("DELETE FROM Students WHERE id = ?", (student_id,))
        conn.commit()
        flash('Student deleted successfully!', 'success')
    except pyodbc.Error as e:
        flash(f'Error deleting student: {str(e)}', 'error')
    return redirect('/view')

@app.route('/edit/<int:student_id>', methods=['GET', 'POST'])
def edit(student_id):
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            course = request.form.get('course', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            gender = request.form.get('gender', '').strip()
            dob = request.form.get('dob', '').strip()

            # Validate all fields
            errors = validate_form_data(name, email, course, phone, address, gender, dob)
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                return redirect(f'/edit/{student_id}')

            cursor.execute("""
                UPDATE Students 
                SET name = ?, email = ?, course = ?, phone = ?, address = ?, gender = ?, dob = ?
                WHERE id = ?
            """, (name, email, course, phone, address, gender, dob, student_id))
            
            conn.commit()
            flash('Student updated successfully!', 'success')
            return redirect('/view')
        except pyodbc.Error as e:
            flash(f'Error updating student: {str(e)}', 'error')
            return redirect(f'/edit/{student_id}')

    # GET request - show edit form
    try:
        cursor.execute("SELECT id, name, email, course, phone, address, gender, dob FROM Students WHERE id = ?", (student_id,))
        student = cursor.fetchone()
        if not student:
            flash('Student not found!', 'error')
            return redirect('/view')
        return render_template('edit.html', student=student)
    except pyodbc.Error as e:
        flash(f'Error fetching student: {str(e)}', 'error')
        return redirect('/view')

if __name__ == '__main__':
    app.run(debug=True)