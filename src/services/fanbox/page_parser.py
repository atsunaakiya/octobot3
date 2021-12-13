import json
from functools import partial
from itertools import count

class _PageParser:
    def __init__(self):
        self.counter = count()
        self.image_ext = None
        self.image_map = None
        self.image_id = []

    def _on_block(self, b):
        if b['type'] == 'p':
            return b['text']
        elif b['type'] == 'header':
            return f"### {b['text']}"
        elif b['type'] == 'image':
            image_id = b['imageId']
            idx = next(self.counter)
            ext = self.image_ext[image_id]
            self.image_id.append(image_id)
            return f'![{image_id}]({idx:06d}.{ext})'
        else:
            return json.dumps(b, ensure_ascii=False)

    def parse_blocks(self, blocks):
        return '\n\n'.join(map(self._on_block, blocks))

    def parse_image_mapping(self, image_map):
        self.image_map = {
            k: v['originalUrl']
            for k, v in image_map.items()
        }
        self.image_ext = {
            k: v['extension']
            for k, v in image_map.items()
        }

    def parse(self, body):
        self.parse_image_mapping(body['imageMap'])
        content = self.parse_blocks(body['blocks'])
        images = [
            self.image_map[img_id]
            for img_id in self.image_id
        ]
        return content, images


def parse_article_body(body):
    return _PageParser().parse(body)


def parse_image_body(body):
    text = body['text']
    images = [
        i['originalUrl']
        for i in body['images']
    ]
    return text, images
