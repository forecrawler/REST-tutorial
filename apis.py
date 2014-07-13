# -*- coding: utf-8 -*-

# import all modules
import datetime
from flask import Flask, jsonify, abort, \
        make_response, request, url_for, render_template
from flask.ext.httpauth import HTTPBasicAuth
from flask.ext.mongoengine import MongoEngine

#create app
app = Flask(__name__)

#create verification
auth = HTTPBasicAuth()

#mongodb config
app.config['MONGODB_DB'] = 'tasks'
app.config['MONGODB_HOST'] = 'localhost'
app.config['MONGODB_PORT'] = 27017
app.config['SECRET_KEY'] = '\xfb\xf7\x00T'

#create database connection object
db = MongoEngine(app)

#create models
class Task(db.Document):
    title = db.StringField(required=True, unique=True)
    description = db.StringField(required=True)
    done = db.BooleanField(default=False)

    def __unicode__(self):
        return self.title

@auth.get_password
def get_password(username):
    if username == 'admin':
        return 'admin'
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error':'Unauthorized access'}), 403)

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error':'Bad request'}), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error':'Not Found'}), 404)

"""
tasks = [
        {
            'id':1,
            'title':u'Buy groceries',
            'description':u'Milk, Cheese, Pizza, Fruit, Tylenol',
            'done':False},
        {
            'id':2,
            'title':u'Learn Python',
            'description':u'Need to find a good Python tutorial on the web.',
            'done':False
            }
        ]
"""

def get_all_tasks():
    tasks = []
    all_tasks = Task.objects.all()
    for i in range(len(all_tasks)):
        tasks.append({"id":str(all_tasks[i]['id']),'title':all_tasks[i]['title'],\
                'description':all_tasks[i]['description'],'done':all_tasks[i]['done']})
    return tasks

def make_public_task(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task', \
                    task_id = task['id'], _external = True)
        else:
            new_task[field] = task[field]
    return new_task

@app.route('/')
def index(**kwargs):
    return make_response(open('templates/index.html').read())

@app.route('/tasks', methods=['GET'])
@auth.login_required
def get_tasks():
    return jsonify({'tasks':map(make_public_task, get_all_tasks())})
    #return jsonify({'tasks':tasks})

@app.route('/tasks/<string:task_id>', methods=['GET'])
@auth.login_required
def get_task(task_id):
    task = filter(lambda t:t['id'] == task_id, get_all_tasks())
    if len(task) == 0:
        abort(404)
    return jsonify({'task':make_public_task(task[0])})

@app.route('/tasks', methods=['POST'])
@auth.login_required
def create_task():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = Task(
            title=request.json['title'],
            description=request.json.get('description',''),
            )
    task.save()
    return jsonify({'task': make_public_task(task)}), 201

@app.route('/tasks/<string:task_id>', methods=['PUT'])
@auth.login_required
def update_task(task_id):
    task = filter(lambda t: t['id'] == task_id, get_all_tasks())
    if len(task) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'title' in request.json and \
            type(request.json['title']) != unicode:
        abort(400)
    if 'description' in request.json and \
            type(request.json['description']) is not unicode:
        abort(400)
    if 'done' in request.json and \
            type(request.json['done']) is not bool:
        abort(400)
    #task[0]['title'] = request.json.get('title', task[0]['title'])
    #task[0]['description'] = \
    #        request.json.get('description', task[0]['description'])
    #task[0]['done'] = request.json.get('done', task[0]['done'])
    title = request.json.get('title', task[0]['title'])
    description = request.json.get('description', task[0]['description'])
    done = request.json.get('done',task[0]['done'])
    Task.objects(id=task_id).update(set__title=title,set__description=description,set__done=done)
    task = filter(lambda t: t['id'] == task_id, get_all_tasks())
    return jsonify({'task': make_public_task(task[0])})

@app.route('/tasks/<string:task_id>', methods=['DELETE'])
@auth.login_required
def delete_task(task_id):
    task = filter(lambda t:t['id'] == task_id, get_all_tasks())
    if len(task) == 0:
        abort(404)
    task = Task.objects(id=task[0]['id'])
    task.delete()
    return jsonify({'result': True})


if __name__ == '__main__':
    app.run(debug=True)
