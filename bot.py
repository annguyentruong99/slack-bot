import os
import re
import json
import random
import string
import requests

from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

app = Flask(__name__) # create a Flask application from the current file

# This function is to show the instruction to the new users, helpful when the application scale
def help_command():
  return "Hướng Dẫn Sử Dụng Trước Khi Dùng:\n\t/cba huong-dan\n\t/cba tao-tai-khoan <username> <email>"

# This function is to handle the registration of new students
def register_student(username, email):
  url = "https://cbavn.com/wp-json/wp/v2/users/register"
  password = ''
  password_chars = string.ascii_letters + string.digits + string.punctuation # This is to create a string contains all alphabetical letters, numbers, and punctuations
  # repeat the action 15 times to get a password that contain 15 random characters
  for i in range(15):
    password += random.choice(password_chars) # choose a random character in password_chars string and put it into the password
  student_metadata = {
    "username": username,
    "email": email,
    "password": password
  }
  headers = {
  'Content-Type': 'application/json'
  }
  res = requests.request("POST", url, headers=headers, data=json.dumps(student_metadata))
  res_code = res.json()["code"]
  if res_code == 406: # Check whether the account has been created in the system
    return "Tài khoản này đã có trong hệ thống"
  return f"Tài khoản đã được tạo! :tada:\n\tusername: {username}\n\temail: {email}\n\tpassword: {password}"
  

# This function is to add the course to a new or existing account
def assign_course(user_id, course_id):
  pass


# This function is to handle the message execution word following the slash command
def request_handler(message):
  message = message.split(" ")
  command = message[0] # Extract the message execution word
  message = message[1:] # Extract the command's params
  notFound = "Làm gì có cái câu lệnh như thế lày! :grinning: Mời bạn chạy /cba huong-dan nếu chưa biết dùng hoặc kiểm tra lại xem có sai sót trong câu lệnh không :grinning:"
  if command == "huong-dan":
    return help_command()
  elif command == "tao-tai-khoan" and len(message) == 2:
    if len(message) == 0:
      return "Chưa có username và/hoặc email của học sinh"
    else:
      username = message[0]
      email = message[1]
      return register_student(username, email)
  else:
    return notFound

@app.route("/", methods=["POST"])
def main():
  message = request.form.get("text")
  data = {
    "text": request_handler(message),
    "response_type": "in_channel"
  }
  return Response(response=json.dumps(data), status=200, mimetype="application/json")


if __name__ == "__main__":
  app.run()