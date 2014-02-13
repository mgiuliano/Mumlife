# mumlife/images.py
"""
Image manipulation module.

"""
import json
import logging
import os
from django.conf import settings
from django.utils.datastructures import MultiValueDictKeyError
from django.http import HttpResponse, HttpResponseBadRequest, Http404, HttpResponseNotAllowed
from PIL import Image

logger = logging.getLogger('mumlife.images')


class ImageException(Exception):
    pass

class ImageRotation(object):
    """
    Implements image rotation functionality.
    By default, the image is rotated clock-wise by 90 degrees.

    'image_path' should be the full path to the image on the server

    """
    def __init__(self, image_path=''):
        try:
            self.image = Image.open(image_path)
            self.path = image_path
        except IOError as e:
            raise ImageException(e)

    def apply(self, angle=-90):
        try:
            self.image = self.image.rotate(angle)
        except TypeError as e:
            raise ImageException(e)
        # Override image
        self.image.save(self.path, quality=100)


class ImageRotater(object):
    """
    Django View handler.
    Interface between ImageRotation and Django.

    At the moment, this class will only rotate the member's profile image.
    Though it has been written for possible future extension.

    """
    def __call__(self, request):
        if request.method == "GET":
            return HttpResponseNotAllowed("Method not allowed")
        try:
            field = request.POST['field']
        except MultiValueDictKeyError:
            return HttpResponseBadRequest("No image provided.")
        if field == 'picture':
            # Process member picture
            member = request.user.get_profile()
            if not member.picture:
                return HttpResponseBadRequest("No image provided.")
            image_path = os.path.join(settings.MEDIA_ROOT, member.picture.name)
            filename = member.picture.url
        else:
            return HttpResponseBadRequest("Not implemented.")
        # Rotate the image
        try:
            ImageRotation(image_path=image_path).apply()
        except ImageException as e:
            return HttpResponseBadRequest(str(e))
        # All went well if we get here
        return HttpResponse(json.dumps({
                                'filename': filename
                            }),
                            content_type='application/json; charset=utf-8')
    

if __name__ == "__main__":
    # Test image rotation with test image located at
    #   /static/img/3bc3d05.jpg
    # >> run from project root
    image_path = './static/img/3bc3d05.jpg'
    real_path = os.path.realpath(os.path.dirname('__FILE__'))
    path = os.path.realpath(os.path.join(real_path, image_path))
    try:
        ImageRotation(image_path=path).apply()
    except ImageException as e:
        print ' >> Error:', e
