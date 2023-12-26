# FlaskMqttDashBoard
#### Video Demo:  <https://youtu.be/QfBfFyhZyJc>
#### Description:
A dashboard generator for MQTT messaging using flask. The webapp supports multiple users where each user has their own dashboard, subscribtion and publish nodes. The messages history for each node is saved in a data base where each is linked to a used ID.

The app.py contains the main python code for the flask webapp. helper.h has a sum of functions assisting and main code. The flask webapp is built based of the finance assignment webapp, using its uses implimntation usings flask_session and security using werkzeug.security libraries. The webapp uses flask_mqtt library to implement the MQTT communication protocol, using each user username, and topics subscribed to and set as publish nodes as unique topics. The webapp uses the public mqtt broker 'broker.emqx.io', initially I wanted each user to be able to use whatever broker they wanted, but changing the broker needed the webapp to reset and that was not possible. limited by the mqtt library and set a universal public broker.

mqtt.db is the database for the project, it saves the users data, and logs all messages and topics, containing multiple tables for each task. The fist table 'users' contains the users database, their passwords hash and their unique topics path generated with the username plus random letters to assure that its unique since a public broker is used. topics is the second table, containing the topics names, their type if publish of subscribe point, and linking each topic to the user id. log is another table containing every message in or out from the app, linking every message to its user id.

inside the template folder is the HTML template used for the website. login.html and register.html are used to log the user in. index.html has the main user dashboard, consist of two parts, the first is a table showing all subscribed nodes and the last message came to that node, the second part is multiple html form, each form belong to a publish node, enabling the dashboard user to publish messages to that topic using the webapp dashboard. addpub.html and addsub.html are user to add topics nodes for the webapp to add to the dashboard. log.html shows all the messages came to and published from the webapp, it only shows the log for the signed in user, having the message unique topic, message, and timestamp.



