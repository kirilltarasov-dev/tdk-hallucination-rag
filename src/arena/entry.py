"""Local or organizer-configured entry links; does not publish the application."""
from io import BytesIO
from urllib.parse import urlsplit


def validate_url(url):
    if not isinstance(url,str):
        raise ValueError('Audience URL must be text')
    parsed=urlsplit(url)
    parsed.port  # Validate a supplied port as well as its hostname.
    if (len(url)>1000 or any(c.isspace() for c in url)
            or parsed.scheme not in ('http','https') or not parsed.hostname
            or parsed.username is not None or parsed.password is not None or parsed.fragment):
        raise ValueError('Audience URL must be HTTP(S), without credentials, whitespace or a fragment')
    return url


def qr_svg(url):
    import qrcode
    from qrcode.image.svg import SvgPathImage
    validate_url(url)
    output=BytesIO()
    qrcode.make(url,image_factory=SvgPathImage,box_size=8,border=4).save(output)
    return output.getvalue().decode()
