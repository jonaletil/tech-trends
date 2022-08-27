import sqlite3
from flask import Flask, json, render_template, request, url_for, redirect, flash
import logging
import sys
import os

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
app.config['connection_count'] = 0


def get_db_connection():
    """
    This function connects to database with the name `database.db`
    """
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    app.config['connection_count'] = app.config['connection_count'] + 1
    return connection


def get_post(post_id):
    """
    Function to get a post using its ID
    Attributes:
        post_id: post ID
    """
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()
    return post


def get_post_count():
    """
    Returns posts count
    """
    connection = get_db_connection()
    posts = connection.execute("SELECT * FROM posts").fetchall()
    connection.close()
    post_count = len(posts)

    return post_count


# Define the main route of the web application
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.error('Article does not exist!')
        return render_template('404.html'), 404
    else:
        app.logger.info('Article \"%s\" retrieved!', post['title'])
        return render_template('post.html', post=post)


# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('About us page retrieved!')
    return render_template('about.html')


# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()

            app.logger.info('Article \"%s\" created!', title)
            return redirect(url_for('index'))

    return render_template('create.html')


# Define healthz endpoint
@app.route('/healthz')
def healthcheck():
    json_response = {
        'result': 'OK - healthy'
    }
    status_code = 200

    try:
        connection = get_db_connection()
        connection.execute('SELECT * FROM posts').fetchone()
        connection.close()
    except Exception as exc:
        json_response['result'] = 'ERROR - unhealthy'
        json_response['error'] = str(exc)
        status_code = 500

    response = app.response_class(
        response=json.dumps(json_response),
        status=status_code,
        mimetype='application/json')

    return response


# Define healthz endpoint
@app.route('/metrics')
def metrics():
    json_metrics = {
        'db_connection_count': app.config['connection_count'],
        'post_count': get_post_count()
    }

    response = app.response_class(
        response=json.dumps(json_metrics),
        status=200,
        mimetype='application/json')

    return response


# start the application on port 3111
if __name__ == "__main__":
    # Set logger and record the events to STDOUT & STDERR
    loglevel = os.getenv("LOGLEVEL", "DEBUG").upper()
    loglevel = (
        getattr(logging, loglevel)
        if loglevel in ["CRITICAL", "DEBUG", "ERROR", "INFO", "WARNING", ]
        else logging.DEBUG
    )
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)

    stderror_handler = logging.StreamHandler(stream=sys.stderr)
    stderror_handler.setLevel(logging.ERROR)

    handlers = [stdout_handler, stderror_handler]
    logging.basicConfig(format='%(levelname)s:%(name)s:%(asctime)s, %(message)s',
                        datefmt='%m/%d/%Y, %H:%M:%S',
                        level=loglevel,
                        handlers=handlers)
    app.run(host='0.0.0.0', port='3111')
