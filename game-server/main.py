from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_socketio import rooms as room_list
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thecakeisalie'
CORS(app, resources = {r'/*':{'origins':'*'}})
socketio = SocketIO(app, cors_allowed_origins='*')

users = dict()
rooms = {'lobby':dict()}

def send_user_list(room = 'lobby', sid = None):
    ''' 
        this function is used to send user lists for the specified room to the correct group
        
        :param room: the room list of users to share, and to target if no user is specified
        :param sid: what session id to send the room to, if specified
    '''
    if sid:
        emit('user list',{'users':list(rooms[room].items())}, to=sid)
    else:
        emit('user list',{'users':list(rooms[room].items())}, to=room)

def join_room_for_sid(sid, room = 'lobby'):
    ''' 
        this function is used to join one room and leave all others
        
        :param sid: the session id to move to a room
        :param room: if left empty, sends the user to the lobby
    '''
    for room_name, room_users in rooms.items():
        if room_name != room:
            user = room_users.pop(sid, None)
            if user:
                print(f'{user} leaving room {room_name}')
                leave_room(room_name, sid)
                send_user_list(room_name)
            
        else:
            print(f'joining room {room_name}')
            room_users[sid]=users[sid]
            join_room(room_name, sid)
            send_user_list(room_name)


@socketio.on('connect')
def connected():
    '''
        this function gets called by the socket on connection. 
        just a basic handshake.

        all socketio functions contain the request object from flask
    '''
    print('client has connected')
    emit('connect',{'data':f'id: {request.sid} is connected'})

@socketio.on('set name')
def set_name(data):
    '''
        this function assigns a username to a session id. 

        :param data: the desired username (currently not checking for collisions)

        all socketio functions contain the request object from flask
    '''
    users[request.sid] = data
    join_room_for_sid(request.sid)
    send_user_list()
    show_rooms(request.sid)

@socketio.on('create room')
def create_room(data):
    '''
        this function creates a room with the requested name, and adds the user to that room. 

        :param data: the desired room name

        all socketio functions contain the request object from flask
    '''
    print(data)
    if rooms.get(data):
        print(f'room {data} already exists')
        return
    rooms[data] = dict()
    join_room_for_sid(request.sid, data)
    send_user_list(data)
    show_rooms()

@socketio.on('join game')
def join_game(data):
    '''
        this function adds a user to a room. 

        :param data: the desired room to join

        all socketio functions contain the request object from flask
    '''
    join_room_for_sid(request.sid, data)
    show_rooms(request.sid)

@socketio.on('leave game')
def leave_game():
    '''
        this function returns the user to the lobby (currently not in use)

        all socketio functions contain the request object from flask
    '''
    join_room_for_sid(request.sid, 'lobby')

@socketio.on('show rooms')
def show_rooms(sid = None):
    '''
        this function shares the existing rooms with the interested user, 
        or broadcasts to all users if no user is specified 
        (currently not called by the socket client directly)

        :param sid: the session id to send the rooms list too

        all socketio functions contain the request object from flask
    '''
    if sid:
        emit('rooms',{'rooms':list(rooms.items())}, to=sid)
    else:
        emit('rooms',{'rooms':list(rooms.items())}, broadcast=True) # shouldnt really send the entire room directories

@socketio.on('disconnect')
def disconnected():
    '''
        this function gets triggered whenever a socketio client disconnects,
        so we perform cleanup on the user data

        all socketio functions contain the request object from flask
    '''
    joined_rooms = room_list(request.sid)
    for r in joined_rooms:
        _r = rooms.get(r,None)
        if _r:
            _r.pop(request.sid)
    user = users.pop(request.sid, None)
    if user:
        print(f'goodbye {user}')
        send_user_list()
    else:
        print(f'userId disconnected {request.sid}')
    emit('disconnect',f'user {request.sid} disconnected',broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True,port=5001)