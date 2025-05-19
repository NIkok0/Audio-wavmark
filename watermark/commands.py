from watermark import app, db
import click
from watermark.models import User

@app.cli.command()  # 注册为命令，可以传入 name 参数来自定义命令
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')

@app.cli.command()
@click.option('--username', prompt=True, help='The username of the admin')
@click.option('--email', prompt=True, help='The email of the admin')
@click.option('--password', prompt=True, hide_input=True, help='The password of the admin')
def create_admin(username, email, password):
    """Create an admin user."""
    from werkzeug.security import generate_password_hash
    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        is_admin=True
    )
    db.session.add(user)
    db.session.commit()
    click.echo(f'Created admin user: {username} ({email})')