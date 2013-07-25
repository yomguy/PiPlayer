
import urlparse, urllib


def path2url(path):
    return urlparse.urljoin(
      'file:', urllib.pathname2url(path))

