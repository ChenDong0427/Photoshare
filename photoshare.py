######################################
# Author: Chen Dong
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'aSecreteKey'

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'RandomCharacters'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

"""
Below is the main functions
"""

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getUserFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()

def getUserFromId(id):
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Users WHERE user_id = '{0}'".format(id))
	return cursor.fetchone()

def getUserActivityScore(id):
	cursor = conn.cursor()
	cursor.execute("SELECT U.user_id, (SELECT COUNT(P.picture_id) FROM Pictures P WHERE P.user_id='{0}'), (SELECT COUNT(C.comment_id) FROM Comments C WHERE C.user_id='{0}') FROM Users U WHERE U.user_id='{0}'".format(id))
	return cursor.fetchone()

def getTopUsersByActivityScore():
	cursor = conn.cursor()
	cursor.execute("SELECT U.user_id, U.first_name, U.last_name, (SELECT COUNT(P.picture_id) FROM Pictures P WHERE P.user_id=U.user_id) AS pic_count, (SELECT COUNT(C.comment_id) FROM Comments C WHERE C.user_id=U.user_id) AS comment_count FROM Users U ORDER BY (pic_count + comment_count) DESC")
	return cursor.fetchall()

def getFriends(id):
	cursor = conn.cursor()
	cursor.execute("SELECT U.* FROM Friends F LEFT JOIN Users U ON U.user_id = F.user_id2 WHERE F.user_id1 = '{0}'".format(id))
	return cursor.fetchall()

def addFriend(id, friend_id):
	if id != friend_id:
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Friends (user_id1, user_id2) VALUES ('{0}', '{1}'), ('{1}', '{0}')".format(id, friend_id))
		conn.commit()

def removeFriend(id, friend_id):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Friends WHERE (user_id1='{0}' AND user_id2='{1}') OR (user_id1='{1}' AND user_id2='{0}')".format(id, friend_id))
	conn.commit()

def recommendFriends(id):
	cursor = conn.cursor()
	cursor.execute('''
		SELECT FA.user_id2 AS user_id, U.first_name AS first_name, U.last_name AS last_name, COUNT(*) as common_friends
		FROM Friends FA
		JOIN Friends FB
			ON (FB.user_id2 = FA.user_id1 AND FB.user_id1 = '{0}')
		LEFT JOIN Friends FC
			ON (FC.user_id2 = FA.user_id2 AND FC.user_id1 = '{0}')  
		INNER JOIN Users U ON U.user_id = FA.user_id2   
		WHERE FC.user_id1 IS NULL AND FA.user_id2 != '{0}'
		GROUP BY FA.user_id2
		ORDER BY common_friends DESC;
	 '''.format(id))
	return cursor.fetchall()

def updateUser(old_email, email, firstname, lastname, dateofbirth, hometown, gender):
	cursor = conn.cursor()
	cursor.execute("UPDATE Users SET email='{0}', first_name='{1}', last_name='{2}', date_of_birth='{3}', hometown='{4}', gender='{5}' WHERE email='{6}'".format(email, firstname, lastname, dateofbirth, hometown, gender, old_email))
	conn.commit()

def changePassword(email, password):
	cursor = conn.cursor()
	cursor.execute("UPDATE Users SET password='{0}' WHERE email='{1}'".format(password, email))
	conn.commit()

def searchUsers(name):
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Users WHERE LOWER(CONCAT_WS(' ', first_name, last_name)) LIKE LOWER('%{0}%')".format(name))
	return cursor.fetchall()

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

def getAlbumsForUser(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Albums WHERE user_id='{0}'".format(uid))
	return cursor.fetchall()

def getAlbumById(album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Albums WHERE album_id='{0}'".format(album_id))
	return cursor.fetchone()

def createAlbum(uid, name):
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Albums (user_id, name) VALUES ('{0}', '{1}')".format(uid, name))
	conn.commit()

def renameAlbum(uid, album_id, name):
	cursor = conn.cursor()
	cursor.execute("UPDATE Albums SET name='{0}' WHERE user_id='{1}' AND album_id='{2}'".format(name, uid, album_id))
	conn.commit()

def deleteAlbum(uid, aid):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Albums WHERE album_id='{0}' AND user_id='{1}'".format(aid, uid))
	conn.commit()

def checkAlbum(uid, album_id):
	cursor = conn.cursor()
	if cursor.execute("SELECT album_id FROM Albums WHERE album_id = '{0}' AND user_id = '{1}'".format(album_id, uid)):
		return True
	else:
		return False

def getPhotos(filters = {}):
	cursor = conn.cursor()

	sql = "SELECT P.*, CONCAT_WS(' ', U.first_name, U.last_name) AS user, A.name AS album_name "
	sql += "FROM Pictures P LEFT JOIN Users U ON U.user_id = P.user_id "
	sql += "LEFT JOIN Albums A ON A.album_id = P.album_id "
	sql += "LEFT JOIN TagPicture TG ON TG.picture_id = P.picture_id WHERE "
	if 'picture_id' in filters:
		sql += "P.picture_id='" + str(filters['picture_id']) + "' AND "
	if 'album_id' in filters:
		sql += "P.album_id='" + str(filters['album_id']) + "' AND "
	if 'user_id' in filters:
		sql += "P.user_id='" + str(filters['user_id']) + "' AND "
	
	if 'tag_id' in filters:
		sql += "TG.tag_id='" + str(filters['tag_id']) + "' AND "
	elif 'tag' in filters:
		sql += "TG.tag_id IN (SELECT T.tag_id AS tag_id FROM Tags T WHERE T.tag = '" + filters['tag'] + "') AND "

	sql += '1=1 GROUP BY P.picture_id ' 

	if 'search' in filters:
		tags_array = filters['search'].strip().split(' ')
		tags = '"' + '","'.join(tags_array) + '"'
		sql += "HAVING SUM(IF(TG.tag_id IN (SELECT T.tag_id AS tag_id FROM Tags T WHERE T.tag IN (" + tags + ")), 1, 0)) = " + str(len(tags_array)) + " "

	sql += 'ORDER BY P.picture_id DESC'

	cursor.execute(sql)
	return cursor.fetchall()

def recommendPhotos(uid):
	cursor = conn.cursor()
	cursor.execute('''
		SELECT P.*, CONCAT_WS(' ', U.first_name, U.last_name) AS user, A.name AS album_name FROM Pictures P
			INNER JOIN TagPicture TP ON TP.picture_id = P.picture_id 
			INNER JOIN 
				(SELECT TPA.tag_id AS tag_id FROM TagPicture TPA INNER JOIN Pictures PA ON PA.picture_id = TPA.picture_id WHERE PA.user_id = '{0}' GROUP BY TPA.tag_id ORDER BY COUNT(PA.picture_id) DESC LIMIT 5) AS TopTags
					ON TopTags.tag_id = TP.tag_id
			LEFT JOIN Users U ON U.user_id = P.user_id
			LEFT JOIN Albums A ON A.album_id = P.album_id
			WHERE P.user_id <> '{0}'
			GROUP BY P.picture_id
			ORDER BY COUNT(P.picture_id) DESC, (SELECT COUNT(TPB.picture_id) FROM TagPicture TPB WHERE TPB.picture_id = P.picture_id) ASC
	'''.format(uid))
	return cursor.fetchall()

def checkPhoto(uid, picture_id):
	cursor = conn.cursor()
	if cursor.execute("SELECT picture_id FROM Pictures WHERE picture_id = '{0}' AND user_id = '{1}'".format(picture_id, uid)):
		return True
	else:
		return False

def updatePhoto(uid, photo_id, caption, album_id):
	cursor = conn.cursor()
	cursor.execute("UPDATE Pictures SET album_id='{0}', caption='{1}' WHERE user_id='{2}' AND picture_id='{3}'".format(album_id, caption, uid, photo_id))
	conn.commit()

def deletePhoto(uid, pictureId):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Pictures WHERE picture_id='{0}' AND user_id='{1}'".format(pictureId, uid))
	conn.commit()

def getTag(tag):
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Tags WHERE tag = '{0}'".format(tag))
	return cursor.fetchone()

def getTagById(tag_id):
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Tags WHERE tag_id = '{0}'".format(tag_id))
	return cursor.fetchone()

def getTagsForPhoto(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT T.tag_id AS tag_id, T.tag as tag FROM Tags T INNER JOIN TagPicture TP ON TP.tag_id = T.tag_id and TP.picture_id = '{0}'".format(photo_id))
	return cursor.fetchall()

def getTopTags():
	cursor = conn.cursor()
	cursor.execute("SELECT T.*, COUNT(TP.tag_id) AS num_used FROM Tags T LEFT JOIN TagPicture TP ON TP.tag_id = T.tag_id GROUP BY T.tag_id HAVING num_used > 0 ORDER BY num_used DESC")
	return cursor.fetchall()

def createTag(tag):
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Tags (tag) VALUES ('{0}')".format(tag))
	conn.commit()
	return cursor.lastrowid

def addTagToPhoto(tag_id, photo_id):
	cursor = conn.cursor()
	cursor.execute("INSERT IGNORE INTO TagPicture SET picture_id = '{0}', tag_id = '{1}'".format(photo_id, tag_id))
	conn.commit()

def removeTagFromPhoto(tag_id, photo_id):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM TagPicture WHERE picture_id='{0}' AND tag_id='{1}'".format(photo_id, tag_id))
	conn.commit()

def getLikesForPhoto(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT L.picture_id AS picture_id, L.user_id AS user_id, U.first_name AS first_name, U.last_name AS last_name FROM Likes L INNER JOIN Users U ON U.user_id = L.user_id WHERE L.picture_id='{0}'".format(photo_id))
	return cursor.fetchall()

def likePhoto(uid, photo_id):
	cursor = conn.cursor()
	cursor.execute("INSERT IGNORE INTO Likes SET user_id = '{0}', picture_id = '{1}'".format(uid, photo_id))
	conn.commit()

def checkLiked(uid, photo_id):
	cursor = conn.cursor()
	if cursor.execute("SELECT picture_id FROM Likes WHERE user_id = '{0}' AND picture_id = '{1}'".format(uid, photo_id)):
		return True
	else:
		return False

def unlikePhoto(uid, photo_id):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Likes WHERE user_id='{0}' AND picture_id='{1}'".format(uid, photo_id))
	conn.commit()

def getCommentsForPhoto(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT C.comment_id AS comment_id, C.picture_id AS picture_id, C.text AS text, C.user_id AS user_id, U.first_name AS first_name, U.last_name AS last_name FROM Comments C LEFT JOIN Users U ON U.user_id = C.user_id WHERE C.picture_id='{0}'".format(photo_id))
	return cursor.fetchall()

def commentPhoto(uid, photo_id, comment):
	cursor = conn.cursor()
	if uid != -1:
		cursor.execute("INSERT INTO Comments (picture_id, user_id, text) VALUES ('{0}', '{1}', '{2}')".format(photo_id, uid, comment))
	else:
		cursor.execute("INSERT INTO Comments (picture_id, text) VALUES ('{0}', '{1}')".format(photo_id, comment))
	conn.commit()

def deleteComment(uid, comment_id):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Comments WHERE comment_id='{0}' AND user_id='{1}'".format(comment_id, uid))
	conn.commit()

def searchComments(search):
	cursor = conn.cursor()
	cursor.execute("SELECT C.comment_id, C.user_id, C.picture_id, C.text, U.first_name, U.last_name FROM Comments C LEFT JOIN Users U ON U.user_id = C.user_id WHERE LOWER(C.text) LIKE LOWER('%{0}%')".format(search))
	return cursor.fetchall()


"""
Below is the login functions
"""

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')



'''
 >> ROUTES
'''

@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message="Welcome to Photoshare", loggedIn = flask_login.current_user.is_authenticated)

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit' value='Login'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('profile'))
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('reg_email')
		password=request.form.get('password')
		firstname=request.form.get('firstname')
		lastname=request.form.get('lastname')
		dateofbirth=request.form.get('dateofbirth')
	except:
		return flask.redirect(flask.url_for('register'))
	
	if len(password) < 6:
		return render_template('register.html', invalidPassword=True)
	
	if len(email) < 1 or len(firstname) < 1 or len(lastname) < 1 or len(dateofbirth) < 1:
		return render_template('register.html', invalidForm=True)

	if isEmailUnique(email):
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Users (email, password, first_name, last_name, date_of_birth) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')".format(email, password, firstname, lastname, dateofbirth))
		conn.commit()
		user = User()
		user.id = email
		flask_login.login_user(user)
		return flask.redirect('/')
	else:
		return render_template('register.html', emailInUse=True)

@app.route('/profile', methods=['GET'])
@flask_login.login_required
def profile():
	return render_template('profile.html', user=getUserFromEmail(flask_login.current_user.id))

@app.route('/profile', methods=['POST'])
@flask_login.login_required
def update_profile():
	try:
		email=request.form.get('email')
		firstname=request.form.get('firstname')
		lastname=request.form.get('lastname')
		dateofbirth=request.form.get('dateofbirth')
		hometown=request.form.get('hometown')
		gender=request.form.get('gender')
	except:
		return flask.redirect(flask.url_for('profile'))
	if email == flask_login.current_user.id or isEmailUnique(email):
		updateUser(flask_login.current_user.id, email, firstname, lastname, dateofbirth, hometown, gender)
		if email != flask_login.current_user.id:
			user = User()
			user.id = email
			flask_login.logout_user()
			flask_login.login_user(user)
		return render_template('profile.html', user=getUserFromEmail(flask_login.current_user.id), message='Profile updated!')
	else:
		return render_template('profile.html', user=getUserFromEmail(flask_login.current_user.id), message='Error: this is email is already in use!')

@app.route('/profile_password', methods=['POST'])
@flask_login.login_required
def update_profile_pass():
	try:
		password=request.form.get('password')
	except:
		return flask.redirect(flask.url_for('profile'))
	if len(password)  < 6:
		return render_template('profile.html', user=getUserFromEmail(flask_login.current_user.id), message='Error: password length must be at least 6!')
	changePassword(flask_login.current_user.id, password)
	return render_template('profile.html', user=getUserFromEmail(flask_login.current_user.id), message='Password was changed!')

@app.route('/user', methods=['GET'])
def user():
	try:
		id=request.args.get('id')
	except:
		return flask.redirect(flask.url_for('hello'))
	user = getUserFromId(id)
	if user == None:
		return flask.redirect(flask.url_for('hello'))
	friends = getFriends(id)
	albums = getAlbumsForUser(id)
	activityScore = getUserActivityScore(id)
	areFriends = False
	ownUser = False
	loggedOff = False
	if flask_login.current_user.is_authenticated:
		ownUser = (flask_login.current_user.id == user[1])
		for friend in friends:
			if friend[1] == flask_login.current_user.id:
				areFriends = True
	else:
		loggedOff = True
	return render_template('user.html', loggedOff=loggedOff, ownUser=ownUser, user=user, friends=friends, areFriends=areFriends, albums=albums, activityScore=activityScore)

@app.route('/user_friend', methods=['POST'])
@flask_login.login_required
def user_add_friend():
	try:
		id=request.form.get('user_id')
	except:
		return flask.redirect(flask.url_for('hello'))
	addFriend(getUserIdFromEmail(flask_login.current_user.id), id)
	return flask.redirect('/user?id=' + id)

@app.route('/user_unfriend', methods=['POST'])
@flask_login.login_required
def user_remove_friend():
	try:
		id=request.form.get('user_id')
	except:
		return flask.redirect(flask.url_for('hello'))
	removeFriend(getUserIdFromEmail(flask_login.current_user.id), id)
	return flask.redirect('/user?id=' + id)

@app.route('/friendrecommendations', methods=['GET'])
@flask_login.login_required
def friend_recommendations():
	users = recommendFriends(getUserIdFromEmail(flask_login.current_user.id))
	return render_template('friend_recommendations.html', users=users)

@app.route('/search/users', methods=['GET'])
def search_users():
	return render_template('search_users.html')

@app.route('/search/users', methods=['POST'])
def search_users_post():
	try:
		name=request.form.get('name')
	except:
		return flask.redirect(flask.url_for('search_users'))
	users = searchUsers(name)
	return render_template('search_users.html', name=name, users=users)

@app.route('/topusers', methods=['GET'])
def top_users():
	topUsers = getTopUsersByActivityScore()
	return render_template('top_users.html', topUsers=topUsers)

@app.route('/albums', methods=['GET'])
@flask_login.login_required
def albums():
	return render_template('albums.html', albums=getAlbumsForUser(getUserIdFromEmail(flask_login.current_user.id)))

@app.route('/albums', methods=['POST'])
@flask_login.login_required
def create_album():
	try:
		name=request.form.get('name')
	except:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('albums'))
	createAlbum(getUserIdFromEmail(flask_login.current_user.id), name)
	return flask.redirect(flask.url_for('albums'))

@app.route('/albums_delete', methods=['POST'])
@flask_login.login_required
def delete_album():
	try:
		albumId=request.form.get('album_id')
	except:
		return flask.redirect(flask.url_for('albums'))
	deleteAlbum(getUserIdFromEmail(flask_login.current_user.id), albumId)
	return flask.redirect(flask.url_for('albums'))

@app.route('/albums_rename', methods=['POST'])
@flask_login.login_required
def rename_album():
	try:
		albumId=request.form.get('album_id')
		name=request.form.get('name')
	except:
		return flask.redirect(flask.url_for('albums'))
	if len(name) < 1:
		return flask.redirect(flask.url_for('albums'))
	renameAlbum(getUserIdFromEmail(flask_login.current_user.id), albumId, name)
	return flask.redirect(flask.url_for('albums'))

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		album = request.form.get('album')
		if (checkAlbum(uid, album) == False):
			return flask.redirect(flask.url_for('upload_file'))
		photo_data = imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, album_id, caption) VALUES (%s, %s, %s, %s )''' ,(photo_data, uid, album, caption))
		conn.commit()
		return flask.redirect('/browse?user_id=' + str(uid) + '&album_id=' + album)
	else:
		return render_template('upload_picture.html', albums=getAlbumsForUser(uid))

@app.route('/browse', methods=['GET'])
def browse():
	uid = -1
	uname = ""
	if flask_login.current_user.is_authenticated:
		u = getUserFromEmail(flask_login.current_user.id)
		uid = u[0]
		uname = u[3] + ' ' + u[4]
	recommendations = ('recommendations' in request.args) and flask_login.current_user.is_authenticated
	photos = getPhotos(request.args) if not recommendations else recommendPhotos(getUserIdFromEmail(flask_login.current_user.id))
	tags = {}
	likes = {}
	comments = {}
	liked = []
	tag = None
	user = None
	album = None
	search = request.args['search'].strip().split(' ') if 'search' in request.args else None
	if 'tag_id' in request.args:
		tag = getTagById(request.args['tag_id'])
	elif 'tag' in request.args:
		tag = getTag(request.args['tag'])
	if 'user_id' in request.args:
		user = getUserFromId(request.args['user_id'])
	if 'album_id' in request.args:
		album = getAlbumById(request.args['album_id'])
	for photo in photos:
		tags[photo[0]] = getTagsForPhoto(photo[0])
		likes[photo[0]] = getLikesForPhoto(photo[0])
		comments[photo[0]] = getCommentsForPhoto(photo[0])
		if uid != -1:
			for like in likes[photo[0]]:
				if like[1] == uid:
					liked.append(photo[0])
					break

	return render_template('browse.html', photos=photos, tags=tags, likes=likes, comments=comments, liked=liked, tag=tag, user=user, album=album, search=search, base64=base64, uid=uid, uname=uname, recommendations=recommendations)

@app.route('/photo', methods=['GET'])
def photo():
	try:
		pictureId=request.args.get('id')
	except:
		return flask.redirect(flask.url_for('browse'))
	photos = getPhotos({'picture_id': pictureId})
	if len(photos) > 0:
		uid = -1
		albums = None
		if flask_login.current_user.is_authenticated:
			uid = getUserIdFromEmail(flask_login.current_user.id)
			albums=getAlbumsForUser(uid)
		tags = getTagsForPhoto(pictureId)
		return render_template('photo.html', photo=photos[0], tags=tags, albums=albums, base64=base64, uid=uid)
	else:
		return render_template('photo.html', message='Photo not found!')

@app.route('/photo_update', methods=['POST'])
@flask_login.login_required
def update_photo():
	try:
		pictureId=request.form.get('photo_id')
		caption=request.form.get('caption')
		albumId=request.form.get('album')
	except:
		return flask.redirect(flask.url_for('browse'))
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if (checkAlbum(uid, albumId) == False):
		return flask.redirect('/photo?id=' + str(pictureId))
	updatePhoto(uid, pictureId, caption, albumId)
	return flask.redirect('/photo?id=' + str(pictureId))

@app.route('/photo_delete', methods=['POST'])
@flask_login.login_required
def delete_photo():
	try:
		pictureId=request.form.get('photo_id')
	except:
		return flask.redirect(flask.url_for('browse'))
	deletePhoto(getUserIdFromEmail(flask_login.current_user.id), pictureId)
	return flask.redirect(flask.url_for('browse'))

@app.route('/photo_like', methods=['POST'])
@flask_login.login_required
def like_photo():
	try:
		pictureId=request.form.get('photo_id')
	except:
		return 'Error'
	likePhoto(getUserIdFromEmail(flask_login.current_user.id), pictureId)
	return 'OK'

@app.route('/photo_unlike', methods=['POST'])
@flask_login.login_required
def unlike_photo():
	try:
		pictureId=request.form.get('photo_id')
	except:
		return 'Error'
	unlikePhoto(getUserIdFromEmail(flask_login.current_user.id), pictureId)
	return 'OK'

@app.route('/photo_comment', methods=['POST'])
def comment_photo():
	try:
		pictureId=request.form.get('photo_id')
		comment=request.form.get('comment')
	except:
		return 'Error'
	uid = getUserIdFromEmail(flask_login.current_user.id) if flask_login.current_user.is_authenticated else -1
	commentPhoto(uid, pictureId, comment)
	return 'OK'

@app.route('/photo_delete_comment', methods=['POST'])
@flask_login.login_required
def delete_comment():
	try:
		commentId=request.form.get('comment_id')
	except:
		return 'Error'
	deleteComment(getUserIdFromEmail(flask_login.current_user.id), commentId)
	return 'OK'

@app.route('/photo_tag_add', methods=['POST'])
@flask_login.login_required
def add_tag():
	try:
		pictureId=request.form.get('photo_id')
		tag=request.form.get('tag')
	except:
		return flask.redirect(flask.url_for('browse'))
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if (checkPhoto(uid, pictureId) == False):
		return flask.redirect('/photo?id=' + str(pictureId))
	tagRow = getTag(tag)
	if tagRow:
		addTagToPhoto(tagRow[0], pictureId)
	else:
		addTagToPhoto(createTag(tag), pictureId)
	return flask.redirect('/photo?id=' + str(pictureId))

@app.route('/photo_tag_remove', methods=['POST'])
@flask_login.login_required
def remove_tag():
	try:
		pictureId=request.form.get('photo_id')
		tagId=request.form.get('tag_id')
	except:
		return flask.redirect(flask.url_for('browse'))
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if (checkPhoto(uid, pictureId) == False):
		return flask.redirect('/photo?id=' + str(pictureId))
	removeTagFromPhoto(tagId, pictureId)
	return flask.redirect('/photo?id=' + str(pictureId))

@app.route('/tags', methods=['GET'])
def tags():
	topTags = getTopTags()
	return render_template('tags.html', topTags=topTags)

@app.route('/search/comments', methods=['GET'])
def search_comments():
	return render_template('search_comments.html')

@app.route('/search/comments', methods=['POST'])
def search_comments_post():
	try:
		search=request.form.get('search')
	except:
		return flask.redirect(flask.url_for('search_comments'))
	comments = searchComments(search)
	return render_template('search_comments.html', search=search, comments=comments)


if __name__ == "__main__":
	app.run(port=5000, debug=True)
