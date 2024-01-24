# Django Paddle Billing

This package provides an integration between Django, a high-level Python Web framework, and Paddle Billing, a platform for selling digital products and services.

## Features

- Easy setup and configuration
- Seamless integration with Django projects
- Comprehensive handling of Paddle Billing features, including webhooks

## Installation

To install the package, use pip:

```bash
pip install django-paddle-billing
```

## Usage

After installing the package, add it to your `INSTALLED_APPS` in your Django settings:

```python
INSTALLED_APPS = [
    ...
    'django_paddle_billing',
    ...
]
```

Then, run migrations:

```bash
python manage.py migrate
```

You can now use the package in your Django project.

## Local webhook testing

In order to test webhooks locally, you can user cloudflared tunnel:
[Cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-local-tunnel/)

### Temporary URL

```bash
cloudflared tunnel --url http://localhost:8000/
```

### Permanent URL

Then, you can create a tunnel for your webhook:

```bash
cloudflared tunnel login
cloudflared tunnel create sandbox.paddle
# Create config file
# ...
cloudflared tunnel route dns sandbox.paddle sandbox-paddle.example.com
cloudflared tunnel run sandbox.paddle
```

Note: The deep level of DNS requires to be paid Advanced DNS (10$/month), so sandbox.paddle.example.com is not free

## Testing

This package uses pytest for testing. To run the tests, use the following command:

```bash
pytest
```

## Contributing

Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.