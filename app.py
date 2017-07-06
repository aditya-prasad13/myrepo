from flask import Flask, g, request, Response
#from cluster import Cluster
from user import NewUser, Token
import flask_restful as restful
from flask_sqlalchemy import SQLAlchemy
from models import db
from influxgetdata import Influxgetdata
from chk_alert import alert_stat
from influxgetdatalast import Influxgetdatalast
from influxgetdatamem import Influxgetdatamem
from influxgetdataswp import Influxgetdataswp
from influxgetdataload import Influxgetdataload
from influxgetdatadisk import Influxgetdatadisk
from urlmonitoring import urlchk
from GetdbBackup import dbBackup_stat
from server_health import healthstats
from vip_data import vipdata
from vip_alert import vip_alert_stat
from ssodr_switch import sso_maxdrswitch
from mongossodr_switch import sso_mongodrswitch
from sso_db_dr import sso_full_dr
from drhealthCheck_sso import CheckDRhealth_sso


#from GetMonStats import GetMonStats

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:r00t@localhost/auth'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
#db = SQLAlchemy(app)
db.init_app(app)
with app.test_request_context():
    db.create_all()


apy = restful.Api(app)

apy.add_resource(NewUser, '/api/v0.1/newuser')
apy.add_resource(Token, '/api/v0.1/token')
#apy.add_resource(Cluster, '/api/v0.1/createStack')
apy.add_resource(Influxgetdata, '/api/v0.1/influxgetdata')
#apy.add_resource(GetMonStats, '/api/v0.1/GetMonStats')
apy.add_resource(alert_stat, '/api/v0.1/chk_alert')
apy.add_resource(Influxgetdatalast, '/api/v0.1/data')
apy.add_resource(Influxgetdatamem, '/api/v0.1/memdata')
apy.add_resource(Influxgetdataswp, '/api/v0.1/swpdata')
apy.add_resource(Influxgetdataload, '/api/v0.1/loaddata')
apy.add_resource(Influxgetdatadisk, '/api/v0.1/diskdata')
apy.add_resource(healthstats, '/health')
apy.add_resource(urlchk, '/api/v0.1/urlchk')
apy.add_resource(dbBackup_stat, '/api/v0.1/dbbackupdata')
apy.add_resource(vipdata, '/vipdata')
apy.add_resource(vip_alert_stat, '/api/v0.1/vip_alert')
apy.add_resource(sso_maxdrswitch, '/api/v0.1/sso_maxdrswitch')
apy.add_resource(sso_mongodrswitch, '/api/v0.1/sso_mongodrswitch')
apy.add_resource(sso_full_dr, '/api/v0.1/sso_full_dr')
apy.add_resource(CheckDRhealth_sso, '/api/v0.1/CheckDRhealth_sso')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)
