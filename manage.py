import os
#from flask_script import Manager
#from flask_migrate import Migrate, MigrateCommand
from flask.cli import FlaskGroup

from app import app, db


app.config.from_object(os.environ['APP_SETTINGS'])

#migrate = Migrate(app, db)
#manager = Manager(app)
cli = FlaskGroup(app)

#manager.add_command('db', MigrateCommand)

@cli.command('test')
@click.argument('test_case', default='test*.py')
def test(test_case='test*.py'):
    print("Handling command {}".format(test_case))

if __name__ == '__main__':
    cli()
