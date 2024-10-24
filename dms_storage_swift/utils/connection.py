import swiftclient
from redis import Redis
from odoo.tools import config
from odoo.tools.config import config


def get_redis_connection():
    return Redis(
        port=config.get_misc("redis", "port", 6380),
        host=config.get_misc("redis", "host", "localhost"),
    )


class SessionSaveConnection(swiftclient.client.Connection):
    def _retry(self, reset_func, func, *args, **kwargs):
        res = super(SessionSaveConnection, self)._retry(
            reset_func, func, *args, **kwargs
        )
        redis = get_redis_connection()
        redis.mset(
            {
                "swift_token_preauthurl": self.url,
                "swift_token_preauthtoken": self.token,
            }
        )

        return res


def get_swift_connection():
    cnx_param = {
        "authurl": config.get("swift_auth_url"),
        "user": config.get("swift_user"),
        "key": config.get("swift_key"),
        "auth_version": "3",
        "os_options": {
            "tenant_id": config.get("swift_tenant_id"),
        },
    }
    if config.get("swift_region"):
        cnx_param["os_options"]["region_name"] = config.get("swift_region")

    redis = get_redis_connection()
    preauth = redis.mget(["swift_token_preauthurl", "swift_token_preauthtoken"])
    if all(preauth):
        cnx_param["preauthurl"] = preauth[0].decode()
        cnx_param["preauthtoken"] = preauth[1].decode()

    cnx = SessionSaveConnection(**cnx_param)

    return cnx
