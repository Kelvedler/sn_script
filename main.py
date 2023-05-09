import json
import random
import requests
import yaml
from cerberus import Validator
from faker import Faker
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

USERS_LIMIT = 100
POSTS_PER_USER_LIMIT = 100
LIKES_PER_USER_LIMIT = 100

BASE_API_URL = 'http://127.0.0.1:8000/'

POSTS_URL = BASE_API_URL + 'person/api/v1/posts/'
SIGN_UP_URL = BASE_API_URL + 'person/api/v1/sign-up'
LIKE_URL = BASE_API_URL + 'person/api/v1/posts/{}/like'

fake = Faker()


class ValidationError(Exception):
    pass


def read_config(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def validate_config(config_dict):
    config_schema = {
        'users_number': {'type': 'integer', 'required': True, 'min': 1, 'max': USERS_LIMIT},
        'user': {'type': 'dict',
                 'required': True,
                 'schema': {
                     'max_posts': {'type': 'integer', 'required': True, 'min': 0, 'max': POSTS_PER_USER_LIMIT},
                     'max_likes': {'type': 'integer', 'required': True, 'min': 0, 'max': LIKES_PER_USER_LIMIT}
                 }}
    }
    validator = Validator()
    validator.validate(config_dict, config_schema)
    if validator.errors:
        raise ValidationError(validator.errors)


def register_users():
    tokens = []
    for _ in range(random.randint(1, users_number)):
        name = fake.name()
        data = {
            'name': name,
            'password': 'Secure123@'
        }
        response = requests.post(SIGN_UP_URL, data=data)
        response_data = response.json()
        if response.status_code == 200:
            access_token = response_data['access_token']
            print(f'\tSuccess; name: {name}, access_token: {access_token}')
            tokens.append(access_token)
        else:
            print(f'\tFail; reason: {response_data}')
    return tokens


def create_posts(access_token):
    ids = []
    for _ in range(random.randint(0, user_max_posts)):
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        data = {'text': fake.sentence(nb_words=10, variable_nb_words=3)}
        response = requests.post(POSTS_URL, headers=headers, data=json.dumps(data))
        response_data = response.json()
        if response.status_code == 201:
            post_id = response_data['id']
            print(f'\tSuccess; Post ID: {post_id}')
            ids.append(post_id)
        else:
            print(f'\tFail; reason: {response_data}')
    return ids


def like_posts(access_token):
    posts_to_like = random.sample(post_ids, random.randint(0, max_possible_likes))
    for post_id in posts_to_like:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        response = requests.post(LIKE_URL.format(post_id), headers=headers)
        if response.status_code == 200:
            print(f'\tSuccess; Post ID: {post_id}')
        else:
            print(f'\tFail; reason: {response.json()}')


if __name__ == '__main__':
    config = read_config(BASE_DIR / 'config.yml')
    validate_config(config)
    users_number = config['users_number']
    user_max_posts = config['user']['max_posts']
    user_max_likes = config['user']['max_likes']

    print('Registering users:')
    user_tokens = register_users()

    print('Creating posts')
    post_ids = []
    for user_token in user_tokens:
        post_ids.extend(create_posts(user_token))

    print('Liking posts')
    max_possible_likes = min(len(post_ids), user_max_likes)
    for user_token in user_tokens:
        like_posts(user_token)
