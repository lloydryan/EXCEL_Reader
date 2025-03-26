# Developer: LLOYD RYAN LArgo
# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, FileField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import mysql.connector
import base64
import pandas as pd
import io
import os

app = Flask(__name__, 
            template_folder=os.path.join(os.getcwd(), 'templates'),  # For HTML files
            static_folder=os.path.join(os.getcwd(), 'static'))   
app.secret_key = 'supersecretkey'
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# MySQL configuration
mysql_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'als',
    'autocommit': True
}

# Define a User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, first_name=None, last_name=None, birthday=None, address=None, profile_picture=None):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.birthday = birthday
        self.address = address
        self.profile_picture = profile_picture


# Login form using Flask-WTF
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Registration form using Flask-WTF
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=20)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    birthday = DateField('Birthday', format='%Y-%m-%d', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired(), Length(max=255)])
    profile_picture = FileField('Profile Picture')
    submit = SubmitField('Register')

    def set_default_profile_picture(self):
        # Set default profile picture path here (adjust the path as per your structure)
        default_picture_path = 'static/default_profile.jpeg'
        # Open the default picture file and assign it to profile_picture field
        with open(default_picture_path, 'rb') as f:
            self.profile_picture.data = f.read()

    def get_profile_picture_data(self):
        if self.profile_picture.data:
            return base64.b64encode(self.profile_picture.data.read()).decode('utf-8')
        else:
            # Set default profile picture if no file is uploaded
            with open('static/default_profile.jpeg', 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')

# Profile management form using Flask-WTF
class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    birthday = DateField('Birthday', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    profile_picture = FileField('Upload New Profile Picture')

# Initialize MySQL connection
def get_mysql_connection():
    return mysql.connector.connect(**mysql_config)

@login_manager.user_loader
def load_user(user_id):
    # Load user from database based on user_id
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT id, username, first_name, last_name, birthday, address, profile_picture FROM teachers WHERE id = %s"
    cursor.execute(query, (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    if user_data:
        return User(user_data['id'], user_data['username'], user_data['first_name'], user_data['last_name'],
                    user_data['birthday'], user_data['address'], user_data['profile_picture'])
    return None

# Route for login page
@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, password FROM teachers WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and password == user['password']:
            user_obj = User(user['id'], username)
            login_user(user_obj)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')
    
    return render_template('login.html', title='Login', form=form)

# Route for logout
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    if request.method == 'POST':
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))
    else:
        flash('Method Not Allowed', 'error')
        return redirect(url_for('login'))


# Route for dashboard page
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Route for registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        birthday = form.birthday.data
        address = form.address.data
        profile_picture = form.get_profile_picture_data()
        
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if the username already exists in the database
        query = "SELECT * FROM teachers WHERE username = %s"
        cursor.execute(query, (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect(url_for('register'))
        
        # If the username is unique, proceed with registration
        query = "INSERT INTO teachers (username, password, first_name, last_name, birthday, address, profile_picture) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (username, password, first_name, last_name, birthday, address, profile_picture))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('register'))
    
    return render_template('register.html', title='Register', form=form)


# Route for user profile management
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    
    if form.validate_on_submit():
        username = form.username.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        birthday = form.birthday.data
        address = form.address.data
        profile_picture = current_user.profile_picture  # Start with current profile picture
        
        if form.profile_picture.data:  # Check if new picture uploaded
            profile_picture = base64.b64encode(form.profile_picture.data.read()).decode('utf-8')
        
        conn = get_mysql_connection()
        cursor = conn.cursor()
        query = "UPDATE teachers SET username = %s, first_name = %s, last_name = %s, birthday = %s, address = %s, profile_picture = %s WHERE id = %s"
        cursor.execute(query, (username, first_name, last_name, birthday, address, profile_picture, current_user.id))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.birthday.data = current_user.birthday
        form.address.data = current_user.address
        form.profile_picture.data = current_user.profile_picture  # For displaying only
    
    return render_template('profile.html', title='Profile', form=form)

# Route to display all uploaded files
@app.route('/files')
@login_required
def list_files():
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        
        # Fetch all uploaded files from the results table
        query = "SELECT id, file_name FROM results"
        cursor.execute(query)
        files = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('file_list.html', files=files)
    except mysql.connector.Error as err:
        flash(f"Error: {err}")
        return render_template('file_list.html', files=[])

# Route to upload a new file
@app.route('/upload')
@login_required
def upload_file():
    return render_template('upload.html')

@app.route('/uploader', methods=['POST'])
@login_required
def uploader():
    if 'file' not in request.files:
        flash("No file part")
        return redirect(url_for('upload_file'))
    file = request.files['file']
    if file.filename == '':
        flash("No selected file")
        return redirect(url_for('upload_file'))
    if file:
        file_data = file.read()
        
        # Save the file info to the database
        try:
            conn = mysql.connector.connect(**mysql_config)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO results (file_name, file_data) VALUES (%s, %s)", (file.filename, file_data))
            conn.commit()
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            flash(f"Error: {err}")
            return redirect(url_for('upload_file'))
        
        flash("File successfully uploaded")
        return redirect(url_for('list_files'))
# Route to read and process a selected file
@app.route('/process_file/<int:file_id>')
def process_file(file_id):
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        
        # Fetch file data for the selected file
        cursor.execute("SELECT file_data FROM results WHERE id = %s", (file_id,))
        file = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if file:
            global uploaded_data
            file_data = file['file_data']
            excel_data = io.BytesIO(file_data)
            try:
                uploaded_data = pd.read_excel(excel_data, usecols="A:CO")  # Reading the specified columns
                max_rows = len(uploaded_data)
                return render_template('row_selector.html', max_rows=max_rows)
            except pd.errors.ParserError:
                return render_template('error.html', error_message="File is not supported on this web app.")
        else:
            flash("File not found")
            return redirect(url_for('list_files'))
    except mysql.connector.Error as err:
        flash(f"Error: {err}")
        return redirect(url_for('list_files'))

@app.route('/delete_file/<int:file_id>', methods=['POST'])
def delete_file(file_id):
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()

        # Delete the file record from the database
        cursor.execute("DELETE FROM results WHERE id = %s", (file_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'error': str(err)})



# Function to connect to MySQL database and fetch data for specific columns

def get_column_pairs_data(columns):
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        
        # Create conditions to exclude rows with null values in the specified columns
        conditions = [f"{col} IS NOT NULL" for col in columns]
        query = f"SELECT {', '.join(columns)} FROM answer_key WHERE {' AND '.join(conditions)}"
        
        cursor.execute(query)
        column_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return column_data
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []


# Route to display data from specific column pairs
@app.route('/answer')
@login_required
def answer_key_table():
    pairs = [
        ('Question_NO', 'LS1_English'),
        ('Question_NO', 'LS1_Filipino'),
        ('Question_NO', 'LS2'),
        ('Question_NO', 'LS3'),
        ('Question_NO', 'LS4'),
        ('Question_NO', 'LS5'),
        ('Question_NO', 'LS6')
    ]
    
    all_column_data = {}
    for pair in pairs:
        column_data = get_column_pairs_data(pair)
        all_column_data[pair] = column_data

    return render_template('answer_key_table.html', all_column_data=all_column_data)

# Retrieve data for selected row and show student details
@app.route('/retrieve', methods=['POST'])
def retrieve_data():
    global uploaded_data
    if uploaded_data is None:
        flash("No data available. Please upload a file first.")
        return redirect(url_for('upload_file'))
    
    row_number = int(request.form['row_number'])
    if row_number < 1 or row_number > len(uploaded_data):
        flash(f"Row number must be between 1 and {len(uploaded_data)}")
        return redirect(url_for('upload_file'))
    
    return redirect(url_for('show_row_data', row_number=row_number))

# Show row data with student details and scores
@app.route('/show_row_data/<int:row_number>', methods=['GET', 'POST'])
@login_required
def show_row_data(row_number):

    first_name = current_user.first_name.title()
    last_name = current_user.last_name.title()


    global uploaded_data
    if uploaded_data is None:
        flash("No data available. Please upload a file first.")
        return redirect(url_for('list_files'))
    
    if row_number < 1 or row_number > len(uploaded_data):
        flash(f"Row number must be between 1 and {len(uploaded_data)}")
        return redirect(url_for('list_files'))
    
    row_data = uploaded_data.iloc[row_number - 1]  # Row numbers are 1-based
    name = row_data.get("1) What is your complete name?   ", 'N/A')
    date = row_data.get("Timestamp")
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        
        # Check if student name exists in the table
        cursor.execute("SELECT * FROM students WHERE student_name = %s", (name,))
        existing_student = cursor.fetchone()
        
        if not existing_student:
            # If student does not exist, insert with default values
            insert_query = """
                INSERT INTO students (student_name, LS1_English_Q8, LS1_English_Q9, LS1_English_Q10, LS1_English_Q11, LS1_English_Q12, LS1_English_Q13, 
                LS1_Filipino_Q8, LS1_Filipino_Q9, LS1_Filipino_Q10, LS1_Filipino_Q11, PIS_Q1, PIS_Q2, PIS_Q3, PIS_Q4, PIS_Q5, PIS_Q6, PIS_Q7, PIS_Q8, PIS_Q9)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            default_values = (name, 2, 2, 1, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1)  # Default values
            cursor.execute(insert_query, default_values)
            conn.commit()
        
        # Fetch student data including LS1_English, LS1_Filipino scores, and PIS scores
        cursor.execute("""
            SELECT LS1_English_Q8, LS1_English_Q9, LS1_English_Q10, LS1_English_Q11, LS1_English_Q12, LS1_English_Q13, 
                LS1_Filipino_Q8, LS1_Filipino_Q9, LS1_Filipino_Q10, LS1_Filipino_Q11, 
                PIS_Q1, PIS_Q2, PIS_Q3, PIS_Q4, PIS_Q5, PIS_Q6, PIS_Q7, PIS_Q8, PIS_Q9 
            FROM students
            WHERE student_name = %s
        """, (name,))
        
        student_data = cursor.fetchone()
        
        cursor.close()
        conn.close()

        if student_data:
            ls1_english_q8 = student_data['LS1_English_Q8']
            ls1_english_q9 = student_data['LS1_English_Q9']
            ls1_english_q10 = student_data['LS1_English_Q10']
            ls1_english_q11= student_data['LS1_English_Q11']
            ls1_english_q12= student_data['LS1_English_Q12']
            ls1_english_q13= student_data['LS1_English_Q13']
            ls1_filipino_q8 = student_data['LS1_Filipino_Q8']
            ls1_filipino_q9 = student_data['LS1_Filipino_Q9']
            ls1_filipino_q10 = student_data['LS1_Filipino_Q10']
            ls1_filipino_q11 = student_data['LS1_Filipino_Q11']

            pis_scores = {
                'Q1': student_data['PIS_Q1'],
                'Q2': student_data['PIS_Q2'],
                'Q3': student_data['PIS_Q3'],
                'Q4': student_data['PIS_Q4'],
                'Q5': student_data['PIS_Q5'],
                'Q6': student_data['PIS_Q6'],
                'Q7': student_data['PIS_Q7'],
                'Q8': student_data['PIS_Q8'],
                'Q9': student_data['PIS_Q9']
            }
            total_score_PIS = sum(pis_scores.values())            
            
            column_to_score_key = {
                '1) What is your complete name?   ': 'Q1',
                '2) What is your sex? Check (\uf0fc) the corresponding box.  ': 'Q2',
                '3) When is your date of birth?   ': 'Q3',
                '4)  Where do you live?   ': 'Q4',
                '5) What is your religion?  ': 'Q5',
                '6) What is your marital status? Check (\uf0fc) the corresponding box.  ': 'Q6',
                '7)  What is your job/occupation?   ': 'Q7',
                '8)  What is your highest educational attainment?   ': 'Q8',
                'B. Write a paragraph composed of two (2) to three (3) sentences about yourself, including your interests and ambition.  ': 'Q9'
            }
            columns_C_to_K = uploaded_data.columns[2:11]

            additional_columns_C_to_K = {
            col: {
                'value': '' if pd.isna(row_data.get(col)) else row_data.get(col, 'N/A'),
                'score': pis_scores.get(column_to_score_key.get(col, ''), 0) 
            }
            for col in columns_C_to_K
            }

            
            # Additional columns
            def get_value_or_blank(value):
                # Return empty string if value is NaN, otherwise return the value
                return '' if pd.isna(value) else value

            # Handle columns from L to X
            additional_columns_L_to_X = {
                col: get_value_or_blank(row_data.get(col, ''))
                for col in uploaded_data.columns[11:24]
            }

            # Handle columns from Y to AI
            additional_columns_Y_to_AI = {
                col: get_value_or_blank(row_data.get(col, ''))
                for col in uploaded_data.columns[24:35]
            }

            # Handle columns from AJ to AV
            additional_columns_AJ_to_AV = {
                col: get_value_or_blank(row_data.get(col, ''))
                for col in uploaded_data.columns[35:48]
            }

            # Handle columns from AW to BK
            additional_columns_AW_to_BK = {
                col: get_value_or_blank(row_data.get(col, ''))
                for col in uploaded_data.columns[48:63]
            }

            # Handle columns from BL to BU
            additional_columns_BL_to_BU = {
                col: get_value_or_blank(row_data.get(col, ''))
                for col in uploaded_data.columns[63:73]
            }

            # Handle columns from BV to CE
            additional_columns_BV_to_CE = {
                col: get_value_or_blank(row_data.get(col, ''))
                for col in uploaded_data.columns[73:83]
            }

            # Handle columns from CF to CO
            additional_columns_CF_to_CO = {
                col: get_value_or_blank(row_data.get(col, ''))
                for col in uploaded_data.columns[83:93]
                
            }
            
            
            
            max_rows = len(uploaded_data)
            
            # Fetch LS data from the database
            ls1_english_data = get_column_pairs_data(['LS1_English'])
            ls1_filipino_data = get_column_pairs_data(['LS1_Filipino'])
            ls2_data = get_column_pairs_data(['LS2'])
            ls3_data = get_column_pairs_data(['LS3'])
            ls4_data = get_column_pairs_data(['LS4'])
            ls5_data = get_column_pairs_data(['LS5'])
            ls6_data = get_column_pairs_data(['LS6'])
            
            # Prepare combined data for each set of columns
            combined_data = {
                'Ls1_English': prepare_combined_data(additional_columns_L_to_X, [row['LS1_English'] for row in ls1_english_data]),
                'Ls1_Filipino': prepare_combined_data(additional_columns_Y_to_AI, [row['LS1_Filipino'] for row in ls1_filipino_data]),
                'Ls2': prepare_combined_data(additional_columns_AJ_to_AV, [row['LS2'] for row in ls2_data]),
                'Ls3': prepare_combined_data(additional_columns_AW_to_BK, [row['LS3'] for row in ls3_data]),
                'Ls4': prepare_combined_data(additional_columns_BL_to_BU, [row['LS4'] for row in ls4_data]),
                'Ls5': prepare_combined_data(additional_columns_BV_to_CE, [row['LS5'] for row in ls5_data]),
                'Ls6': prepare_combined_data(additional_columns_CF_to_CO, [row['LS6'] for row in ls6_data])
            }
            
            question_scores = calculate_question_scores(name, combined_data, additional_columns_Y_to_AI)



            
            
            if request.method == 'POST':
                return redirect(url_for('update_score', row_number=row_number))
            else:
                return render_template('row_data.html', name=name, date=date, 
                                       row_number=row_number,  # Pass row_number to template
                                       ls1_english_q8=ls1_english_q8, ls1_english_q9=ls1_english_q9,
                                       ls1_english_q10=ls1_english_q10, ls1_english_q11=ls1_english_q11,
                                       ls1_english_q12=ls1_english_q12, ls1_english_q13=ls1_english_q13,
                                       ls1_filipino_q8=ls1_filipino_q8, ls1_filipino_q9=ls1_filipino_q9,
                                       additional_columns_L_to_T=additional_columns_L_to_X, additional_columns_C_to_K=additional_columns_C_to_K,
                                       total_score_PIS=total_score_PIS,max_rows=max_rows,pis_scores=pis_scores, 
                                       combined_data=combined_data,
                                       question_scores=question_scores,first_name=first_name, 
                                       last_name=last_name)
        else:
            flash(f"No data found for student: {name}")
            return redirect(url_for('list_files'))
    
    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return redirect(url_for('list_files'))


def prepare_combined_data(additional_columns, ls_data):
    combined_data = []
    additional_values = list(additional_columns.values())
    
    # Ensure both lists are of the same length for a one-to-one mapping
    length = min(len(additional_values), len(ls_data))
    for i in range(length):
        combined_data.append({
            'column': list(additional_columns.keys())[i],
            'uploaded_value': additional_values[i],
            'ls_value': ls_data[i]
        })
    return combined_data
def calculate_question_scores(name, combined_data, additional_columns_U_to_AC):
    question_scores = {}
    for section, data in combined_data.items():
        section_scores = []
        for i, item in enumerate(data):
            question_no = i + 1
            uploaded_value = str(item['uploaded_value']).strip().upper()
            ls_value = str(item['ls_value']).strip().upper()

            score = 0
            if ls_value == '2POINTS':
                score = fetch_score_from_db(name, section, question_no, default=2)
            elif ls_value == '1POINT':
                score = fetch_score_from_db(name, section, question_no, default=1)
            elif uploaded_value and uploaded_value[0] == ls_value:
                score = 1
            
            section_scores.append({'question_no': question_no, 'score': score})

        question_scores[section] = section_scores

    # Add LS1 Filipino question 7 result to the question scores
    ls1_filipino_q7_score = check_ls1_filipino_question_7(additional_columns_U_to_AC)
    question_scores['Ls1_Filipino'][6]['score'] = ls1_filipino_q7_score

    return question_scores

def fetch_score_from_db(student_name, section, question_no, default=0):
    column_map = {
        'Ls1_English': [8, 9, 10, 11, 12, 13],
        'Ls1_Filipino': [8, 9, 10, 11]
    }
    if section in column_map and question_no in column_map[section]:
        column_name = f"{section}_Q{question_no}"
        try:
            conn = mysql.connector.connect(**mysql_config)
            cursor = conn.cursor()
            query = f"SELECT {column_name} FROM students WHERE student_name = %s"
            cursor.execute(query, (student_name,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result[0] if result else default
        except mysql.connector.Error as err:
            print(f"Error fetching {column_name}: {err}")
            return default
    return default

def check_ls1_filipino_question_7(additional_columns):
    question_7_column = list(additional_columns.keys())[6]
    uploaded_value = str(additional_columns[question_7_column]).strip().upper()
    return 1 if uploaded_value in ['KOMPYUTER'] else 0

@app.route('/update_score', methods=['POST'])
def update_score():
    student_name = request.form['student_name']
    section = request.form['section']
    question_no = int(request.form['question_no'])
    score = int(request.form['score'])
    row = int(request.form['row'])

    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()

        column_map = {
            'Ls1_English': [8, 9, 10, 11, 12, 13],
            'Ls1_Filipino': [8, 9, 10, 11]
        }

        if section in column_map and question_no in column_map[section]:
            column_name = f"{section}_Q{question_no}"
            query = f"UPDATE students SET {column_name} = %s WHERE student_name = %s"
            cursor.execute(query, (score, student_name))

        conn.commit()
        cursor.close()
        conn.close()

        flash('Score updated successfully')
    except mysql.connector.Error as err:
        flash(f"Error: {err}")

    return redirect(url_for('show_row_data', row_number=row))


@app.route('/update_score_pis', methods=['POST'])
def update_score_pis():
    row = request.form['row']
    question_id = request.form['question_id']
    student_name = request.form['student_name']
    section = request.form['section']
    score = request.form['score']

    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()
        
        # Ensure that question_id is valid and avoid SQL injection
        valid_columns = [
            'PIS_Q1', 'PIS_Q2', 'PIS_Q3', 'PIS_Q4', 'PIS_Q5',
            'PIS_Q6', 'PIS_Q7', 'PIS_Q8', 'PIS_Q9'
        ]
        if question_id not in valid_columns:
            raise ValueError("Invalid question ID")

        update_query = f"UPDATE students SET {question_id} = %s WHERE student_name = %s"
        cursor.execute(update_query, (score, student_name))
        conn.commit()
    
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()
    print(f"Row: {row}, Question ID: {question_id}, Score: {score}, Student Name: {student_name}, Section: {section}")
    return redirect(url_for('show_row_data', row_number=row))


if __name__ == '__main__':
    app.run(debug=True)
