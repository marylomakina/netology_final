import requests
import json

class VkPhoto:
    def __init__(self, raw_data):
        self.size = raw_data['sizes'][-1]['type']
        self.likes = raw_data['likes']['count']
        self.url = raw_data['sizes'][-1]['url']
        self.date = raw_data['date']

    def get_long_file_name(self):
        return f'{self.likes}_{self.date}.jpg'

    def get_short_file_name(self):
        return f'{self.likes}.jpg'

    def get_file_path(self, directory_name):
        return f'{directory_name}/{self.filename}'

    def get_info(self):
        return {'file_name': self.filename, 'size': self.size}


class VkPhotoManager:
    photos_url = 'https://api.vk.com/method/photos.get'

    def __init__(self, auth_token):
        self.auth_token = auth_token

    def load_photos(self, vk_id, count=5):
        params = self.build_load_photos_params(vk_id, count)
        print(f'VK: Loading {count} photos from user {vk_id}...')
        response = requests.get(self.photos_url, params=params)
        print(f'VK: Got response, status code = {response.status_code}')
        if response.status_code != 200:
            print(f"VK: Loading photos failed ({response.reason})")
            return []
        response_json = response.json()
        if 'error' in response_json:
            print(f"VK: Loading photos failed ({response_json['error']['error_msg']})")
            return []
        photos_raw = response_json['response']['items']
        print(f"VK: Loaded {len(photos_raw)} photos")
        return self.parse_photos(photos_raw)

    def build_load_photos_params(self, vk_id, count):
        return {
            'owner_id': vk_id,
            'access_token': self.auth_token,
            'v': '5.131',
            'album_id': 'profile',
            'extended': '1',
            'count': str(count)
        }

    def parse_photos(self, photos_info):
        photos = []
        for item in photos_info:
            photos.append(VkPhoto(item))
        self.name_files(photos)
        return photos

    def name_files(self, photos):
        likes = [photo.likes for photo in photos]
        counts = dict((like, likes.count(like)) for like in likes)
        for photo in photos:
            photo.filename = photo.get_long_file_name() if counts[photo.likes] > 1 else photo.get_short_file_name()
            photo.info = photo.get_info()


class YandexUploader:
    upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    folder_url = 'https://cloud-api.yandex.net/v1/disk/resources'

    def __init__(self, auth_token):
        self.auth_token = auth_token

    def create_folder(self, folder_name):
        header = self.get_headers()
        params = {
            'path': folder_name
        }
        print(f'YD: Creating folder {folder_name}...')
        response = requests.put(self.folder_url, headers=header, params=params)
        print(f'YD: Creating folder response: {response.status_code}')

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': f'OAuth {self.auth_token}'
        }

    def upload_photo(self, directory_name: str, photo_info: VkPhoto):
        print(f'YD: Loading {photo_info.filename}...')
        photo_response = requests.get(photo_info.url)
        print(f'YD: Loading file response: {photo_response.status_code}')
        header = self.get_headers()
        print(f'YD: Getting upload url for {photo_info.filename}...')
        upload_url_response = requests.get(self.upload_url, headers=header,
                                           params=self.build_upload_params(directory_name, photo_info))
        print(f'YD: Getting upload url response: {upload_url_response.status_code}')
        file_upload_url = upload_url_response.json()['href']
        print(f'YD: Uploading file {photo_info.filename}...')
        upload_response = requests.put(file_upload_url, data=photo_response.content)
        print(f'YD: Uploading file response: {upload_response.status_code}')


    def build_upload_params(self, directory_name: str, photo_info: VkPhoto):
        return {'path': photo_info.get_file_path(directory_name), 'overwrite': True}


def main():
    vk_id = input('Введите id пользователя VK: ')
    vk_token = input('vk token: ')
    ya_token = input('ya token: ')
    folder_name = 'Netologia'
    photos_count = 5

    vk_manager = VkPhotoManager(vk_token)
    photos = vk_manager.load_photos(vk_id, photos_count)

    if len(photos) < 1:
        print('No photos loaded, exiting')
        return

    yandex_uploader = YandexUploader(ya_token)
    yandex_uploader.create_folder(folder_name)
    for photo in photos:
        yandex_uploader.upload_photo(folder_name, photo)
    with open("result.json", "w") as file:
        json.dump([photo.info for photo in photos], file, indent=1)


if __name__ == '__main__':
    main()