from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, GuitarShop, GuitarItem, User

#Login functionality imports
from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
	open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Guitar Catalog App"

engine = create_engine('sqlite:///guitarselection.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) \
				for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html', STATE=state)
	
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo?alt=json"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output
    


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None
		
@app.route("/gdisconnect")
def gdisconnect():
	#only disconnect a connected user
	access_token = login_session.get('access_token')
	print 'In gdisconnect access token is %s', access_token
	if access_token is None:
		print 'Access token is None'
		response = make_response(json.dumps('Current user not connected.'), 401)
		response.headers['Content_Type'] = 'application/json'
		return response
	
	#Execute HTTP GET request to revoke the current token.
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' %login_session['access_token']
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]
	print 'result is '
	print result
	if result['status'] == '200':
		#reset the user's session.
		del login_session['access_token']
		del login_session['gplus_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		
		response = make_response(json.dumps('Successfully disconnected.'), 200)
		response.headers['Content_Type'] = 'application/json'
		return response
	else:
		response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
		response.headers['Content-Type'] = 'application/json'
		return response

@app.route('/guitarshops/<int:guitarshop_id>/guitars/JSON')
def guitarSelectionJSON(guitarshop_id):
    guitarshop = session.query(GuitarShop).filter_by(id=guitarshop_id).one()
    items = session.query(GuitarItem).filter_by(
        guitarshop_id=guitarshop_id).all()
    return jsonify(GuitarItems=[i.serialize for i in items])


# ADD JSON ENDPOINT HERE
@app.route('/guitarshops/<int:guitarshop_id>/guitarselection/<int:list_id>/JSON')
def listItemJSON(guitarshop_id, list_id):
    guitarItem = session.query(GuitarItem).filter_by(id=list_id).one()
    return jsonify(GuitarItem=guitarItem.serialize)


@app.route('/')
@app.route('/guitarcatalog/', methods = ['GET', 'POST'])
def guitarCatalog():
	guitarshops = session.query(GuitarShop).order_by(asc(GuitarShop.name))
	return render_template('guitarcatalog.html', guitarshops=guitarshops)

	
@app.route('/guitarcatalog/<int:id>/editshop',
           methods=['GET', 'POST'])
def editGuitarShop(id):
	editedShop = session.query(GuitarShop).filter_by(id=id).one()
	if 'username' not in login_session:
		return redirect('/login')
	if editedShop.user_id != login_session['user_id']:
		return "<script>function myFunction() {alert('You are not authorized to edit this store. Please create your own store in order to edit.');}</script><body onload='myFunction()''>"
	if request.method == 'POST':
		if request.form['name']:
			editedShop.name = request.form['name']
			flash('Shop %s Successfully Edited' % editedShop.name)
			return redirect(url_for('guitarCatalog'))
	else:
		return render_template('editguitarshop.html', shop=editedShop)


@app.route('/guitarshops/<int:user_id>/<int:guitarshop_id>/', methods = ['GET', 'POST'])
def guitarShopList(user_id, guitarshop_id):
    guitarshop = session.query(GuitarShop).filter_by(id=guitarshop_id).one()
    items = session.query(GuitarItem).filter_by(guitarshop_id=guitarshop_id)
    return render_template(
        'guitarshops.html', guitarshop=guitarshop, items=items, guitarshop_id=guitarshop_id, user_id=user_id)

@app.route('/guitarcatalog/newstore', methods=['GET', 'POST'])
def newStore():
	if 'username' not in login_session:
		return redirect('/login')
	if request.method == 'POST':
		newStore = GuitarShop(name=request.form['name'], user_id=login_session['user_id'])
		session.add(newStore)
		flash('New Shop Created')
		session.commit()
		return redirect(url_for('guitarCatalog'))
	else:
		return render_template('addnewshop.html')
		
@app.route('/guitarshops/<int:guitarshop_id>/new', methods=['GET', 'POST'])
def newListItem(guitarshop_id):
	if 'username' not in login_session:
		return redirect('/login')
	if request.method == 'POST':
		newItem = GuitarItem(name=request.form['name'], description=request.form[ \
			'description'], price=request.form['price'], guitarshop_id=guitarshop_id, user_id= \
			guitarshop.user_id)
		session.add(newItem)
		user_id=login_session['user_id']
		session.commit()
		return redirect(url_for('guitarShopList', guitarshop_id=guitarshop_id))
	else:
		return render_template('newlistitem.html', guitarshop_id=guitarshop_id)


@app.route('/guitarshops/<int:guitarshop_id>/<int:list_id>/edit',
           methods=['GET', 'POST'])
def editListItem(guitarshop_id, list_id):
	if 'username' not in login_session:
		return redirect('/login')
	editedItem = session.query(GuitarItem).filter_by(id=list_id).one()
	if request.method == 'POST':
		if request.form['name']:
			editedItem.name = request.form['name']
		if request.form['description']:
			editedItem.description = request.form['description']
		if request.form['price']:
			editedItem.price = request.form['price']
		user_id=login_session['user_id']
		session.add(editedItem)
		session.commit()
		flash('Guitar Successfully Edited')
		return redirect(url_for('guitarShopList', guitarshop_id=guitarshop_id))
	else:
		return render_template('editguitaritem.html', guitarshop_id=guitarshop_id, list_id=list_id, item=editedItem)


@app.route('/guitarshops/<int:guitarshop_id>/<int:list_id>/delete',
           methods=['GET', 'POST'])
def deleteListItem(guitarshop_id, list_id):
	if 'username' not in login_session:
		return redirect('/login')
	itemToDelete = session.query(GuitarItem).filter_by(id=list_id).one()
	if request.method == 'POST':
		session.delete(itemToDelete)
		user_id=login_session['user_id']
		session.commit()
		return redirect(url_for('guitarShopList', guitarshop_id=guitarshop_id))
	else:
		return render_template('deleteguitaritem.html', item=itemToDelete)



if __name__ == '__main__':
	app.secret_key = 'MKGtY6vH_LRF6iv8qmWXafj1'
	app.debug = True
	app.run(host='0.0.0.0', port=5000)
