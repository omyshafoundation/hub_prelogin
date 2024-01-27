from flask import Flask,render_template,request
import requests
import mysql.connector
import random
import os
import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')  # Use an absolute path

# Ensure the 'uploads' folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
@app.route('/')
def hello_world():
    mysql_db_config = {
    'host': '127.0.0.1',
    'user': 'vongle',
    'password': 'ashiv3377',
    'database': 'osqacademy',
}
    try:
        mysql_connection = mysql.connector.connect(**mysql_db_config)
        if mysql_connection.is_connected():
            cursor = mysql_connection.cursor()
            query = "SELECT name, description, timestart FROM mdl_event WHERE description LIKE '%<img%' ORDER BY timestart DESC LIMIT 4;"

            cursor.execute(query)
            last_four_records = cursor.fetchall()
            total_records = len(last_four_records)
            select_query = 'SELECT * FROM special_mentions_data' 
            cursor.execute(select_query)
            rows = cursor.fetchall()
            result = [{'id': row[0],
           'name': row[1],
           'image': row[2],
           'title': row[3],
           'title_description': row[4],
           'added_at': row[5].isoformat() if row[5] else None
           } for row in rows]


            starting_row_number = max(1, total_records - 3)  # Display the last 4 rows as 96, 97, 98, 99

# Create lists as before
            names = [record[0] for record in last_four_records]
            descriptions = [record[1] for record in last_four_records]
            timestarts = [record[2] for record in last_four_records]
            for i in range(len(timestarts)):
                timestarts[i] = convert_utc_to_ist_datetime(timestarts[i])
# Create a list of row numbers
            row_numbers = list(range(starting_row_number, starting_row_number + total_records))
            img_variable_list=[]
            for i, description in enumerate(descriptions):
                res = description.split('@@PLUGINFILE@@/', 1)
                splitString = res[1]
                quote_position = splitString.find('"')
                splitString = splitString[:quote_position]
                query=f"SELECT itemid FROM mdl_files WHERE filename = '{splitString}' LIMIT 1 OFFSET 1;"
                print(query)
                cursor.execute(query)
                ids = cursor.fetchone()
                id = ids[0] if ids else None
                
                description = description.replace('@@PLUGINFILE@@', f'https://hub.vong.earth/pluginfile.php/2/calendar/event_description/{id}')
                img_start_index = description.find('<img')

                if img_start_index != -1:
       
                    img_end_index = description.find('>', img_start_index)

                    if img_end_index != -1:
            # Extract content between <img> and </img>
                        img_content = description[img_start_index :img_end_index+1]
                    else:
            # If </img> is not present, extract content until the end of the string
                        img_content = description[img_start_index :]
                    img_variable = img_content.strip()
                    img_variable_list.append(img_variable)
                descriptions[i] = remove_html_tags(description.replace(img_variable, ''))
            data_for_template = zip(row_numbers, names, descriptions, timestarts,img_variable_list)
            

            #api for leaderboARD
            api_url = 'https://hub.vong.earth/webservice/rest/server.php'

            # Access token (replace 'your-access-token' with your actual access token)
            access_token = 'd478810b234eb7682244b9f474c7468f'

            # Function to make a request to the Moodle API
            def make_moodle_api_request(function, params=None):
                data = {
                    'wstoken': access_token,
                    'wsfunction': function,
                    'moodlewsrestformat': 'json'
                }
                if params:
                    data.update(params)

                response = requests.post(api_url, data=data)
                return response.json()

# Function to generate random avatar color
            def generate_random_color():
                color = '#' + ''.join(random.choices('0123456789ABCDEF', k=6))
                return color

# Course ID (replace 'course-id' with the actual course ID)
            students = []
            students_data=[]
            course_ids = ['14', '16', '17'] 
            for course_id in course_ids:
                # Retrieve all enrolled users
                users_response = make_moodle_api_request('core_enrol_get_enrolled_users', {
                    'courseid': course_id
                })
    

    # Process and collect grades for each user
   
                excluded_titles = ["Course total"]

                for user in users_response:
                    user_id = user['id']
                    fullname = user['fullname']
                    email_address = user['email']

        # Retrieve grades table for the user
                    grades_response = make_moodle_api_request('gradereport_user_get_grades_table', {
                    'userid': user_id,
                    'courseid': course_id
                    })

        # Process and collect the grades for the user
                    if 'tables' in grades_response and len(grades_response['tables']) > 0:
                        grades_table = grades_response['tables'][0]['tabledata']
                        grades_total = 0  # Initialize total grades for the user

                        for grade_item in grades_table:
                            if 'itemname' in grade_item and 'content' in grade_item['itemname']:
                                grade_item_name = grade_item['itemname']['content']
                            else:
                                grade_item_name = 'N/A'

                            grade = 'N/A'

                            if 'grade' in grade_item:
                                grade = grade_item['grade']['content']

                  # Exclude rows related to specific column titles
                            exclude_row = True
                            for title in excluded_titles:
                                if title in grade_item_name:
                                    exclude_row = False
                                    break

                            if exclude_row:
                                continue

    # Check if the grade is numeric
                            if grade.replace('.', '', 1).isdigit():
                                grades_total += float(grade)

                            student1 = {
                                'user_id': user_id,
                'fullname': fullname,
                'email_address': email_address,
                'grades_total': grades_total,
                'avatar_color': generate_random_color()  # Generate random avatar color
                             }
                            students_data.append(student1)
            students_dict = {}
            print(students_data)
            for student_data in students_data:
                user_id = student_data['user_id']
                grades_total = student_data['grades_total']

                if user_id in students_dict:
                    students_dict[user_id]['grades_total'] += grades_total
                else:
                    student = {
            'user_id': user_id,
            'fullname': student_data['fullname'],
            'email_address': student_data['email_address'],
            'grades_total': grades_total,
            'avatar_color': generate_random_color()
                }
                    students_dict[user_id] = student
  

            students = list(students_dict.values())

# Sort students based on grades in descending order
            students.sort(key=lambda x: x['grades_total'], reverse=True)

# Retrieve top three students
            top_three_students = students[:3]
            return render_template('index.html', data=data_for_template,mentions=result,top_three_students=top_three_students, students=students)
           
            
    except Exception as e:
        # Handle exceptions appropriately (e.g., log the error)
        print(f"Error: {e}")
        return render_template('error.html', error_message=str(e)), 500

    finally:
        if mysql_connection.is_connected():
            cursor.close()
            mysql_connection.close()


def convert_utc_to_ist_datetime(timestamp_utc):
    utc_datetime = datetime.utcfromtimestamp(timestamp_utc)
    utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    ist_datetime = utc_datetime.astimezone(timezone(timedelta(hours=5, minutes=30)))
    converted_ist_timestamp = ist_datetime.strftime('%Y-%m-%d %H:%M')
    return converted_ist_timestamp

def remove_html_tags(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    text_content = soup.get_text()
    return text_content
from flask import send_from_directory



@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


@app.route('/admin')
def admin():
    return render_template('adminform.html')

@app.route('/submit_admin', methods=['POST'])
def submit():
    host = 'localhost'
    user = 'vongle'
    password = 'ashiv3377'
    database = 'osqacademy'

    try:
        if request.method == 'POST':
            name = request.form['name']
            title = request.form['title']
            description = request.form['description']

            # Use request.files to get the uploaded file
            image = request.files['image']
            
            # Save the uploaded file to the 'uploads' folder
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))

            with mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            ) as conn:
                with conn.cursor(dictionary=True) as cursor:
                    # Use parameterized query to prevent SQL injection
                    insert_query = "INSERT INTO special_mentions_data (name, image, title, title_description) VALUES (%s, %s, %s, %s);"
                    cursor.execute(insert_query, (name, image.filename, title, description))

                # Commit the changes after the inner cursor block
                conn.commit()

            return "Data submitted successfully."

    except mysql.connector.Error as err:
        return f"Error: {err}"


if __name__ == '__main__':
    app.run(debug=True)
