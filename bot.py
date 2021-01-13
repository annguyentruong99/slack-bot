import os
import re
import json
import random
import string
import requests

from pathlib import Path
from dotenv import load_dotenv
from threading import Thread
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

app = Flask(__name__) # create a Flask application from the current file

# This function is dedicated to posting messages to posting message to Slack
def post_message(message: str):
  webhook_url = os.environ["WEBHOOK_URL"]
  slack_data = {'text': message, 'response_type': 'in_channel'}
  response = requests.post(webhook_url, data=json.dumps(slack_data), headers={'Content-Type': 'application/json'})

# This function is to get the ids of the corresponding courses
def get_course_ids() -> dict:
  course_ids = {}
  url = os.environ["COURSES_API"]
  payload={}
  headers = {
    'Authorization': 'Basic YW4ubmd1eWVudHJ1b25nOTlAZ21haWwuY29tOkx1b2N0aGl0Z2ExMjM='
  }
  response = requests.request("GET", url, headers=headers, data=payload)
  for res in response.json():
    if res["id"] not in course_ids:
      course_ids[res["title"]["rendered"]] = res["id"]
  return course_ids

# This function is to show the instruction to the new users, helpful when the application scale
def help_command() -> str:
  return post_message("Hướng Dẫn Sử Dụng Trước Khi Dùng:\n\t/cba huong-dan\n\t/cba tao-tai-khoan <email> <course_id>")

def post_req(url: str, data: dict) -> bool:
  headers = {
  'Authorization': os.environ["AUTH"],
  'Content-Type': 'application/json'
  }
  res = requests.request("POST", url, headers=headers, data=json.dumps(data))
  return True

# This function is to handle the registration of new students
def register_student(email: str) -> str:
  url = os.environ["USERS_API"]
  password = ''
  username = email.split("@")[0]
  password_chars = string.ascii_letters + string.digits + string.punctuation # This is to create a string contains all alphabetical letters, numbers, and punctuations
  # repeat the action 15 times to get a password that contain 15 random characters
  for i in range(15):
    password += random.choice(password_chars) # choose a random character in password_chars string and put it into the password
  student_metadata = {
    "username": username,
    "email": email,
    "password": password
  }
  post_req(url, student_metadata)
  if post_req(url, student_metadata) == True:
    return post_message(f"Tài khoản của học sinh đã được tạo thành công, dưới đây là thông tin của tài khoản:\n\t Username: {username} \n\t Password: {password}")
  else:
    return post_message("Lập tài khoản thất bại, thử lại hoặc kiểm tra hệ thống xem tài khoản đã được lập chưa.")
  

# This function is to handle the message execution word following the slash command
def request_handler(message:str) -> str:
  message = message.split(" ")
  command = message[0] # Extract the message execution word
  message = message[1:] # Extract the command's params
  notFound = "Làm gì có cái câu lệnh như thế lày! :grinning: Mời thanh niên chạy /cba huong-dan nếu chưa biết dùng hoặc kiểm tra lại xem có sai sót trong câu lệnh không :grinning:"
  if command == "huong-dan":
    return help_command()
  elif command == "tao-tai-khoan" and len(message) >= 1:
    if len(message) == 0:
      return post_message("Chưa có username và/hoặc email của học sinh")
    else:
      email = message[0]
      return register_student(email)
  elif command == "ma-khoa-hoc":
    course_ids = get_course_ids()
    message = ""
    for key, val in course_ids.items():
      message += f"{key}: {val}\n"
    post_message(message)
  else:
    return post_message(notFound)


@app.route("/", methods=["POST"])
def main():
  message = request.form.get("text")
  thr = Thread(target=request_handler, args=[message])
  thr.start()
  data = {
    "text": "Loading...",
    "response_type": "in_channel"
  }
  return Response(response=json.dumps(data), status=200, mimetype="application/json")


if __name__ == "__main__":
  app.run(debug=True)