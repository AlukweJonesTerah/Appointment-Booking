# Appointment-Booking
This is project is a booking appoint project that utilizes google calendar API. It allows clients clients and customers to book sessions and appointments in order to meet an agent.
This project can be implemented in chatbots and any other systems of intrest. It also open to any suggestions of improvement and contribution.

Note: This is just a sandbox project the UI is simple and plain with no design. The views and algorithms implemented in the project are plain and not complex or good fit logic but any one is invited to contribute on the project and maybe improve it.

To Use this project or to test it you google calendar client_sceret.json file,and token.json file 
To get the client_sceret.json file you can create a google developer account and visit this link for more instructions

https://developers.google.com/calendar/api/quickstart/python

To get the token.json file just run the app.py file or caltut.py file for the first time run

To run the project run the app.py

database setting 
run 

export FLASK_APP=pythonProject-4-Copy

flask db init
flask db migrate -m "Initial migration"
flask db upgrade
