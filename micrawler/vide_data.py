class Video:
    def __init__(self, id=None, title=None, video_url=None, thumbnail_url=None, description=None, tags=None,
                 status=None, save_path=None, download_path=None):
        self._download_path = download_path
        self._save_path = save_path
        self._id = id
        self._title = title
        self._video_url = video_url
        self._thumbnail_url = thumbnail_url
        self._description = description
        self._tags = tags
        self._status = status

    # Getter and Setter for id
    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    # Getter and Setter for title
    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    # Getter and Setter for video_url
    @property
    def video_url(self):
        return self._video_url

    @video_url.setter
    def video_url(self, value):
        self._video_url = value

    # Getter and Setter for thumbnail_url
    @property
    def thumbnail_url(self):
        return self._thumbnail_url

    @thumbnail_url.setter
    def thumbnail_url(self, value):
        self._thumbnail_url = value

    # Getter and Setter for description
    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

    # Getter and Setter for tags
    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, value):
        self._tags = value

    # Getter and Setter for status
    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def save_path(self):
        return self._save_path

    @save_path.setter
    def save_path(self, value):
        self._save_path = value

    @property
    def download_path(self):
        return self._download_path

    @download_path.setter
    def download_path(self, value):
        self._download_path = value
