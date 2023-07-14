from uuid import uuid4

from flask import request, jsonify, Blueprint

from tools import KBCollection

train_bp = Blueprint('train', __name__)


@train_bp.route('', methods=['POST'])
def train_user():
    uid = request.args.get('uid')
    rid = request.args.get('rid')
    print("### UID\n", uid)
    print("### RID\n", rid)

    data = request.json
    print("### Data\n", data)

    try:
        kb_id = str(uuid4())
        collection = KBCollection(uid=uid)
        collection.add(ids=[kb_id], documents=[data], metadatas=[{'user': uid}])
        KBCollection.persist()
    except Exception as e:
        print("ERROR user_train", e)
        return jsonify({'error': str(e)}), 500

    return jsonify({'response': 'ok'})
