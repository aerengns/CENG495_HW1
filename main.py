from bson import ObjectId
from flask import render_template, request, redirect, url_for, flash
from flask import session
from flask_login import login_user, login_required, logout_user

import db
from app import app, bcrypt
from forms import LoginForm, SignUpForm, ReviewForm
from models import ITEM_TYPES, User, Item, Review


def get_current_user():
    return User.get_by_id(session['_user_id'])


@app.route("/get_flash", methods=['GET'])
def get_flash():
    return session.pop('flash_message', "")


### AUTH ###
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        form = LoginForm()
        return render_template('login.html', form=form)
    elif request.method == 'POST':
        form = LoginForm(**request.form)
        if form.validate():
            user = User.get_by_username(form.username.data)
            login_user(user, remember=form.remember.data, force=True)
            return redirect(url_for('home'))

        session['flash_message'] = 'Incorrect Username or Password!'
        return render_template('login.html', form=form)
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        form = SignUpForm()
        return render_template('signup.html', form=form)
    elif request.method == 'POST':
        form = SignUpForm(**request.form)
        if form.validate():
            document = form.data
            document['pwd'] = bcrypt.generate_password_hash(document['pwd'])
            document.pop('cpwd', None)
            user = User(**document)
            user.save()
            return redirect(url_for("home"))
        session['flash_message'] = 'User already exists!'
        return redirect(url_for('signup'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


### AUTH END ###

@app.route('/home')
def home():
    items = [ITEM_TYPES[item_doc['item_type']](**item_doc) for item_doc in db.items_collection.find({})]

    return render_template('index.html', items=items, review_form=ReviewForm())


@app.route('/items_ajax', methods=['GET', 'POST'])
def items_ajax():
    item_type = request.args.get('category_filter')
    fltr = {'item_type': item_type} if item_type else {}
    items = [ITEM_TYPES[item_doc['item_type']](**item_doc) for item_doc in db.items_collection.find(fltr)]
    return render_template('items_ajax.html', items=items, review_form=ReviewForm())


@app.route('/profile')
def profile():
    return render_template('profile.html', user=get_current_user())


@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'GET':
        # items = db.items_collection.find({'seller': ObjectId(session['_user_id'])})
        items = db.items_collection.find({})
        return render_template('add_page.html', items=items)

    elif request.method == 'POST':
        # Create a new item document based on the form data
        item_doc = {key: value for key, value in request.form.items()}
        item_type = item_doc.pop('item_type')
        item_doc['seller'] = ObjectId(session['_user_id'])

        item = ITEM_TYPES[item_type](**item_doc)
        item.save()
        # Redirect back to the home page
        return redirect(url_for('home'))


@app.route('/remove_item', methods=['POST'])
def remove_item():
    item_id = ObjectId(request.form.get('item_id'))
    db.reviews_collection.delete_many(filter={'item': item_id})
    db.items_collection.delete_one(filter={'_id': item_id})
    return redirect(url_for('home'))


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    users = []
    form = SignUpForm()
    for user_dic in db.users_collection.find({}):
        user_dic['id'] = user_dic.pop('_id')
        users.append(User(**user_dic))
    users.remove(get_current_user())
    return render_template('signup.html', users=users, form=form)


@app.route('/remove_user', methods=['POST'])
def remove_user():
    user_id = ObjectId(request.form.get('user_id'))
    db.items_collection.delete_many(filter={'seller': user_id})
    db.reviews_collection.delete_many(filter={'creator': user_id})
    db.users_collection.delete_one(filter={'_id': user_id})
    return redirect(url_for('add_user'))


@app.route('/add_review/<string:item_id>', methods=['POST'])
def add_review(item_id):
    form = ReviewForm(**request.form)
    review_doc = form.data
    # Check for previous review
    user_id = get_current_user().id
    review = db.reviews_collection.find_one({'creator': ObjectId(user_id), 'item': ObjectId(item_id)})
    if review:
        Review(**review).update(review_doc)
    else:
        review_doc['creator'] = user_id
        review_doc['item'] = ObjectId(item_id)
        review = Review(**review_doc)
        review.save()
    return redirect(url_for('home'))


@app.route('/remove_review', methods=['POST'])
def remove_review():
    review_id = ObjectId(request.form.get('review_id'))
    db.reviews_collection.delete_one(filter={'_id': review_id})
    return redirect(url_for('home'))
