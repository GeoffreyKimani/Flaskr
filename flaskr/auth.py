import functools

from flask import Blueprint, request, render_template, flash, url_for, redirect, session, g
from werkzeug.security import generate_password_hash, check_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


# register a new user
@bp.route('/register', methods=['GET', 'POST'])
def register():
    title = 'SIGNUP'
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        # simple validation; check for required fields, check for duplicate entries
        if not username:
            error = 'Username is required!'
        elif not password:
            error = 'Password is required!'
        elif db.execute(
                'SELECT id FROM user WHERE username =? ', (username,)
        ).fetchone() is not None:
            error = 'User {} already exists'.format(username)

        if error is None:
            db.execute(
                'INSERT INTO user (username, password) VALUES (?,?)',
                (username, generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for('auth.login'))
        flash(error)

    return render_template('register.html', title=title)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    title = 'LOGIN'
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        user = db.execute(
            'SELECT * FROM user WHERE username =  ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        flash(error)

    return render_template('login.html', title=title)


'''bp.before_app_request() registers a function that runs before the view function, no matter what URL is requested.
 load_logged_in_user checks if a user id is stored in the session and gets that user’s data from the database, 
 storing it on g.user, which lasts for the length of the request. If there is no user id, or if the id doesn’t exist,
  g.user will be None.'''


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    title = 'INDEX'
    session.clear()
    return redirect(url_for('index'))


# Creating, editing, and deleting blog posts will require a user to be logged in.
# A decorator can be used to check this for each view it’s applied to.
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
